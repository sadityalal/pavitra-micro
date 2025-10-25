from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import List, Optional
from backend import config, db, sanitize_input, get_logger
from .models import (
    PaymentCreate, PaymentResponse, PaymentInitiateResponse,
    PaymentVerifyRequest, RefundCreate, RefundResponse,
    PaymentMethodResponse, HealthResponse, PaymentStatus, PaymentAuthStatus
)
from datetime import datetime
import hashlib
import hmac
import json

router = APIRouter()
logger = get_logger(__name__)

@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM payment_transactions")
            payments_count = cursor.fetchone()['count']
            
            return HealthResponse(
                status="healthy",
                service="payment",
                payments_count=payments_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="payment",
            payments_count=0,
            timestamp=datetime.utcnow()
        )

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(payment_data: PaymentCreate, user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            # Verify order exists and belongs to user
            cursor.execute("""
                SELECT id, total_amount, payment_status, user_id 
                FROM orders 
                WHERE id = %s AND user_id = %s
            """, (payment_data.order_id, user_id))
            
            order = cursor.fetchone()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            if order['payment_status'] == 'paid':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order is already paid"
                )
            
            # Verify amount matches order total
            if abs(payment_data.amount - float(order['total_amount'])) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment amount does not match order total"
                )
            
            # Create payment transaction
            cursor.execute("""
                INSERT INTO payment_transactions (
                    order_id, user_id, amount, currency, payment_method,
                    gateway_name, status, payment_status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payment_data.order_id,
                user_id,
                payment_data.amount,
                payment_data.currency,
                payment_data.payment_method.value,
                payment_data.gateway.value,
                'pending',
                'pending'
            ))
            
            payment_id = cursor.lastrowid
            
            # Generate gateway-specific data
            gateway_order_id = f"PT_{payment_id}_{int(datetime.now().timestamp())}"
            
            # For Razorpay integration
            razorpay_order_id = None
            razorpay_key = None
            
            if payment_data.gateway.value == 'razorpay' and config.razorpay_key_id:
                razorpay_order_id = gateway_order_id
                razorpay_key = config.razorpay_key_id
                
                # Update payment with gateway order ID
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET gateway_order_id = %s 
                    WHERE id = %s
                """, (razorpay_order_id, payment_id))
            
            logger.info(f"Payment initiated: {payment_id} for order {payment_data.order_id}")
            
            return PaymentInitiateResponse(
                payment_id=payment_id,
                gateway_order_id=gateway_order_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_key=razorpay_key,
                amount=payment_data.amount,
                currency=payment_data.currency,
                callback_url=f"/api/v1/payments/verify/{payment_id}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate payment"
        )

@router.post("/verify/{payment_id}")
async def verify_payment(payment_id: int, verify_data: PaymentVerifyRequest, user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            # Get payment details
            cursor.execute("""
                SELECT pt.*, o.total_amount, o.user_id
                FROM payment_transactions pt
                JOIN orders o ON pt.order_id = o.id
                WHERE pt.id = %s
            """, (payment_id,))
            
            payment = cursor.fetchone()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            if payment['user_id'] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Verify payment with gateway (simulated for now)
            # In production, this would call the actual payment gateway API
            is_successful = True  # Simulate successful payment
            
            if is_successful:
                # Update payment status
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET status = 'completed',
                        payment_status = 'captured',
                        gateway_transaction_id = %s,
                        upi_id = %s,
                        authorized_at = NOW(),
                        captured_at = NOW()
                    WHERE id = %s
                """, (
                    verify_data.gateway_transaction_id,
                    verify_data.upi_id,
                    payment_id
                ))
                
                # Update order payment status
                cursor.execute("""
                    UPDATE orders 
                    SET payment_status = 'paid',
                        paid_at = NOW(),
                        status = 'confirmed'
                    WHERE id = %s
                """, (payment['order_id'],))
                
                # Add order history
                cursor.execute("""
                    INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type, reason)
                    VALUES (%s, 'payment_status', 'pending', 'paid', 'system', 'Payment completed successfully')
                """, (payment['order_id'],))
                
                logger.info(f"Payment verified successfully: {payment_id}")
                
                return {
                    "success": True,
                    "message": "Payment verified successfully",
                    "order_id": payment['order_id']
                }
            else:
                # Payment failed
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET status = 'failed',
                        payment_status = 'failed',
                        failed_at = NOW(),
                        failure_reason = 'Payment verification failed'
                    WHERE id = %s
                """, (payment_id,))
                
                logger.warning(f"Payment verification failed: {payment_id}")
                
                return {
                    "success": False,
                    "message": "Payment verification failed"
                }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify payment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        )

@router.get("/transactions", response_model=List[PaymentResponse])
async def get_payment_transactions(
    user_id: int = 1,
    page: int = 1,
    page_size: int = 20
):
    try:
        with db.get_cursor() as cursor:
            offset = (page - 1) * page_size
            
            cursor.execute("""
                SELECT * FROM payment_transactions 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, (user_id, page_size, offset))
            
            payments = cursor.fetchall()
            
            return [
                PaymentResponse(
                    id=payment['id'],
                    uuid=payment['uuid'],
                    order_id=payment['order_id'],
                    user_id=payment['user_id'],
                    amount=float(payment['amount']),
                    currency=payment['currency'],
                    payment_method=payment['payment_method'],
                    gateway_name=payment['gateway_name'],
                    gateway_transaction_id=payment['gateway_transaction_id'],
                    gateway_order_id=payment['gateway_order_id'],
                    status=payment['status'],
                    payment_status=payment['payment_status'],
                    failure_reason=payment['failure_reason'],
                    initiated_at=payment['initiated_at'],
                    authorized_at=payment['authorized_at'],
                    captured_at=payment['captured_at'],
                    failed_at=payment['failed_at'],
                    refunded_at=payment['refunded_at'],
                    refund_amount=float(payment['refund_amount']),
                    created_at=payment['created_at'],
                    updated_at=payment['updated_at']
                )
                for payment in payments
            ]
            
    except Exception as e:
        logger.error(f"Failed to fetch payment transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment transactions"
        )

@router.get("/transactions/{payment_id}", response_model=PaymentResponse)
async def get_payment_transaction(payment_id: int, user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM payment_transactions 
                WHERE id = %s AND user_id = %s
            """, (payment_id, user_id))
            
            payment = cursor.fetchone()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment transaction not found"
                )
            
            return PaymentResponse(
                id=payment['id'],
                uuid=payment['uuid'],
                order_id=payment['order_id'],
                user_id=payment['user_id'],
                amount=float(payment['amount']),
                currency=payment['currency'],
                payment_method=payment['payment_method'],
                gateway_name=payment['gateway_name'],
                gateway_transaction_id=payment['gateway_transaction_id'],
                gateway_order_id=payment['gateway_order_id'],
                status=payment['status'],
                payment_status=payment['payment_status'],
                failure_reason=payment['failure_reason'],
                initiated_at=payment['initiated_at'],
                authorized_at=payment['authorized_at'],
                captured_at=payment['captured_at'],
                failed_at=payment['failed_at'],
                refunded_at=payment['refunded_at'],
                refund_amount=float(payment['refund_amount']),
                created_at=payment['created_at'],
                updated_at=payment['updated_at']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch payment transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment transaction"
        )

@router.post("/refund", response_model=RefundResponse)
async def create_refund(refund_data: RefundCreate, user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            # Get payment details
            cursor.execute("""
                SELECT pt.*, o.user_id
                FROM payment_transactions pt
                JOIN orders o ON pt.order_id = o.id
                WHERE pt.id = %s
            """, (refund_data.payment_id,))
            
            payment = cursor.fetchone()
            if not payment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Payment not found"
                )
            
            # Check permissions (user can only refund their own payments or admin)
            if payment['user_id'] != user_id:
                # TODO: Check if user is admin
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Check if payment can be refunded
            if payment['status'] != 'completed':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only completed payments can be refunded"
                )
            
            # Check refund amount
            max_refund = float(payment['amount']) - float(payment['refund_amount'])
            if refund_data.amount > max_refund:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum refund amount is {max_refund}"
                )
            
            # Process refund (simulated)
            # In production, this would call the payment gateway's refund API
            refund_success = True
            gateway_refund_id = f"REF_{payment['id']}_{int(datetime.now().timestamp())}"
            
            if refund_success:
                # Update payment refund amount
                new_refund_amount = float(payment['refund_amount']) + refund_data.amount
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET refund_amount = %s,
                        refunded_at = CASE WHEN %s = amount THEN NOW() ELSE refunded_at END,
                        status = CASE WHEN %s = amount THEN 'refunded' ELSE status END
                    WHERE id = %s
                """, (new_refund_amount, new_refund_amount, new_refund_amount, refund_data.payment_id))
                
                # Update order status if full refund
                if new_refund_amount == float(payment['amount']):
                    cursor.execute("""
                        UPDATE orders 
                        SET payment_status = 'refunded',
                            status = 'refunded'
                        WHERE id = %s
                    """, (payment['order_id'],))
                
                # Create refund record
                cursor.execute("""
                    INSERT INTO refunds (payment_id, amount, reason, status, gateway_refund_id)
                    VALUES (%s, %s, %s, 'completed', %s)
                """, (refund_data.payment_id, refund_data.amount, refund_data.reason, gateway_refund_id))
                
                refund_id = cursor.lastrowid
                
                logger.info(f"Refund processed: {refund_id} for payment {refund_data.payment_id}")
                
                return RefundResponse(
                    id=refund_id,
                    payment_id=refund_data.payment_id,
                    amount=refund_data.amount,
                    reason=refund_data.reason,
                    status='completed',
                    gateway_refund_id=gateway_refund_id,
                    created_at=datetime.now()
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Refund processing failed"
                )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )

@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM payment_methods 
                WHERE user_id = %s AND is_active = 1
                ORDER BY is_default DESC, created_at DESC
            """, (user_id,))
            
            methods = cursor.fetchall()
            
            return [
                PaymentMethodResponse(
                    id=method['id'],
                    method_type=method['method_type'],
                    is_default=bool(method['is_default']),
                    upi_id=method['upi_id'],
                    upi_app=method['upi_app'],
                    card_last_four=method['card_last_four'],
                    card_type=method['card_type'],
                    card_network=method['card_network'],
                    bank_name=method['bank_name'],
                    created_at=method['created_at']
                )
                for method in methods
            ]
            
    except Exception as e:
        logger.error(f"Failed to fetch payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )

@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """
    Webhook endpoint for Razorpay payment notifications
    """
    try:
        body = await request.body()
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        # Verify webhook signature
        # In production, verify using Razorpay secret
        # secret = config.razorpay_secret
        # expected_signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        
        # if not hmac.compare_digest(expected_signature, signature):
        #     raise HTTPException(status_code=400, detail="Invalid signature")
        
        webhook_data = json.loads(body)
        event = webhook_data.get('event')
        
        logger.info(f"Razorpay webhook received: {event}")
        
        # Handle different webhook events
        if event == 'payment.captured':
            payment_data = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            
            with db.get_cursor() as cursor:
                # Update payment status
                cursor.execute("""
                    UPDATE payment_transactions 
                    SET status = 'completed',
                        payment_status = 'captured',
                        gateway_transaction_id = %s,
                        captured_at = NOW()
                    WHERE gateway_order_id = %s
                """, (payment_data.get('id'), payment_data.get('order_id')))
                
                # Get order ID from payment
                cursor.execute("""
                    SELECT order_id FROM payment_transactions 
                    WHERE gateway_order_id = %s
                """, (payment_data.get('order_id'),))
                
                payment = cursor.fetchone()
                if payment:
                    # Update order status
                    cursor.execute("""
                        UPDATE orders 
                        SET payment_status = 'paid',
                            paid_at = NOW(),
                            status = 'confirmed'
                        WHERE id = %s
                    """, (payment['order_id'],))
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
