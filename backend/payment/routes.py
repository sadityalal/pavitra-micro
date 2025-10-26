from fastapi import APIRouter, HTTPException, Depends, status, Request, BackgroundTasks, Header
from typing import List, Optional, Dict, Any
from shared import config, db, sanitize_input, get_logger, redis_client, rabbitmq_client
from shared.auth_middleware import get_current_user
from .models import (
    PaymentCreate, PaymentResponse, PaymentInitiateResponse,
    PaymentVerifyRequest, RefundCreate, RefundResponse,
    PaymentMethodResponse, HealthResponse, PaymentStatus, PaymentAuthStatus,
    SavePaymentMethodRequest, TokenizedPaymentRequest
)
from .secure_payment_handler import secure_payment_handler
from datetime import datetime
import hashlib
import hmac
import json
import secrets
import string

try:
    import razorpay
    import stripe
except ImportError as e:
    get_logger(__name__).warning(f"Payment gateway libraries not available: {e}")
    razorpay = None
    stripe = None

router = APIRouter()
logger = get_logger(__name__)

class SecurePaymentGatewayService:
    def __init__(self):
        self.razorpay_client = None
        self.stripe_client = None
        self._initialize_gateways()
    
    def _initialize_gateways(self):
        if config.razorpay_key_id and config.razorpay_secret:
            if not razorpay:
                logger.warning("Razorpay library not available")
            else:
                try:
                    self.razorpay_client = razorpay.Client(
                        auth=(config.razorpay_key_id, config.razorpay_secret)
                    )
                    if config.razorpay_test_mode:
                        logger.info("Razorpay client initialized in test mode")
                    else:
                        logger.info("Razorpay client initialized in live mode")
                except Exception as e:
                    logger.error(f"Failed to initialize Razorpay client: {e}")
        
        if config.stripe_secret_key:
            if not stripe:
                logger.warning("Stripe library not available")
            else:
                try:
                    stripe.api_key = config.stripe_secret_key
                    self.stripe_client = stripe
                    if config.stripe_test_mode:
                        logger.info("Stripe client initialized in test mode")
                    else:
                        logger.info("Stripe client initialized in live mode")
                except Exception as e:
                    logger.error(f"Failed to initialize Stripe client: {e}")
    
    def create_razorpay_order(self, amount: float, currency: str, receipt: str) -> Optional[Dict[str, Any]]:
        if not self.razorpay_client:
            logger.error("Razorpay client not available")
            return None
        
        try:
            order_data = {
                'amount': int(amount * 100),
                'currency': currency,
                'receipt': receipt,
                'payment_capture': 1
            }
            order = self.razorpay_client.order.create(data=order_data)
            logger.info(f"Razorpay order created: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"Failed to create Razorpay order: {e}")
            return None
    
    def create_stripe_payment_intent(self, amount: float, currency: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.stripe_client:
            logger.error("Stripe client not available")
            return None
        
        try:
            intent = self.stripe_client.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                metadata=metadata,
                automatic_payment_methods={
                    'enabled': True,
                }
            )
            logger.info(f"Stripe payment intent created: {intent.id}")
            return {
                'client_secret': intent.client_secret,
                'id': intent.id
            }
        except Exception as e:
            logger.error(f"Failed to create Stripe payment intent: {e}")
            return None
    
    def verify_razorpay_payment(self, payment_id: str, signature: str, order_id: str) -> bool:
        if not self.razorpay_client:
            logger.error("Razorpay client not available")
            return False
        
        try:
            if not all([payment_id, signature, order_id]):
                logger.error("Missing required parameters for Razorpay verification")
                return False
            
            params = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            self.razorpay_client.utility.verify_payment_signature(params)
            logger.info(f"Razorpay payment verified successfully: {payment_id}")
            return True
        except Exception as e:
            logger.error(f"Razorpay verification failed: {e}")
            return False
    
    def verify_stripe_payment(self, payment_intent_id: str) -> bool:
        if not self.stripe_client:
            logger.error("Stripe client not available")
            return False
        
        try:
            if not payment_intent_id:
                logger.error("Missing payment_intent_id for Stripe verification")
                return False
            
            payment_intent = self.stripe_client.PaymentIntent.retrieve(payment_intent_id)
            is_successful = payment_intent.status == 'succeeded'
            
            if is_successful:
                logger.info(f"Stripe payment verified successfully: {payment_intent_id}")
            else:
                logger.warning(f"Stripe payment not successful: {payment_intent.status}")
            
            return is_successful
        except Exception as e:
            logger.error(f"Stripe verification failed: {e}")
            return False
    
    def process_razorpay_refund(self, payment_id: str, amount: float) -> Optional[Dict[str, Any]]:
        if not self.razorpay_client:
            logger.error("Razorpay client not available")
            return None
        
        try:
            refund_data = {
                'amount': int(amount * 100)
            }
            refund = self.razorpay_client.payment.refund(payment_id, refund_data)
            logger.info(f"Razorpay refund processed: {refund.get('id')}")
            return refund
        except Exception as e:
            logger.error(f"Razorpay refund failed: {e}")
            return None
    
    def process_stripe_refund(self, payment_intent_id: str, amount: float) -> Optional[Dict[str, Any]]:
        if not self.stripe_client:
            logger.error("Stripe client not available")
            return None
        
        try:
            refund = self.stripe_client.Refund.create(
                payment_intent=payment_intent_id,
                amount=int(amount * 100)
            )
            logger.info(f"Stripe refund processed: {refund.id}")
            return refund
        except Exception as e:
            logger.error(f"Stripe refund failed: {e}")
            return None

payment_gateway_service = SecurePaymentGatewayService()

def generate_secure_transaction_id() -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

def publish_payment_event(payment_data: dict, event_type: str):
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

def cache_payment_data(key: str, data: Any, expire: int = 3600):
    try:
        redis_client.redis_client.setex(key, expire, json.dumps(data))
        logger.info(f"Cached payment data for key: {key}")
    except Exception as e:
        logger.error(f"Failed to cache payment data: {e}")

def get_cached_payment_data(key: str) -> Optional[Any]:
    try:
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached payment data: {e}")
        return None

def invalidate_payment_cache(user_id: int):
    try:
        keys_patterns = [
            f"payment_methods:{user_id}",
            f"payment_transactions:{user_id}:*",
            f"user_payments:{user_id}:*"
        ]
        
        for pattern in keys_patterns:
            keys = redis_client.redis_client.keys(pattern)
            if keys:
                redis_client.redis_client.delete(*keys)
        
        logger.info(f"Invalidated payment cache for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate payment cache: {e}")

@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM payment_transactions")
            payments_count = cursor.fetchone()['count']
            
            gateway_status = {
                'razorpay': payment_gateway_service.razorpay_client is not None,
                'stripe': payment_gateway_service.stripe_client is not None
            }
            
            return HealthResponse(
                status="healthy",
                service="payment",
                payments_count=payments_count,
                timestamp=datetime.utcnow(),
                gateway_status=gateway_status
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="payment",
            payments_count=0,
            timestamp=datetime.utcnow(),
            gateway_status={}
        )

@router.post("/tokenize-card")
async def tokenize_card(
    card_data: SavePaymentMethodRequest,
    request: Request
):
    """Tokenize card data securely - returns token for temporary use"""
    try:
        config.refresh_cache()
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        # Tokenize the card data (stores temporarily in memory)
        token = secure_payment_handler.tokenize_card_data(card_data.card_data.model_dump())
        
        logger.info(f"Card tokenized for user {user_id}, token: {token[:8]}...")
        
        return {
            "token": token,
            "message": "Card data tokenized securely",
            "expires_in": secure_payment_handler.token_expiry
        }
    
    except Exception as e:
        logger.error(f"Card tokenization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to tokenize card data"
        )

@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(request: Request):
    """Get user's saved payment methods"""
    try:
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        cached_methods = get_cached_payment_data(f"payment_methods:{user_id}")
        if cached_methods:
            logger.info(f"Returning cached payment methods for user {user_id}")
            return [PaymentMethodResponse(**method) for method in cached_methods]
        
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
                    expiry_month=method['expiry_month'],
                    expiry_year=method['expiry_year'],
                    card_holder_name=method['card_holder_name'],
                    created_at=method['created_at']
                )
                for method in methods
            ]
            
            cache_payment_data(f"payment_methods:{user_id}", [method.model_dump() for method in method_list])
            return method_list
    
    except Exception as e:
        logger.error(f"Failed to fetch payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )

@router.post("/save-payment-method")
async def save_payment_method(
    request_data: SavePaymentMethodRequest,
    request: Request
):
    """Save payment method securely using tokenized data"""
    try:
        config.refresh_cache()
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        # Get user details for gateway customer creation
        with db.get_cursor() as cursor:
            cursor.execute("SELECT first_name, last_name, email, phone FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        
        # Process with payment gateway to get a secure token
        gateway_token = None
        if payment_gateway_service.razorpay_client:
            # In real implementation, you'd use Razorpay's card tokenization
            # For now, we'll simulate a gateway token
            gateway_token = f"rzp_tok_{secrets.token_hex(16)}"
        
        # Detect card type and network
        card_number = request_data.card_data.number
        card_type = _detect_card_type(card_number)
        card_network = _detect_card_network(card_number)
        
        # Save to payment_methods table (only non-sensitive data)
        with db.get_cursor() as cursor:
            # If setting as default, unset other defaults
            if request_data.is_default:
                cursor.execute("""
                    UPDATE payment_methods 
                    SET is_default = 0 
                    WHERE user_id = %s AND method_type = 'card'
                """, (user_id,))
            
            cursor.execute("""
                INSERT INTO payment_methods (
                    user_id, method_type, is_default, card_last_four,
                    card_type, card_network, expiry_month, expiry_year,
                    card_holder_name, token
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                'card',
                request_data.is_default,
                card_number[-4:],  # Only last 4 digits
                card_type,
                card_network,
                request_data.card_data.expiry_month,
                request_data.card_data.expiry_year,
                request_data.card_data.name,
                gateway_token  # Gateway-provided token
            ))
            
            method_id = cursor.lastrowid
        
        invalidate_payment_cache(user_id)
        logger.info(f"Payment method saved securely for user {user_id}, method_id: {method_id}")
        
        return {
            "method_id": method_id,
            "message": "Payment method saved securely",
            "card_last_four": card_number[-4:]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save payment method: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save payment method"
        )

def _detect_card_type(card_number: str) -> str:
    """Detect card type based on number"""
    if card_number.startswith('4'):
        return 'visa'
    elif card_number.startswith(('51', '52', '53', '54', '55')):
        return 'mastercard'
    elif card_number.startswith(('34', '37')):
        return 'amex'
    elif card_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38')):
        return 'diners'
    elif card_number.startswith(('6011', '65')):
        return 'discover'
    else:
        return 'unknown'

def _detect_card_network(card_number: str) -> str:
    """Detect card network"""
    card_type = _detect_card_type(card_number)
    if card_type in ['visa', 'mastercard', 'amex']:
        return card_type.upper()
    return 'OTHER'

@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    payment_data: PaymentCreate,
    request: Request,
    background_tasks: BackgroundTasks = None
):
    """Initiate payment - supports both tokenized and direct card payments"""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Payment processing is temporarily unavailable."
            )
        
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, total_amount, payment_status, user_id, status
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
            
            if order['status'] in ['cancelled', 'refunded']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot process payment for cancelled or refunded order"
                )
            
            if abs(payment_data.amount - float(order['total_amount'])) > 0.01:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment amount does not match order total"
                )
            
            transaction_id = generate_secure_transaction_id()
            
            # Create payment transaction
            cursor.execute("""
                INSERT INTO payment_transactions (
                    order_id, user_id, amount, currency, payment_method,
                    gateway_name, status, payment_status, gateway_order_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payment_data.order_id,
                user_id,
                payment_data.amount,
                payment_data.currency,
                payment_data.payment_method.value,
                payment_data.gateway.value,
                'pending',
                'pending',
                transaction_id
            ))
            
            payment_id = cursor.lastrowid
            
            # Handle different payment methods
            gateway_response = None
            payment_page_url = None
            client_secret = None
            secure_token = None
            
            if payment_data.payment_method.value in ['credit_card', 'debit_card']:
                if payment_data.saved_payment_method_id:
                    # Use saved payment method
                    cursor.execute("""
                        SELECT token, card_last_four FROM payment_methods 
                        WHERE id = %s AND user_id = %s AND method_type = 'card' AND is_active = 1
                    """, (payment_data.saved_payment_method_id, user_id))
                    saved_method = cursor.fetchone()
                    
                    if not saved_method:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Saved payment method not found"
                        )
                    
                    # Use the gateway token for processing
                    logger.info(f"Using saved payment method: {saved_method['card_last_four']}")
                
                elif payment_data.card_data:
                    # Tokenize new card data
                    secure_token = secure_payment_handler.tokenize_card_data(
                        payment_data.card_data.model_dump()
                    )
                    logger.info(f"New card tokenized: {secure_token[:8]}...")
            
            # Create gateway order based on payment method
            if payment_data.gateway.value == 'razorpay':
                order_data = payment_gateway_service.create_razorpay_order(
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    receipt=f"order_{payment_data.order_id}"
                )
                
                if order_data:
                    gateway_response = order_data
                    cursor.execute("""
                        UPDATE payment_transactions
                        SET gateway_order_id = %s
                        WHERE id = %s
                    """, (order_data['id'], payment_id))
            
            elif payment_data.gateway.value == 'stripe':
                intent_data = payment_gateway_service.create_stripe_payment_intent(
                    amount=payment_data.amount,
                    currency=payment_data.currency,
                    metadata={
                        'order_id': payment_data.order_id,
                        'payment_id': payment_id,
                        'user_id': user_id
                    }
                )
                
                if intent_data:
                    gateway_response = intent_data
                    client_secret = intent_data['client_secret']
                    cursor.execute("""
                        UPDATE payment_transactions
                        SET gateway_order_id = %s
                        WHERE id = %s
                    """, (intent_data['id'], payment_id))
            
            elif payment_data.gateway.value == 'cash_on_delivery':
                cursor.execute("""
                    UPDATE payment_transactions
                    SET status = 'completed', payment_status = 'authorized'
                    WHERE id = %s
                """, (payment_id,))
                
                cursor.execute("""
                    UPDATE orders
                    SET payment_status = 'paid', status = 'confirmed'
                    WHERE id = %s
                """, (payment_data.order_id,))
            
            cursor.execute("SELECT * FROM payment_transactions WHERE id = %s", (payment_id,))
            payment = cursor.fetchone()
            
            if background_tasks:
                background_tasks.add_task(
                    publish_payment_event,
                    payment,
                    'initiated'
                )
            
            logger.info(f"Payment initiated: {payment_id} for order {payment_data.order_id}")
            
            return PaymentInitiateResponse(
                payment_id=payment_id,
                gateway_order_id=transaction_id,
                razorpay_order_id=gateway_response.get('id') if gateway_response else None,
                razorpay_key=config.razorpay_key_id if payment_data.gateway.value == 'razorpay' else None,
                stripe_client_secret=client_secret,
                amount=payment_data.amount,
                currency=payment_data.currency,
                callback_url=f"/api/v1/payments/verify/{payment_id}",
                payment_page_url=payment_page_url,
                token=secure_token
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
    request: Request,
    background_tasks: BackgroundTasks = None
):
    """Verify payment after gateway callback"""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Payment verification is temporarily unavailable."
            )
        
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT pt.*, o.total_amount, o.user_id, pt.gateway_name, pt.gateway_order_id
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
            
            if payment['status'] in ['completed', 'refunded']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Payment already processed"
                )
            
            is_successful = False
            gateway_transaction_id = verify_data.gateway_transaction_id
            
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
            
            elif payment['gateway_name'] == 'cash_on_delivery':
                is_successful = True
                gateway_transaction_id = f"COD_{payment_id}_{int(datetime.now().timestamp())}"
            
            else:
                is_successful = True
                gateway_transaction_id = gateway_transaction_id or f"MANUAL_{payment_id}_{int(datetime.now().timestamp())}"
            
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
                    gateway_transaction_id,
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
                
                invalidate_payment_cache(user_id)
                logger.info(f"Payment verified successfully: {payment_id}")
                
                return {
                    "success": True,
                    "message": "Payment verified successfully",
                    "order_id": payment['order_id'],
                    "payment_id": payment_id
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
    request: Request,
    page: int = 1,
    page_size: int = 20
):
    """Get user's payment transactions"""
    try:
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        cache_key = f"payment_transactions:{user_id}:{page}:{page_size}"
        cached_data = get_cached_payment_data(cache_key)
        
        if cached_data:
            logger.info(f"Returning cached payment transactions for user {user_id}")
            return [PaymentResponse(**item) for item in cached_data]
        
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
            
            cache_payment_data(cache_key, [item.model_dump() for item in payment_list], expire=300)
            return payment_list
    
    except Exception as e:
        logger.error(f"Failed to fetch payment transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment transactions"
        )

@router.get("/transactions/{payment_id}", response_model=PaymentResponse)
async def get_payment_transaction(
    payment_id: int,
    request: Request
):
    """Get specific payment transaction"""
    try:
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
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
async def create_refund(
    refund_data: RefundCreate,
    request: Request,
    background_tasks: BackgroundTasks = None
):
    """Create refund for a payment"""
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Refund processing is temporarily unavailable."
            )
        
        current_user = await get_current_user(request)
        user_id = current_user['sub']
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT pt.*, o.user_id, pt.gateway_name, pt.gateway_transaction_id, pt.amount, pt.refund_amount
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
            
            refund_success = False
            gateway_refund_id = None
            
            if payment['gateway_name'] == 'razorpay' and payment_gateway_service.razorpay_client:
                refund_result = payment_gateway_service.process_razorpay_refund(
                    payment['gateway_transaction_id'],
                    refund_data.amount
                )
                if refund_result:
                    refund_success = True
                    gateway_refund_id = refund_result['id']
            
            elif payment['gateway_name'] == 'stripe' and payment_gateway_service.stripe_client:
                refund_result = payment_gateway_service.process_stripe_refund(
                    payment['gateway_transaction_id'],
                    refund_data.amount
                )
                if refund_result:
                    refund_success = True
                    gateway_refund_id = refund_result.id
            
            else:
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
                    INSERT INTO refunds (payment_id, amount, reason, status, gateway_refund_id, processed_by)
                    VALUES (%s, %s, %s, 'completed', %s, %s)
                """, (refund_data.payment_id, refund_data.amount, refund_data.reason, gateway_refund_id, user_id))
                
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
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks = None,
    x_razorpay_signature: str = Header(None)
):
    """Razorpay webhook handler"""
    try:
        if not x_razorpay_signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature"
            )
        
        body = await request.body()
        
        if payment_gateway_service.razorpay_client:
            try:
                payment_gateway_service.razorpay_client.utility.verify_webhook_signature(
                    body.decode(), x_razorpay_signature, config.razorpay_secret
                )
            except Exception as e:
                logger.error(f"Webhook signature verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid webhook signature"
                )
        
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
                    SELECT order_id, user_id FROM payment_transactions
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
                    
                    cursor.execute("SELECT * FROM payment_transactions WHERE gateway_order_id = %s",
                                   (payment_data.get('order_id'),))
                    
                    updated_payment = cursor.fetchone()
                    if background_tasks and updated_payment:
                        background_tasks.add_task(
                            publish_payment_event,
                            updated_payment,
                            'completed'
                        )
        
        return {"status": "success"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

@router.get("/debug/maintenance")
async def debug_maintenance():
    """Debug endpoint to check maintenance mode"""
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode)),
        "maintenance_mode_raw": str(config.maintenance_mode)
    }

@router.get("/debug/settings")
async def debug_settings():
    """Debug endpoint to check payment settings"""
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "debug_mode": config.debug_mode,
        "app_debug": config.app_debug,
        "log_level": config.log_level,
        "cors_origins": config.cors_origins,
        "payment_gateways": {
            "razorpay_available": payment_gateway_service.razorpay_client is not None,
            "stripe_available": payment_gateway_service.stripe_client is not None,
            "razorpay_test_mode": config.razorpay_test_mode,
            "stripe_test_mode": config.stripe_test_mode
        }
    }
