from fastapi import APIRouter, HTTPException, Depends, status, Request, BackgroundTasks
from typing import List, Optional
from shared import config, db, sanitize_input, get_logger, redis_client, rabbitmq_client
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


class PaymentGatewayService:
    def __init__(self):
        self.razorpay_client = None
        self.stripe_client = None

        if config.razorpay_key_id and config.razorpay_secret:
            self.razorpay_client = razorpay.Client(
                auth=(config.razorpay_key_id, config.razorpay_secret)
            )

        if config.stripe_secret_key:
            stripe.api_key = config.stripe_secret_key
            self.stripe_client = stripe

    def verify_razorpay_payment(self, payment_id: str, signature: str, order_id: str) -> bool:
        """Verify Razorpay payment signature"""
        if not self.razorpay_client:
            return False

        try:
            params = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.razorpay_client.utility.verify_payment_signature(params)
            return True
        except Exception as e:
            logger.error(f"Razorpay verification failed: {e}")
            return False

    def verify_stripe_payment(self, payment_intent_id: str) -> bool:
        """Verify Stripe payment"""
        if not self.stripe_client:
            return False

        try:
            payment_intent = self.stripe_client.PaymentIntent.retrieve(payment_intent_id)
            return payment_intent.status == 'succeeded'
        except Exception as e:
            logger.error(f"Stripe verification failed: {e}")
            return False


payment_gateway_service = PaymentGatewayService()

def publish_payment_event(payment_data: dict, event_type: str):
    """Publish payment event to RabbitMQ"""
    try:
        message = {
            'event_type': event_type,
            'payment_id': payment_data['id'],
            'order_id': payment_data['order_id'],
            'user_id': payment_data['user_id'],
            'amount': float(payment_data['amount']),
            'status': payment_data['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'data': payment_data
        }
        
        rabbitmq_client.publish_message(
            exchange='payment_events',
            routing_key=f'payment.{event_type}',
            message=message
        )
        logger.info(f"Payment {event_type} event published for payment {payment_data['id']}")
    except Exception as e:
        logger.error(f"Failed to publish payment event: {e}")

def cache_payment_methods(user_id: int, methods: List[dict], expire: int = 3600):
    """Cache user payment methods in Redis"""
    try:
        key = f"payment_methods:{user_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(methods))
        logger.info(f"Cached payment methods for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache payment methods: {e}")

def get_cached_payment_methods(user_id: int) -> Optional[List[dict]]:
    """Get cached payment methods from Redis"""
    try:
        key = f"payment_methods:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached payment methods: {e}")
        return None

def invalidate_payment_cache(user_id: int):
    """Invalidate payment-related cache for user"""
    try:
        keys = [
            f"payment_methods:{user_id}",
            f"payment_transactions:{user_id}"
        ]
        for key in keys:
            redis_client.redis_client.delete(key)
        logger.info(f"Invalidated payment cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate payment cache: {e}")

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
async def initiate_payment(payment_data: PaymentCreate, user_id: int = 1, background_tasks: BackgroundTasks = None):
    try:
        with db.get_cursor() as cursor:
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
            if abs(payment_data.amount - float(order['total_amount'])) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment amount does not match order total"
                )
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
            gateway_order_id = f"PT_{payment_id}_{int(datetime.now().timestamp())}"
            razorpay_order_id = None
            razorpay_key = None
            if payment_data.gateway.value == 'razorpay' and config.razorpay_key_id:
                razorpay_order_id = gateway_order_id
                razorpay_key = config.razorpay_key_id
                cursor.execute("""
                    UPDATE payment_transactions
                    SET gateway_order_id = %s
                    WHERE id = %s
                """, (razorpay_order_id, payment_id))
            
            # Get created payment
            cursor.execute("SELECT * FROM payment_transactions WHERE id = %s", (payment_id,))
            payment = cursor.fetchone()
            
            # Publish payment initiated event
            if background_tasks:
                background_tasks.add_task(
                    publish_payment_event,
                    payment,
                    'initiated'
                )
            
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
async def verify_payment(
        payment_id: int,
        verify_data: PaymentVerifyRequest,
        user_id: int = 1,
        background_tasks: BackgroundTasks = None
):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT pt.*, o.total_amount, o.user_id, pt.gateway_name
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

            # Actual payment verification based on gateway
            is_successful = False
            if payment['gateway_name'] == 'razorpay':
                is_successful = payment_gateway_service.verify_razorpay_payment(
                    verify_data.gateway_transaction_id,
                    verify_data.gateway_signature,
                    payment['gateway_order_id']
                )
            elif payment['gateway_name'] == 'stripe':
                is_successful = payment_gateway_service.verify_stripe_payment(
                    verify_data.gateway_transaction_id
                )
            else:
                # For cash on delivery or other methods
                is_successful = True

            if is_successful:
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

                cursor.execute("""
                    UPDATE orders
                    SET payment_status = 'paid',
                        paid_at = NOW(),
                        status = 'confirmed'
                    WHERE id = %s
                """, (payment['order_id'],))

                cursor.execute("""
                    INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type, reason)
                    VALUES (%s, 'payment_status', 'pending', 'paid', 'system', 'Payment completed successfully')
                """, (payment['order_id'],))

                cursor.execute("SELECT * FROM payment_transactions WHERE id = %s", (payment_id,))
                updated_payment = cursor.fetchone()

                if background_tasks:
                    background_tasks.add_task(
                        publish_payment_event,
                        updated_payment,
                        'completed'
                    )

                redis_client.invalidate_product_cache(f"order:{payment['order_id']}")
                logger.info(f"Payment verified successfully: {payment_id}")

                return {
                    "success": True,
                    "message": "Payment verified successfully",
                    "order_id": payment['order_id']
                }
            else:
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
        # Try to get from cache first
        cache_key = f"payment_transactions:{user_id}:{page}:{page_size}"
        cached_data = get_cached_payment_methods(cache_key)
        if cached_data:
            logger.info(f"Returning cached payment transactions for user {user_id}")
            return cached_data
        
        with db.get_cursor() as cursor:
            offset = (page - 1) * page_size
            cursor.execute("""
                SELECT * FROM payment_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, page_size, offset))
            payments = cursor.fetchall()
            payment_list = [
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
            
            # Cache the results
            cache_payment_methods(cache_key, payment_list, expire=300)  # 5 minutes
            
            return payment_list
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

@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(user_id: int = 1):
    try:
        # Try to get from cache first
        cached_methods = get_cached_payment_methods(user_id)
        if cached_methods:
            logger.info(f"Returning cached payment methods for user {user_id}")
            return cached_methods
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM payment_methods
                WHERE user_id = %s AND is_active = 1
                ORDER BY is_default DESC, created_at DESC
            """, (user_id,))
            methods = cursor.fetchall()
            method_list = [
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
            
            # Cache the results
            cache_payment_methods(user_id, method_list)
            
            return method_list
    except Exception as e:
        logger.error(f"Failed to fetch payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
        refund_data: RefundCreate,
        user_id: int = 1,
        background_tasks: BackgroundTasks = None
):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT pt.*, o.user_id, pt.gateway_name, pt.gateway_transaction_id
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

            if payment['user_id'] != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

            if payment['status'] != 'completed':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only completed payments can be refunded"
                )

            max_refund = float(payment['amount']) - float(payment['refund_amount'])
            if refund_data.amount > max_refund:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Maximum refund amount is {max_refund}"
                )

            # Process refund through payment gateway
            refund_success = False
            gateway_refund_id = None

            if payment['gateway_name'] == 'razorpay' and payment_gateway_service.razorpay_client:
                try:
                    refund = payment_gateway_service.razorpay_client.payment.refund(
                        payment['gateway_transaction_id'],
                        {'amount': int(refund_data.amount * 100)}  # Convert to paise
                    )
                    refund_success = True
                    gateway_refund_id = refund['id']
                except Exception as e:
                    logger.error(f"Razorpay refund failed: {e}")
                    refund_success = False

            elif payment['gateway_name'] == 'stripe' and payment_gateway_service.stripe_client:
                try:
                    refund = payment_gateway_service.stripe_client.Refund.create(
                        payment_intent=payment['gateway_transaction_id'],
                        amount=int(refund_data.amount * 100)  # Convert to cents
                    )
                    refund_success = True
                    gateway_refund_id = refund.id
                except Exception as e:
                    logger.error(f"Stripe refund failed: {e}")
                    refund_success = False
            else:
                # For cash on delivery or manual processing
                refund_success = True
                gateway_refund_id = f"MANUAL_REF_{payment['id']}_{int(datetime.now().timestamp())}"

            if refund_success:
                new_refund_amount = float(payment['refund_amount']) + refund_data.amount
                cursor.execute("""
                    UPDATE payment_transactions
                    SET refund_amount = %s,
                        refunded_at = CASE WHEN %s = amount THEN NOW() ELSE refunded_at END,
                        status = CASE WHEN %s = amount THEN 'refunded' ELSE status END
                    WHERE id = %s
                """, (new_refund_amount, new_refund_amount, new_refund_amount, refund_data.payment_id))

                if new_refund_amount == float(payment['amount']):
                    cursor.execute("""
                        UPDATE orders
                        SET payment_status = 'refunded',
                            status = 'refunded'
                        WHERE id = %s
                    """, (payment['order_id'],))

                cursor.execute("""
                    INSERT INTO refunds (payment_id, amount, reason, status, gateway_refund_id)
                    VALUES (%s, %s, %s, 'completed', %s)
                """, (refund_data.payment_id, refund_data.amount, refund_data.reason, gateway_refund_id))

                refund_id = cursor.lastrowid
                cursor.execute("SELECT * FROM payment_transactions WHERE id = %s", (refund_data.payment_id,))
                updated_payment = cursor.fetchone()

                if background_tasks:
                    background_tasks.add_task(
                        publish_payment_event,
                        updated_payment,
                        'refunded'
                    )

                invalidate_payment_cache(user_id)
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
                    detail="Refund processing failed at payment gateway"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process refund: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )

@router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request, background_tasks: BackgroundTasks = None):
    try:
        body = await request.body()
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        # Verify webhook signature (implement proper verification)
        webhook_data = json.loads(body)
        event = webhook_data.get('event')
        logger.info(f"Razorpay webhook received: {event}")
        
        if event == 'payment.captured':
            payment_data = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
            with db.get_cursor() as cursor:
                cursor.execute("""
                    UPDATE payment_transactions
                    SET status = 'completed',
                        payment_status = 'captured',
                        gateway_transaction_id = %s,
                        captured_at = NOW()
                    WHERE gateway_order_id = %s
                """, (payment_data.get('id'), payment_data.get('order_id')))
                
                cursor.execute("""
                    SELECT order_id FROM payment_transactions
                    WHERE gateway_order_id = %s
                """, (payment_data.get('order_id'),))
                payment = cursor.fetchone()
                if payment:
                    cursor.execute("""
                        UPDATE orders
                        SET payment_status = 'paid',
                            paid_at = NOW(),
                            status = 'confirmed'
                        WHERE id = %s
                    """, (payment['order_id'],))
                    
                    # Get updated payment
                    cursor.execute("SELECT * FROM payment_transactions WHERE gateway_order_id = %s", (payment_data.get('order_id'),))
                    updated_payment = cursor.fetchone()
                    
                    # Publish payment completed event
                    if background_tasks and updated_payment:
                        background_tasks.add_task(
                            publish_payment_event,
                            updated_payment,
                            'completed'
                        )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )
