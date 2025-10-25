from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from backend import config, db, sanitize_input, get_logger
from .models import (
    OrderCreate, OrderResponse, OrderWithItemsResponse,
    OrderListResponse, HealthResponse, OrderStatus, PaymentStatus
)
from datetime import datetime

router = APIRouter()
logger = get_logger(__name__)

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
async def create_order(order_data: OrderCreate, user_id: int = 1):  # TODO: Get from auth
    try:
        with db.get_cursor() as cursor:
            # Calculate order totals
            subtotal = 0
            items_data = []
            
            for item in order_data.items:
                # Get product details
                cursor.execute("""
                    SELECT name, sku, main_image_url, base_price, gst_rate, stock_quantity, stock_status
                    FROM products WHERE id = %s AND status = 'active'
                """, (item.product_id,))
                
                product = cursor.fetchone()
                if not product:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {item.product_id} not found"
                    )
                
                if product['stock_status'] == 'out_of_stock':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Product {product['name']} is out of stock"
                    )
                
                if item.quantity > product['stock_quantity'] and product['stock_status'] != 'on_backorder':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Not enough stock for {product['name']}"
                    )
                
                unit_price = float(product['base_price'])
                item_total = unit_price * item.quantity
                subtotal += item_total
                
                items_data.append({
                    'product_id': item.product_id,
                    'variation_id': item.variation_id,
                    'product_name': product['name'],
                    'product_sku': product['sku'],
                    'product_image': product['main_image_url'],
                    'unit_price': unit_price,
                    'quantity': item.quantity,
                    'total_price': item_total,
                    'gst_rate': float(product['gst_rate']),
                    'gst_amount': item_total * float(product['gst_rate']) / 100
                })
            
            # Calculate shipping and tax
            shipping_amount = 0.0
            if subtotal < config.free_shipping_min_amount:
                shipping_amount = 50.0  # Default shipping cost
            
            tax_amount = sum(item['gst_amount'] for item in items_data)
            discount_amount = 0.0  # Could apply coupons here
            total_amount = subtotal + shipping_amount + tax_amount - discount_amount
            
            # Check minimum order amount
            if subtotal < config.min_order_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Minimum order amount is {config.currency_symbol}{config.min_order_amount}"
                )
            
            # Generate order number
            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE DATE(created_at) = CURDATE()")
            daily_count = cursor.fetchone()['count'] + 1
            order_number = f"PT{datetime.now().strftime('%Y%m%d')}{daily_count:04d}"
            
            # Create order
            cursor.execute("""
                INSERT INTO orders (
                    order_number, user_id, subtotal, shipping_amount, tax_amount,
                    discount_amount, total_amount, payment_method, shipping_address,
                    billing_address, customer_note, is_gst_invoice, gst_number
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_number, user_id, subtotal, shipping_amount, tax_amount,
                discount_amount, total_amount, order_data.payment_method.value,
                str(order_data.shipping_address),
                str(order_data.billing_address) if order_data.billing_address else str(order_data.shipping_address),
                sanitize_input(order_data.customer_note) if order_data.customer_note else None,
                order_data.use_gst_invoice,
                sanitize_input(order_data.gst_number) if order_data.gst_number else None
            ))
            
            order_id = cursor.lastrowid
            
            # Create order items
            for item in items_data:
                cursor.execute("""
                    INSERT INTO order_items (
                        order_id, product_id, variation_id, product_name, product_sku,
                        product_image, unit_price, quantity, total_price, gst_rate, gst_amount
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_id, item['product_id'], item['variation_id'],
                    item['product_name'], item['product_sku'], item['product_image'],
                    item['unit_price'], item['quantity'], item['total_price'],
                    item['gst_rate'], item['gst_amount']
                ))
                
                # Update product stock
                cursor.execute("""
                    UPDATE products 
                    SET stock_quantity = stock_quantity - %s,
                        total_sold = total_sold + %s,
                        stock_status = CASE 
                            WHEN stock_quantity - %s <= low_stock_threshold THEN 'low_stock'
                            WHEN stock_quantity - %s <= 0 THEN 'out_of_stock'
                            ELSE stock_status
                        END
                    WHERE id = %s
                """, (item['quantity'], item['quantity'], item['quantity'], item['quantity'], item['product_id']))
            
            # Get complete order with items
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            order_items = cursor.fetchall()
            
            logger.info(f"Order created successfully: {order_number}")
            
            return OrderWithItemsResponse(
                id=order['id'],
                uuid=order['uuid'],
                order_number=order['order_number'],
                user_id=order['user_id'],
                subtotal=float(order['subtotal']),
                shipping_amount=float(order['shipping_amount']),
                tax_amount=float(order['tax_amount']),
                discount_amount=float(order['discount_amount']),
                total_amount=float(order['total_amount']),
                status=order['status'],
                payment_status=order['payment_status'],
                payment_method=order['payment_method'],
                shipping_address=eval(order['shipping_address']),
                billing_address=eval(order['billing_address']) if order['billing_address'] else None,
                customer_note=order['customer_note'],
                is_gst_invoice=bool(order['is_gst_invoice']),
                gst_number=order['gst_number'],
                created_at=order['created_at'],
                updated_at=order['updated_at'],
                items=[
                    {
                        'id': item['id'],
                        'product_id': item['product_id'],
                        'variation_id': item['variation_id'],
                        'product_name': item['product_name'],
                        'product_sku': item['product_sku'],
                        'product_image': item['product_image'],
                        'unit_price': float(item['unit_price']),
                        'quantity': item['quantity'],
                        'total_price': float(item['total_price']),
                        'gst_rate': float(item['gst_rate']),
                        'gst_amount': float(item['gst_amount']),
                        'variation_attributes': item['variation_attributes']
                    }
                    for item in order_items
                ]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@router.get("/{order_id}", response_model=OrderWithItemsResponse)
async def get_order(order_id: int, user_id: int = 1):  # TODO: Get from auth
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM orders WHERE id = %s AND user_id = %s", (order_id, user_id))
            order = cursor.fetchone()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            cursor.execute("SELECT * FROM order_items WHERE order_id = %s", (order_id,))
            order_items = cursor.fetchall()
            
            return OrderWithItemsResponse(
                id=order['id'],
                uuid=order['uuid'],
                order_number=order['order_number'],
                user_id=order['user_id'],
                subtotal=float(order['subtotal']),
                shipping_amount=float(order['shipping_amount']),
                tax_amount=float(order['tax_amount']),
                discount_amount=float(order['discount_amount']),
                total_amount=float(order['total_amount']),
                status=order['status'],
                payment_status=order['payment_status'],
                payment_method=order['payment_method'],
                shipping_address=eval(order['shipping_address']),
                billing_address=eval(order['billing_address']) if order['billing_address'] else None,
                customer_note=order['customer_note'],
                is_gst_invoice=bool(order['is_gst_invoice']),
                gst_number=order['gst_number'],
                created_at=order['created_at'],
                updated_at=order['updated_at'],
                items=[
                    {
                        'id': item['id'],
                        'product_id': item['product_id'],
                        'variation_id': item['variation_id'],
                        'product_name': item['product_name'],
                        'product_sku': item['product_sku'],
                        'product_image': item['product_image'],
                        'unit_price': float(item['unit_price']),
                        'quantity': item['quantity'],
                        'total_price': float(item['total_price']),
                        'gst_rate': float(item['gst_rate']),
                        'gst_amount': float(item['gst_amount']),
                        'variation_attributes': item['variation_attributes']
                    }
                    for item in order_items
                ]
            )
            
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
    page: int = 1,
    page_size: int = 20,
    status: Optional[OrderStatus] = None
):
    try:
        with db.get_cursor() as cursor:
            # Build query conditions
            query_conditions = ["user_id = %s"]
            query_params = [user_id]
            
            if status:
                query_conditions.append("status = %s")
                query_params.append(status.value)
            
            where_clause = " AND ".join(query_conditions)
            
            # Count total orders
            count_query = f"SELECT COUNT(*) as total FROM orders WHERE {where_clause}"
            cursor.execute(count_query, query_params)
            total_count = cursor.fetchone()['total']
            
            # Get orders with pagination
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
                order_list.append(OrderResponse(
                    id=order['id'],
                    uuid=order['uuid'],
                    order_number=order['order_number'],
                    user_id=order['user_id'],
                    subtotal=float(order['subtotal']),
                    shipping_amount=float(order['shipping_amount']),
                    tax_amount=float(order['tax_amount']),
                    discount_amount=float(order['discount_amount']),
                    total_amount=float(order['total_amount']),
                    status=order['status'],
                    payment_status=order['payment_status'],
                    payment_method=order['payment_method'],
                    shipping_address=eval(order['shipping_address']),
                    billing_address=eval(order['billing_address']) if order['billing_address'] else None,
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
        logger.error(f"Failed to fetch user orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: int, 
    status: OrderStatus,
    user_id: int = 1  # TODO: Get from auth, check admin permissions
):
    try:
        with db.get_cursor() as cursor:
            # Check if order exists and belongs to user (or user is admin)
            cursor.execute("SELECT user_id FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()
            
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Update order status
            cursor.execute("""
                UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s
            """, (status.value, order_id))
            
            # Add to order history
            cursor.execute("""
                INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type)
                VALUES (%s, 'status', %s, %s, 'customer')
            """, (order_id, order['status'], status.value))
            
            logger.info(f"Order {order_id} status updated to {status.value}")
            
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
async def cancel_order(order_id: int, user_id: int = 1):
    try:
        with db.get_cursor() as cursor:
            # Check if order can be cancelled
            cursor.execute("""
                SELECT status, payment_status FROM orders 
                WHERE id = %s AND user_id = %s
            """, (order_id, user_id))
            
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
            
            # Update order status
            cursor.execute("""
                UPDATE orders 
                SET status = 'cancelled', cancelled_at = NOW(), updated_at = NOW()
                WHERE id = %s
            """, (order_id,))
            
            # Restore product stock
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
            
            # Add to order history
            cursor.execute("""
                INSERT INTO order_history (order_id, field_changed, old_value, new_value, change_type, reason)
                VALUES (%s, 'status', %s, 'cancelled', 'customer', 'Customer requested cancellation')
            """, (order_id, order['status']))
            
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
