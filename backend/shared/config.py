import os
import logging
import json
from typing import Any, Optional, Dict, List
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self._cache = {}
        self._db = None

    def _get_db(self):
        if self._db is None:
            try:
                from .database import db
                self._db = db
            except ImportError:
                logger.warning("Database not available yet")
                return None
        return self._db

    def _get_setting(self, key: str, default: Any = None) -> Any:
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
        else:
            return value

    def refresh_cache(self):
        self._cache.clear()

    # === ESSENTIAL BOOTSTRAP SETTINGS (Environment Only) ===
    
    # Database Configuration - Essential for bootstrapping
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

    # JWT Configuration - Security sensitive, keep in environment
    @property
    def jwt_secret(self) -> str:
        return os.getenv('JWT_SECRET', 'dev-secret-change-in-production')

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', 'HS256')

    # Service Ports - Docker infrastructure
    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '8000'))

    # Upload Path - File system path
    @property
    def upload_path(self) -> str:
        return os.getenv('UPLOAD_PATH', '/app/uploads')

    # === ALL OTHER SETTINGS (From Database) ===

    # Redis Configuration
    @property
    def redis_host(self) -> str:
        return self._get_setting('redis_host', 'redis')

    @property
    def redis_port(self) -> int:
        return self._get_setting('redis_port', 6379)

    @property
    def redis_password(self) -> str:
        return self._get_setting('redis_password', 'redis123')

    @property
    def redis_db(self) -> int:
        return self._get_setting('redis_db', 0)

    # RabbitMQ Configuration
    @property
    def rabbitmq_host(self) -> str:
        return self._get_setting('rabbitmq_host', '')

    @property
    def rabbitmq_port(self) -> int:
        return self._get_setting('rabbitmq_port', )

    @property
    def rabbitmq_user(self) -> str:
        return self._get_setting('rabbitmq_user', )

    @property
    def rabbitmq_password(self) -> str:
        return self._get_setting('rabbitmq_password', )

    # SMTP Configuration
    @property
    def smtp_host(self) -> str:
        return self._get_setting('smtp_host', )

    @property
    def smtp_port(self) -> int:
        return self._get_setting('smtp_port', )

    @property
    def smtp_username(self) -> str:
        return self._get_setting('smtp_username', )

    @property
    def smtp_password(self) -> str:
        return self._get_setting('smtp_password',)

    @property
    def email_from(self) -> str:
        return self._get_setting('email_from', )

    @property
    def email_from_name(self) -> str:
        return self._get_setting('email_from_name',)

    # Application Settings
    @property
    def site_name(self) -> str:
        return self._get_setting('site_name', )

    @property
    def site_description(self) -> str:
        return self._get_setting('site_description',)

    @property
    def app_name(self) -> str:
        return self._get_setting('app_name',)

    @property
    def app_description(self) -> str:
        return self._get_setting('app_description',)

    @property
    def currency(self) -> str:
        return self._get_setting('currency', )

    @property
    def currency_symbol(self) -> str:
        return self._get_setting('currency_symbol', '₹')

    @property
    def default_currency(self) -> str:
        return self._get_setting('default_currency', 'INR')

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
    def maintenance_mode(self) -> bool:
        return self._get_setting('maintenance_mode', False)

    @property
    def debug_mode(self) -> bool:
        return self._get_setting('debug_mode', False)

    @property
    def app_debug(self) -> bool:
        return self._get_setting('app_debug', False)

    @property
    def enable_reviews(self) -> bool:
        return self._get_setting('enable_reviews', True)

    @property
    def enable_wishlist(self) -> bool:
        return self._get_setting('enable_wishlist', True)

    @property
    def min_order_amount(self) -> float:
        return self._get_setting('min_order_amount', 0.0)

    @property
    def free_shipping_min_amount(self) -> float:
        return self._get_setting('free_shipping_min_amount', 500.0)

    @property
    def max_upload_size(self) -> int:
        return self._get_setting('max_upload_size', 5242880)

    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_setting('allowed_file_types', ['jpg', 'jpeg', 'png', 'gif', 'webp'])

    @property
    def log_level(self) -> str:
        return self._get_setting('log_level', 'INFO')

    @property
    def cors_origins(self) -> List[str]:
        return self._get_setting('cors_origins', ['http://localhost:3000'])

    @property
    def rate_limit_requests(self) -> int:
        return self._get_setting('rate_limit_requests', 100)

    @property
    def rate_limit_window(self) -> int:
        return self._get_setting('rate_limit_window', 900)

    @property
    def razorpay_test_mode(self) -> bool:
        return self._get_setting('razorpay_test_mode', True)

    @property
    def stripe_test_mode(self) -> bool:
        return self._get_setting('stripe_test_mode', True)

    @property
    def email_notifications(self) -> bool:
        return self._get_setting('email_notifications', True)

    @property
    def sms_notifications(self) -> bool:
        return self._get_setting('sms_notifications', True)

    @property
    def push_notifications(self) -> bool:
        return self._get_setting('push_notifications', True)

    @property
    def refund_policy_days(self) -> int:
        return self._get_setting('refund_policy_days', 30)

    @property
    def auto_refund_enabled(self) -> bool:
        return self._get_setting('auto_refund_enabled', False)

    @property
    def refund_processing_fee(self) -> float:
        return self._get_setting('refund_processing_fee', 0.0)

    # Payment Gateway Settings
    @property
    def razorpay_key_id(self) -> str:
        return self._get_setting('razorpay_key_id', '')

    @property
    def razorpay_secret(self) -> str:
        return self._get_setting('razorpay_secret', '')

    @property
    def stripe_publishable_key(self) -> str:
        return self._get_setting('stripe_publishable_key', '')

    @property
    def stripe_secret_key(self) -> str:
        return self._get_setting('stripe_secret_key', '')

    @property
    def mysql_host_name(self) -> str:
        return self._get_setting('mysql_host_name', '')
    @property
    def mysql_user(self) -> str:
        return self._get_setting('mysql_user', '')
    @property
    def mysql_password(self) -> str:
        return self._get_setting('mysql_password', '')

config = DatabaseConfig()
