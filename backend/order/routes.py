from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Query
from typing import List, Optional
from decimal import Decimal
import json
from datetime import datetime

from shared import config, db, sanitize_input, get_logger, rabbitmq_client, redis_client
from shared.auth_middleware import get_current_user
from .models import (
    OrderCreate, OrderResponse, OrderWithItemsResponse,
    OrderListResponse, HealthResponse, OrderStatus, PaymentStatus,
    OrderStatusUpdate, OrderCancelRequest
)

router = APIRouter()
logger = get_logger(__name__)


def require_roles(required_roles: List[str]):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get('roles', [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        return current_user

    return role_dependency


def cache_order(order_id: int, order_data: dict, expire: int = 1800):
    try:
        key = f"order:{order_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(order_data))
        logger.info(f"Cached order {order_id}")
    except Exception as e:
        logger.error(f"Failed to cache order: {e}")


def get_cached_order(order_id: int) -> Optional[dict]:
    try:
        key = f"order:{order_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached order: {e}")
        return None


def cache_user_orders(user_id: int, orders_data: dict, expire: int = 900):
    try:
        key = f"user_orders:{user_id}"
        redis_client.redis_client.setex(key, expire, json.dumps(orders_data))
        logger.info(f"Cached orders for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to cache user orders: {e}")


def get_cached_user_orders(user_id: int) -> Optional[dict]:
    try:
        key = f"user_orders:{user_id}"
        data = redis_client.redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.error(f"Failed to get cached user orders: {e}")
        return None


def invalidate_order_cache(order_id: int, user_id: int = None):
    try:
        keys = [f"order:{order_id}"]
        if user_id:
            keys.append(f"user_orders:{user_id}")

        for key in keys:
            redis_client.redis_client.delete(key)
        logger.info(f"Invalidated cache for order {order_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate order cache: {e}")


def publish_order_event(order_data: dict, event_type: str):
    try:
        message = {
            'event_type': event_type,
            'order_id': order_data['id'],
            'order_number': order_data['order_number'],
            'user_id': order_data['user_id'],
            'total_amount': float(order_data['total_amount']),
            'status': order_data['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'data': order_data
        }
        rabbitmq_client.publish_message(
            exchange='order_events',
            routing_key=f'order.{event_type}',
            message=message
        )
        logger.info(f"Order {event_type} event published for order {order_data['order_number']}")
    except Exception as e:
        logger.error(f"Failed to publish order event: {e}")


def validate_address(address: dict) -> bool:
    required_fields = ['full_name', 'phone', 'address_line1', 'city', 'state', 'postal_code']
    return all(field in address and address[field] for field in required_fields)


@router.get("/health", response_model=HealthResponse)
async def health():
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            orders_count = cursor.fetchone()['count']
            return HealthResponse(
                status="healthy",
                service="order",
                orders_count=orders_count,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="order",
            orders_count=0,
            timestamp=datetime.utcnow()
        )


@router.post("/", response_model=OrderWithItemsResponse)
async def create_order(
        order_data: OrderCreate,
        background_tasks: BackgroundTasks = None,
        current_user: dict = Depends(get_current_user)
):
    try:
        config.refresh_cache()
        if config.maintenance_mode:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is under maintenance. Order creation is temporarily unavailable."
            )

        user_id = int(current_user['sub'])

        if not validate_address(order_data.shipping_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid shipping address. Required fields: full_name, phone, address_line1, city, state, postal_code"
            )

        if order_data.billing_address and not validate_address(order_data.billing_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid billing address. Required fields: full_name, phone, address_line1, city, state, postal_code"
            )

        with db.get_cursor() as cursor:
            connection = db.get_connection()
            connection.start_transaction()

            try:
                subtotal = Decimal('0')
                items_data = []

                for item in order_data.items:
                    cursor.execute("""
                        SELECT name, sku, main_image_url, base_price, gst_rate,
                               stock_quantity, stock_status, low_stock_threshold
                        FROM products
                        WHERE id = %s AND status = 'active'
                    """, (item.product_id,))
                    product = cursor.fetchone()

                    if not product:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Product {item.product_id} not found or inactive"
                        )

                    if product['stock_status'] == 'out_of_stock':
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Product {product['name']} is out of stock"
                        )

                    if item.quantity > product['stock_quantity'] and product['stock_status'] != 'on_backorder':
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Not enough stock for {product['name']}. Available: {product['stock_quantity']}"
                        )

                    unit_price = Decimal(str(product['base_price']))
                    item_total = unit_price * item.quantity
                    subtotal += item_total

                    variation_attributes = None
                    if item.variation_id:
                        cursor.execute("""
                            SELECT pav.value, pa.name as attribute_name
                            FROM variation_attributes va
                            JOIN product_attribute_values pav ON va.attribute_value_id = pav.id
                            JOIN product_attributes pa ON pav.attribute_id = pa.id
                            WHERE va.variation_id = %s
                        """, (item.variation_id,))
                        attributes = cursor.fetchall()
                        if attributes:
                            variation_attributes = {attr['attribute_name']: attr['value'] for attr in attributes}

                    items_data.append({
                        'product_id': item.product_id,
                        'variation_id': item.variation_id,
                        'product_name': product['name'],
                        'product_sku': product['sku'],
                        'product_image': product['main_image_url'],
                        'unit_price': float(unit_price),
                        'quantity': item.quantity,
                        'total_price': float(item_total),
                        'gst_rate': float(product['gst_rate']),
                        'gst_amount': float(item_total * Decimal(str(product['gst_rate'])) / 100),
                        'variation_attributes': variation_attributes
                    })

                shipping_amount = Decimal('0.0')
                if subtotal < Decimal(str(config.free_shipping_min_amount)):
                    shipping_amount = Decimal('50.0')

                tax_amount = sum(Decimal(str(item['gst_amount'])) for item in items_data)
                discount_amount = Decimal('0.0')
                total_amount = subtotal + shipping_amount + tax_amount - discount_amount

                if subtotal < Decimal(str(config.min_order_amount)):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Minimum order amount is {config.currency_symbol}{config.min_order_amount}"
                    )

                cursor.execute("SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = CURDATE()")
                daily_count = cursor.fetchone()['count'] + 1
                order_number = f"PT{datetime.now().strftime('%Y%m%d')}{daily_count:04d}"

                cursor.execute("""
                    INSERT INTO orders (
                        order_number, user_id, subtotal, shipping_amount, tax_amount,
                        discount_amount, total_amount, payment_method, shipping_address,
                        billing_address, customer_note, is_gst_invoice, gst_number,
                        status, payment_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_number, user_id, float(subtotal), float(shipping_amount), float(tax_amount),
                    float(discount_amount), float(total_amount), order_data.payment_method.value,
                    json.dumps(order_data.shipping_address),
                    json.dumps(order_data.billing_address) if order_data.billing_address else json.dumps(
                        order_data.shipping_address),
                    sanitize_input(order_data.customer_note) if order_data.customer_note else None,
                    order_data.use_gst_invoice,
                    sanitize_input(order_data.gst_number) if order_data.gst_number else None,
                    'pending',
                    'pending'
                ))

                order_id = cursor.lastrowid

                for item in items_data:
                    cursor.execute("""
                        INSERT INTO order_items (
                            order_id, product_id, variation_id, product_name, product_sku,
                            product_image, unit_price, quantity, total_price, gst_rate, gst_amount,
                            variation_attributes
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        order_id, item['product_id'], item['variation_id'],
                        item['product_name'], item['product_sku'], item['product_image'],
                        item['unit_price'], item['quantity'], item['total_price'],
                        item['gst_rate'], item['gst_amount'],
                        json.dumps(item['variation_attributes']) if item['variation_attributes'] else None
                    ))

                    cursor.execute("""
                        UPDATE products
                        SET stock_quantity = stock_quantity - %s,
                            total_sold = total_sold + %s,
                            stock_status = CASE
                                WHEN stock_quantity - %s <= 0 THEN 'out_of_stock'
                                WHEN stock_quantity - %s <= low_stock_threshold THEN 'low_stock'
                                ELSE stock_status
                            END
                        WHERE id = %s
                    """, (item['quantity'], item['quantity'], item['quantity'], item['quantity'], item['product_id']))

                connection.commit()

                cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
                order = cursor.fetchone()

                cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
                order_items = cursor.fetchall()

                processed_items = []
                for item in order_items:
                    variation_attributes = None
                    if item['variation_attributes']:
                        try:
                            variation_attributes = json.loads(item['variation_attributes']) if item[
                                'variation_attributes'] else None
                        except:
                            variation_attributes = None

                    processed_items.append({
                        'id': item['id'],
                        'product_id': item['product_id'],
                        'variation_id': item['variation_id'],
                        'product_name': item['product_name'],
                        'product_sku': item['product_sku'],
                        'product_image': item['product_image'],
                        'unit_price': Decimal(str(item['unit_price'])),
                        'quantity': item['quantity'],
                        'total_price': Decimal(str(item['total_price'])),
                        'gst_rate': Decimal(str(item['gst_rate'])),
                        'gst_amount': Decimal(str(item['gst_amount'])),
                        'variation_attributes': variation_attributes
                    })

                shipping_address = json.loads(order['shipping_address']) if isinstance(order['shipping_address'],
                                                                                       str) else order[
                    'shipping_address']
                billing_address = json.loads(order['billing_address']) if order['billing_address'] and isinstance(
                    order['billing_address'], str) else order['billing_address']

                order_response = OrderWithItemsResponse(
                    id=order['id'],
                    uuid=order['uuid'],
                    order_number=order['order_number'],
                    user_id=order['user_id'],
                    subtotal=Decimal(str(order['subtotal'])),
                    shipping_amount=Decimal(str(order['shipping_amount'])),
                    tax_amount=Decimal(str(order['tax_amount'])),
                    discount_amount=Decimal(str(order['discount_amount'])),
                    total_amount=Decimal(str(order['total_amount'])),
                    status=order['status'],
                    payment_status=order['payment_status'],
                    payment_method=order['payment_method'],
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    customer_note=order['customer_note'],
                    is_gst_invoice=bool(order['is_gst_invoice']),
                    gst_number=order['gst_number'],
                    created_at=order['created_at'],
                    updated_at=order['updated_at'],
                    items=processed_items
                )

                if background_tasks:
                    background_tasks.add_task(
                        publish_order_event,
                        order,
                        'created'
                    )

                cache_order(order_id, order_response.model_dump())
                invalidate_order_cache(None, user_id)

                logger.info(f"Order created successfully: {order_number} for user {user_id}")
                return order_response

            except Exception as e:
                connection.rollback()
                raise e

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )


@router.get("/{order_id}", response_model=OrderWithItemsResponse)
async def get_order(
        order_id: int,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        user_roles = current_user.get('roles', [])

        cached_order = get_cached_order(order_id)
        if cached_order and (
                cached_order['user_id'] == user_id or 'admin' in user_roles or 'super_admin' in user_roles):
            logger.info(f"Returning cached order {order_id}")
            return OrderWithItemsResponse(**cached_order)

        with db.get_cursor() as cursor:
            if 'admin' in user_roles or 'super_admin' in user_roles:
                cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            else:
                cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))

            order = cursor.fetchone()
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )

            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            order_items = cursor.fetchall()

            processed_items = []
            for item in order_items:
                variation_attributes = None
                if item['variation_attributes']:
                    try:
                        if isinstance(item['variation_attributes'], str):
                            variation_attributes = json.loads(item['variation_attributes'])
                        else:
                            variation_attributes = item['variation_attributes']
                    except (ValueError, SyntaxError, Exception):
                        variation_attributes = None
                        logger.warning(f"Failed to parse variation_attributes for order item {item['id']}")

                processed_items.append({
                    'id': item['id'],
                    'product_id': item['product_id'],
                    'variation_id': item['variation_id'],
                    'product_name': item['product_name'],
                    'product_sku': item['product_sku'],
                    'product_image': item['product_image'],
                    'unit_price': Decimal(str(item['unit_price'])),
                    'quantity': item['quantity'],
                    'total_price': Decimal(str(item['total_price'])),
                    'gst_rate': Decimal(str(item['gst_rate'])),
                    'gst_amount': Decimal(str(item['gst_amount'])),
                    'variation_attributes': variation_attributes
                })

            shipping_address = {}
            billing_address = None

            try:
                if isinstance(order['shipping_address'], str):
                    shipping_address = json.loads(order['shipping_address'])
                else:
                    shipping_address = order['shipping_address']
            except (ValueError, SyntaxError, Exception):
                shipping_address = {}
                logger.warning(f"Failed to parse shipping_address for order {order['id']}")

            if order['billing_address']:
                try:
                    if isinstance(order['billing_address'], str):
                        billing_address = json.loads(order['billing_address'])
                    else:
                        billing_address = order['billing_address']
                except (ValueError, SyntaxError, Exception):
                    billing_address = None
                    logger.warning(f"Failed to parse billing_address for order {order['id']}")

            order_response = OrderWithItemsResponse(
                id=order['id'],
                uuid=order['uuid'],
                order_number=order['order_number'],
                user_id=order['user_id'],
                subtotal=Decimal(str(order['subtotal'])),
                shipping_amount=Decimal(str(order['shipping_amount'])),
                tax_amount=Decimal(str(order['tax_amount'])),
                discount_amount=Decimal(str(order['discount_amount'])),
                total_amount=Decimal(str(order['total_amount'])),
                status=order['status'],
                payment_status=order['payment_status'],
                payment_method=order['payment_method'],
                shipping_address=shipping_address,
                billing_address=billing_address,
                customer_note=order['customer_note'],
                is_gst_invoice=bool(order['is_gst_invoice']),
                gst_number=order['gst_number'],
                created_at=order['created_at'],
                updated_at=order['updated_at'],
                items=processed_items
            )

            cache_order(order_id, order_response.model_dump())
            return order_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch order"
        )


@router.get("/user/{user_id}", response_model=OrderListResponse)
async def get_user_orders(
        user_id: int,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: Optional[OrderStatus] = None,
        current_user: dict = Depends(get_current_user)
):
    try:
        current_user_id = int(current_user['sub'])
        user_roles = current_user.get('roles', [])

        if current_user_id != user_id and 'admin' not in user_roles and 'super_admin' not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view these orders"
            )

        cache_key = f"user_orders:{user_id}:{page}:{page_size}:{status}"
        cached_orders = get_cached_user_orders(cache_key)
        if cached_orders:
            logger.info(f"Returning cached orders for user {user_id}")
            return OrderListResponse(**cached_orders)

        with db.get_cursor() as cursor:
            query_conditions = ["user_id = %s"]
            query_params = [user_id]

            if status:
                query_conditions.append("status = %s")
                query_params.append(status.value)

            where_clause = " AND ".join(query_conditions)
            count_query = f"SELECT COUNT(*) as total FROM orders WHERE {where_clause}"
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['total']

            offset = (page - 1) * page_size
            orders_query = f"""
                SELECT * FROM orders
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(orders_query, query_params + [page_size, offset])
            orders = cursor.fetchall()

            order_list = []
            for order in orders:
                shipping_address = {}
                billing_address = None

                try:
                    if isinstance(order['shipping_address'], str):
                        shipping_address = json.loads(order['shipping_address'])
                    else:
                        shipping_address = order['shipping_address']
                except (ValueError, SyntaxError, Exception):
                    shipping_address = {}
                    logger.warning(f"Failed to parse shipping_address for order {order['id']}")

                if order['billing_address']:
                    try:
                        if isinstance(order['billing_address'], str):
                            billing_address = json.loads(order['billing_address'])
                        else:
                            billing_address = order['billing_address']
                    except (ValueError, SyntaxError, Exception):
                        billing_address = None
                        logger.warning(f"Failed to parse billing_address for order {order['id']}")

                order_list.append(OrderResponse(
                    id=order['id'],
                    uuid=order['uuid'],
                    order_number=order['order_number'],
                    user_id=order['user_id'],
                    subtotal=Decimal(str(order['subtotal'])),
                    shipping_amount=Decimal(str(order['shipping_amount'])),
                    tax_amount=Decimal(str(order['tax_amount'])),
                    discount_amount=Decimal(str(order['discount_amount'])),
                    total_amount=Decimal(str(order['total_amount'])),
                    status=order['status'],
                    payment_status=order['payment_status'],
                    payment_method=order['payment_method'],
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    customer_note=order['customer_note'],
                    is_gst_invoice=bool(order['is_gst_invoice']),
                    gst_number=order['gst_number'],
                    created_at=order['created_at'],
                    updated_at=order['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size
            response = OrderListResponse(
                orders=order_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

            cache_user_orders(cache_key, response.model_dump())
            return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch user orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.put("/{order_id}/status")
async def update_order_status(
        order_id: int,
        status_update: OrderStatusUpdate,
        background_tasks: BackgroundTasks = None,
        current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )

            old_status = order['status']
            cursor.execute("""
                UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s
            """, (status_update.status.value, order_id))

            cursor.execute("""
                INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type, reason)
                VALUES (%s, 'status', %s, %s, 'admin', %s)
            """, (order_id, old_status, status_update.status.value, status_update.admin_note))

            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            updated_order = cursor.fetchone()

            if background_tasks:
                background_tasks.add_task(
                    publish_order_event,
                    updated_order,
                    'status_updated'
                )

            invalidate_order_cache(order_id, updated_order['user_id'])
            logger.info(
                f"Order {order_id} status updated to {status_update.status.value} by admin {current_user['sub']}")

            return {"message": "Order status updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order status"
        )


@router.post("/{order_id}/cancel")
async def cancel_order(
        order_id: int,
        cancel_request: OrderCancelRequest,
        background_tasks: BackgroundTasks = None,
        current_user: dict = Depends(get_current_user)
):
    try:
        user_id = int(current_user['sub'])
        user_roles = current_user.get('roles', [])

        with db.get_cursor() as cursor:
            if 'admin' in user_roles or 'super_admin' in user_roles:
                cursor.execute("SELECT status, payment_status FROM orders WHERE id = %s", (order_id,))
            else:
                cursor.execute("SELECT status, payment_status FROM orders WHERE id = %s AND user_id = %s",
                               (order_id, user_id))

            order = cursor.fetchone()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )

            if order['status'] in ['shipped', 'delivered', 'cancelled']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order cannot be cancelled in its current status"
                )

            cursor.execute("""
                UPDATE orders
                SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW()
                WHERE id = %s
            """, (order_id,))

            cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
            order_items = cursor.fetchall()

            for item in order_items:
                cursor.execute("""
                    UPDATE products
                    SET stock_quantity = stock_quantity + %s,
                        stock_status = CASE
                            WHEN stock_quantity + %s > low_stock_threshold THEN 'in_stock'
                            ELSE stock_status
                        END
                    WHERE id = %s
                """, (item['quantity'], item['quantity'], item['product_id']))

            change_type = 'admin' if 'admin' in user_roles or 'super_admin' in user_roles else 'customer'
            cursor.execute("""
                INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type, reason)
                VALUES (%s, 'status', %s, 'cancelled', %s, %s)
            """, (order_id, order['status'], change_type, cancel_request.reason))

            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            updated_order = cursor.fetchone()

            if background_tasks:
                background_tasks.add_task(
                    publish_order_event,
                    updated_order,
                    'cancelled'
                )

            invalidate_order_cache(order_id, user_id)
            logger.info(f"Order {order_id} cancelled by user {user_id}")

            return {"message": "Order cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )


@router.get("/admin/orders", response_model=OrderListResponse)
async def get_all_orders(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        status: Optional[OrderStatus] = None,
        current_user: dict = Depends(require_roles(["admin", "super_admin"]))
):
    try:
        with db.get_cursor() as cursor:
            query_conditions = ["1=1"]
            query_params = []

            if status:
                query_conditions.append("status = %s")
                query_params.append(status.value)

            where_clause = " AND ".join(query_conditions)
            count_query = f"SELECT COUNT(*) as total FROM orders WHERE {where_clause}"
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['total']

            offset = (page - 1) * page_size
            orders_query = f"""
                SELECT * FROM orders
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(orders_query, query_params + [page_size, offset])
            orders = cursor.fetchall()

            order_list = []
            for order in orders:
                shipping_address = {}
                billing_address = None

                try:
                    if isinstance(order['shipping_address'], str):
                        shipping_address = json.loads(order['shipping_address'])
                    else:
                        shipping_address = order['shipping_address']
                except (ValueError, SyntaxError, Exception):
                    shipping_address = {}

                if order['billing_address']:
                    try:
                        if isinstance(order['billing_address'], str):
                            billing_address = json.loads(order['billing_address'])
                        else:
                            billing_address = order['billing_address']
                    except (ValueError, SyntaxError, Exception):
                        billing_address = None

                order_list.append(OrderResponse(
                    id=order['id'],
                    uuid=order['uuid'],
                    order_number=order['order_number'],
                    user_id=order['user_id'],
                    subtotal=Decimal(str(order['subtotal'])),
                    shipping_amount=Decimal(str(order['shipping_amount'])),
                    tax_amount=Decimal(str(order['tax_amount'])),
                    discount_amount=Decimal(str(order['discount_amount'])),
                    total_amount=Decimal(str(order['total_amount'])),
                    status=order['status'],
                    payment_status=order['payment_status'],
                    payment_method=order['payment_method'],
                    shipping_address=shipping_address,
                    billing_address=billing_address,
                    customer_note=order['customer_note'],
                    is_gst_invoice=bool(order['is_gst_invoice']),
                    gst_number=order['gst_number'],
                    created_at=order['created_at'],
                    updated_at=order['updated_at']
                ))

            total_pages = (total_count + page_size - 1) // page_size
            return OrderListResponse(
                orders=order_list,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )

    except Exception as e:
        logger.error(f"Failed to fetch all orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )


@router.get("/debug/test")
async def debug_test():
    import traceback
    try:
        from shared import config, db, get_logger
        logger = get_logger(__name__)

        maintenance_mode = config.maintenance_mode
        debug_mode = config.debug_mode

        db_status = "unknown"
        order_count = 0
        try:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                db_status = "connected"
                cursor.execute("SELECT COUNT(*) as count FROM orders")
                order_count = cursor.fetchone()['count']
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
            logger.error(f"Database error: {db_error}")

        redis_status = "unknown"
        try:
            from shared.redis_client import redis_client
            redis_status = "connected" if redis_client._ensure_connection() else "disconnected"
        except Exception as redis_error:
            redis_status = f"error: {str(redis_error)}"

        return {
            "status": "ok",
            "maintenance_mode": maintenance_mode,
            "debug_mode": debug_mode,
            "database": db_status,
            "order_count": order_count,
            "redis": redis_status,
            "service": "order"
        }
    except Exception as e:
        error_traceback = traceback.format_exc()
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": error_traceback,
            "service": "order"
        }


@router.get("/debug/maintenance")
async def debug_maintenance():
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode)),
        "maintenance_mode_raw": str(config.maintenance_mode)
    }


@router.get("/debug/settings")
async def debug_settings():
    config.refresh_cache()
    return {
        "maintenance_mode": config.maintenance_mode,
        "debug_mode": config.debug_mode,
        "app_debug": config.app_debug,
        "log_level": config.log_level,
        "cors_origins": config.cors_origins,
        "cache_info": {
            "cache_size": len(config._cache),
            "cache_keys": list(config._cache.keys())
        }
    }