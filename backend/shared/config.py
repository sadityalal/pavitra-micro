import os
import logging
import json
from typing import Any, Optional, Dict, List

# Basic logger for config module itself
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self._cache = {}
        self._db = None
    
    def _get_db(self):
        """Lazy load database to avoid circular imports"""
        if self._db is None:
            try:
                from .database import db
                self._db = db
            except ImportError:
                logger.warning("Database not available yet")
                return None
        return self._db
    
    def _get_setting(self, key: str, default: Any = None) -> Any:
        """Get any setting from database with caching"""
        if key in self._cache:
            return self._cache[key]
        
        db = self._get_db()
        if not db:
            return default
        
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_value, setting_type FROM site_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            
            if result:
                value = self._convert_value(result['setting_value'], result['setting_type'])
                self._cache[key] = value
                return value
            return default
        except Exception as e:
            logger.warning(f"Failed to get {key} from database: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def _convert_value(self, value: str, value_type: str) -> Any:
        """Convert string value from DB to proper type"""
        if value_type == 'boolean':
            return value.lower() == 'true'
        elif value_type == 'number':
            try:
                return float(value) if '.' in value else int(value)
            except ValueError:
                return value
        elif value_type == 'json':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:  # string
            return value
    
    def refresh_cache(self):
        """Clear cache to force reload from database"""
        self._cache.clear()
    
    # Database Connection Settings (from environment - needed for bootstrapping)
    @property
    def db_host(self) -> str:
        return os.getenv('DB_HOST', 'mysql')
    
    @property
    def db_port(self) -> int:
        return int(os.getenv('DB_PORT', '3306'))
    
    @property
    def db_name(self) -> str:
        return os.getenv('DB_NAME', 'pavitra_trading')
    
    @property
    def db_user(self) -> str:
        return os.getenv('DB_USER', 'pavitra_app')
    
    @property
    def db_password(self) -> str:
        return os.getenv('DB_PASSWORD', 'app123')
    
    # JWT Settings (from environment for security)
    @property
    def jwt_secret(self) -> str:
        return os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
    
    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', 'HS256')
    
    # Service Ports (from environment - infrastructure)
    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '8000'))
    
    # ALL APPLICATION SETTINGS FROM DATABASE
    
    # Logging Settings
    @property
    def log_level(self) -> str:
        return self._get_setting('log_level', 'INFO')
    
    @property
    def log_retention_days(self) -> int:
        return self._get_setting('log_retention_days', 30)
    
    # Application Settings
    @property
    def app_name(self) -> str:
        return self._get_setting('app_name', 'Pavitra Trading')
    
    @property
    def app_description(self) -> str:
        return self._get_setting('app_description', 'Your trusted online shopping destination')
    
    @property
    def maintenance_mode(self) -> bool:
        return self._get_setting('maintenance_mode', False)
    
    @property
    def debug_mode(self) -> bool:
        return self._get_setting('debug_mode', False)
    
    # CORS Settings
    @property
    def cors_origins(self) -> List[str]:
        return self._get_setting('cors_origins', ['http://localhost:3000'])
    
    # E-commerce Settings
    @property
    def default_currency(self) -> str:
        return self._get_setting('default_currency', 'INR')
    
    @property
    def currency_symbol(self) -> str:
        return self._get_setting('currency_symbol', '₹')
    
    @property
    def supported_currencies(self) -> List[str]:
        return self._get_setting('supported_currencies', ['INR', 'USD', 'EUR', 'GBP'])
    
    @property
    def default_country(self) -> str:
        return self._get_setting('default_country', 'IN')
    
    @property
    def default_gst_rate(self) -> float:
        return self._get_setting('default_gst_rate', 18.0)
    
    @property
    def enable_guest_checkout(self) -> bool:
        return self._get_setting('enable_guest_checkout', True)
    
    @property
    def min_order_amount(self) -> float:
        return self._get_setting('min_order_amount', 0.0)
    
    @property
    def free_shipping_min_amount(self) -> float:
        return self._get_setting('free_shipping_min_amount', 500.0)
    
    # Feature Flags
    @property
    def enable_reviews(self) -> bool:
        return self._get_setting('enable_reviews', True)
    
    @property
    def enable_wishlist(self) -> bool:
        return self._get_setting('enable_wishlist', True)
    
    @property
    def enable_comparison(self) -> bool:
        return self._get_setting('enable_comparison', True)
    
    @property
    def enable_coupons(self) -> bool:
        return self._get_setting('enable_coupons', True)
    
    # File Upload Settings
    @property
    def max_upload_size(self) -> int:
        return self._get_setting('max_upload_size', 5242880)  # 5MB
    
    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_setting('allowed_file_types', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
    
    @property
    def upload_path(self) -> str:
        return os.getenv('UPLOAD_PATH', '/app/uploads')
    
    # Rate Limiting
    @property
    def rate_limit_requests(self) -> int:
        return self._get_setting('rate_limit_requests', 100)
    
    @property
    def rate_limit_window(self) -> int:
        return self._get_setting('rate_limit_window', 900)  # 15 minutes
    
    # Email Settings
    @property
    def smtp_host(self) -> str:
        return self._get_setting('smtp_host', 'smtp.gmail.com')
    
    @property
    def smtp_port(self) -> int:
        return self._get_setting('smtp_port', 587)
    
    @property
    def smtp_username(self) -> str:
        return self._get_setting('smtp_username', '')
    
    @property
    def smtp_password(self) -> str:
        return self._get_setting('smtp_password', '')
    
    @property
    def email_from(self) -> str:
        return self._get_setting('email_from', 'noreply@pavitra-trading.com')
    
    @property
    def email_from_name(self) -> str:
        return self._get_setting('email_from_name', 'Pavitra Trading')
    
    # Payment Settings
    @property
    def razorpay_test_mode(self) -> bool:
        return self._get_setting('razorpay_test_mode', True)
    
    @property
    def razorpay_key_id(self) -> str:
        return self._get_setting('razorpay_key_id', '')
    
    @property
    def stripe_test_mode(self) -> bool:
        return self._get_setting('stripe_test_mode', True)
    
    @property
    def stripe_publishable_key(self) -> str:
        return self._get_setting('stripe_publishable_key', '')
    
    # Notification Settings
    @property
    def email_notifications(self) -> bool:
        return self._get_setting('email_notifications', True)
    
    @property
    def sms_notifications(self) -> bool:
        return self._get_setting('sms_notifications', True)
    
    @property
    def push_notifications(self) -> bool:
        return self._get_setting('push_notifications', True)

# Global config instance
config = DatabaseConfig()
