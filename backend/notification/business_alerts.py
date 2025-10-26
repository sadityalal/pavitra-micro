from typing import Dict, Any
from shared import get_logger, config
from .routes import telegram_service, email_service, log_notification

logger = get_logger(__name__)

class BusinessAlertService:
    def __init__(self):
        self.admin_email = getattr(config, 'site_email', 'admin@pavitra-trading.com')
        self.telegram_chat_id = getattr(config, 'telegram_chat_id', None)
    
    def send_new_order_alert(self, order_data: Dict[str, Any]):
        """Send alert to business about new order"""
        try:
            # Telegram alert to business
            telegram_msg = f"""
🛍️ <b>NEW ORDER RECEIVED</b>

Order #: {order_data.get('order_number')}
Customer: {order_data.get('customer_name')}
Amount: ₹{order_data.get('total_amount')}
Items: {order_data.get('item_count', 0)}
Time: {order_data.get('created_at')}

<a href="https://admin.pavitra-trading.com/orders/{order_data.get('id')}">View Order</a>
            """
            
            telegram_service.send_message(self.telegram_chat_id, telegram_msg)
            
            # Email alert to business
            email_subject = f"New Order - {order_data.get('order_number')}"
            email_content = f"""
            <h2>New Order Received</h2>
            <p><strong>Order Number:</strong> {order_data.get('order_number')}</p>
            <p><strong>Customer:</strong> {order_data.get('customer_name')}</p>
            <p><strong>Email:</strong> {order_data.get('customer_email')}</p>
            <p><strong>Amount:</strong> ₹{order_data.get('total_amount')}</p>
            <p><strong>Items:</strong> {order_data.get('item_count', 0)}</p>
            <p><strong>Order Time:</strong> {order_data.get('created_at')}</p>
            """
            
            email_service.send_email(self.admin_email, email_subject, email_content)
            
            logger.info(f"Business alert sent for new order {order_data.get('order_number')}")
            
        except Exception as e:
            logger.error(f"Failed to send business alert: {e}")
    
    def send_low_stock_alert(self, product_data: Dict[str, Any]):
        """Send low stock alert to business"""
        try:
            telegram_msg = f"""
⚠️ <b>LOW STOCK ALERT</b>

Product: {product_data.get('product_name')}
SKU: {product_data.get('sku')}
Current Stock: {product_data.get('current_stock')}
Threshold: {product_data.get('threshold', 5)}

<a href="https://admin.pavitra-trading.com/products/{product_data.get('id')}">Manage Stock</a>
            """
            
            telegram_service.send_message(self.telegram_chat_id, telegram_msg)
            logger.info(f"Low stock alert sent for product {product_data.get('sku')}")
            
        except Exception as e:
            logger.error(f"Failed to send low stock alert: {e}")
    
    def send_daily_sales_report(self, report_data: Dict[str, Any]):
        """Send daily sales report to business"""
        try:
            telegram_msg = f"""
📊 <b>DAILY SALES REPORT</b>

Date: {report_data.get('date')}
Total Orders: {report_data.get('total_orders')}
Total Revenue: ₹{report_data.get('total_revenue')}
Successful Payments: {report_data.get('successful_payments')}
New Customers: {report_data.get('new_customers')}

Top Products:
{self._format_top_products(report_data.get('top_products', []))}
            """
            
            telegram_service.send_message(self.telegram_chat_id, telegram_msg)
            logger.info("Daily sales report sent")
            
        except Exception as e:
            logger.error(f"Failed to send sales report: {e}")
    
    def _format_top_products(self, top_products: list) -> str:
        """Format top products for Telegram message"""
        if not top_products:
            return "No sales today"
        
        formatted = []
        for i, product in enumerate(top_products[:5], 1):
            formatted.append(f"{i}. {product.get('name')} - {product.get('quantity')} sold")
        
        return "\n".join(formatted)

# Global instance
business_alerts = BusinessAlertService()
