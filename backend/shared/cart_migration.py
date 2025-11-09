import logging
from typing import Optional
from shared import get_logger, db
from shared.session_service import session_service

logger = get_logger(__name__)


def migrate_guest_cart_to_user(guest_session_id: str, user_id: int) -> int:
    """
    Migrate cart items from guest session to user account
    Returns number of items migrated
    """
    try:
        logger.info(f"🔄 Starting cart migration: guest_session={guest_session_id}, user_id={user_id}")

        # Get guest session
        guest_session = session_service.get_session(guest_session_id)
        if not guest_session:
            logger.warning(f"❌ Guest session not found: {guest_session_id}")
            return 0

        if not guest_session.cart_items:
            logger.info("ℹ️ No cart items in guest session to migrate")
            return 0

        logger.info(
            f"📦 Found {len(guest_session.cart_items)} items in guest cart: {list(guest_session.cart_items.keys())}")

        migrated_count = 0
        with db.get_cursor() as cursor:
            # Get user's existing cart items from database
            cursor.execute("""
                SELECT product_id, variation_id, quantity 
                FROM shopping_cart 
                WHERE user_id = %s
            """, (user_id,))
            existing_cart_items = {f"{row['product_id']}_{row['variation_id'] or 'none'}": row for row in
                                   cursor.fetchall()}
            logger.info(f"📊 User already has {len(existing_cart_items)} items in database")

            # Process each guest cart item
            for item_key, guest_item in guest_session.cart_items.items():
                try:
                    if not isinstance(guest_item, dict):
                        logger.warning(f"⚠️ Invalid cart item format: {item_key} = {guest_item}")
                        continue

                    product_id = guest_item.get('product_id')
                    variation_id = guest_item.get('variation_id')
                    quantity = guest_item.get('quantity', 1)

                    if not product_id:
                        logger.warning(f"⚠️ Missing product_id in cart item: {item_key}")
                        continue

                    # Check if product exists and is active
                    cursor.execute("""
                        SELECT id, stock_quantity, max_cart_quantity 
                        FROM products 
                        WHERE id = %s AND status = 'active'
                    """, (product_id,))
                    product = cursor.fetchone()

                    if not product:
                        logger.warning(f"⚠️ Product not found or inactive: {product_id}")
                        continue

                    # Calculate available quantity
                    max_quantity = product['max_cart_quantity'] or 20
                    available_quantity = min(quantity, product['stock_quantity']) if product[
                                                                                         'stock_quantity'] > 0 else quantity
                    available_quantity = min(available_quantity, max_quantity)

                    if available_quantity <= 0:
                        logger.warning(f"⚠️ No available quantity for product: {product_id}")
                        continue

                    # Check if item already exists in user's cart
                    existing_key = f"{product_id}_{variation_id or 'none'}"
                    if existing_key in existing_cart_items:
                        # Update existing item
                        existing_item = existing_cart_items[existing_key]
                        new_quantity = min(existing_item['quantity'] + available_quantity, max_quantity)

                        cursor.execute("""
                            UPDATE shopping_cart 
                            SET quantity = %s, updated_at = NOW() 
                            WHERE user_id = %s AND product_id = %s 
                            AND (variation_id = %s OR (variation_id IS NULL AND %s IS NULL))
                        """, (new_quantity, user_id, product_id, variation_id, variation_id))

                        logger.info(
                            f"📥 Updated existing cart item: product={product_id}, old_qty={existing_item['quantity']}, new_qty={new_quantity}")
                    else:
                        # Insert new item
                        cursor.execute("""
                            INSERT INTO shopping_cart (user_id, product_id, variation_id, quantity)
                            VALUES (%s, %s, %s, %s)
                        """, (user_id, product_id, variation_id, available_quantity))

                        logger.info(f"📥 Added new cart item: product={product_id}, qty={available_quantity}")

                    migrated_count += 1

                except Exception as e:
                    logger.error(f"❌ Failed to migrate cart item {item_key}: {e}")
                    continue

            # Clear guest session cart after successful migration
            if migrated_count > 0:
                try:
                    session_service.update_session_data(guest_session_id, {"cart_items": {}})
                    logger.info(f"✅ Cleared guest session cart: {guest_session_id}")
                except Exception as clear_error:
                    logger.error(f"❌ Failed to clear guest session: {clear_error}")

        logger.info(f"✅ Cart migration completed: {migrated_count} items migrated to user {user_id}")
        return migrated_count

    except Exception as e:
        logger.error(f"❌ Cart migration failed: {e}")
        import traceback
        logger.error(f"❌ Migration traceback: {traceback.format_exc()}")
        return 0