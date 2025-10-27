import os
import logging
import json
import time
from typing import Any, Optional, Dict, List
import secrets
logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self._cache = {}
        self._cache_timestamps = {}
        self._db = None
        self._cache_duration = 10  # 10 seconds cache for performance
        self._last_settings_check = 0
        self._settings_version = 0
        self._validate_required_settings()

    def _validate_required_settings(self):
        if not self.debug_mode and not os.getenv('JWT_SECRET'):
            raise ValueError("JWT_SECRET environment variable is required in production")

    def _get_db(self):
        if self._db is None:
            try:
                from .database import db
                self._db = db
                try:
                    self._db.get_connection()
                    logger.info("Database connection established in config")
                except Exception as e:
                    logger.warning(f"Database connection test failed: {e}")
            except ImportError:
                logger.warning("Database not available yet")
                return None
        return self._db

    def _check_settings_version(self):
        """Check if settings have been updated in database"""
        current_time = time.time()
        if current_time - self._last_settings_check < 5:  # Check every 5 seconds max
            return
            
        self._last_settings_check = current_time
        db = self._get_db()
        if not db:
            return
            
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT MAX(updated_at) as last_update FROM site_settings")
            result = cursor.fetchone()
            if result and result['last_update']:
                # Convert timestamp to version number
                new_version = int(result['last_update'].timestamp())
                if new_version > self._settings_version:
                    logger.info("Settings updated in database, clearing cache")
                    self._cache.clear()
                    self._cache_timestamps.clear()
                    self._settings_version = new_version
        except Exception as e:
            logger.warning(f"Failed to check settings version: {e}")
        finally:
            if connection and connection.is_connected():
                connection.close()

    def _get_setting(self, key: str, default: Any = None) -> Any:
        # Always check if settings have been updated
        self._check_settings_version()

        current_time = time.time()
        if (key in self._cache and
                key in self._cache_timestamps and
                current_time - self._cache_timestamps[key] < self._cache_duration):
            return self._cache[key]

        env_key = key.upper()
        if env_key in os.environ:
            value = os.environ[env_key]
            value = self._convert_value(value, type(default))
            self._cache[key] = value
            self._cache_timestamps[key] = current_time
            return value

        db = self._get_db()
        if not db:
            logger.warning(f"Database not available for setting {key}, using default: {default}")
            return default

        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_value, setting_type FROM site_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()

            # DEBUG: Log what we found in database
            logger.info(f"🔧 DATABASE DEBUG - Key: {key}, Found: {result is not None}")
            if result:
                logger.info(
                    f"🔧 DATABASE DEBUG - Raw Value: '{result['setting_value']}', Type: {result['setting_type']}")

            if result:
                # Use the setting_type from database to determine conversion
                db_type = result['setting_type']
                value = self._convert_value_by_type(result['setting_value'], db_type)

                # DEBUG: Log conversion result
                logger.info(
                    f"🔧 CONVERSION DEBUG - Key: {key}, Raw: '{result['setting_value']}', Converted: {value}, Type: {type(value)}")

                self._cache[key] = value
                self._cache_timestamps[key] = current_time
                logger.info(
                    f"Loaded setting {key} from database: {value} (db_type: {db_type}, python_type: {type(value)})")
                return value

            logger.warning(f"Setting {key} not found in database, using default: {default}")
            return default

        except Exception as e:
            logger.warning(f"Failed to get {key} from database: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()

    def _convert_value_by_type(self, value: str, db_type: str) -> Any:
        """Convert value based on database setting_type"""
        if db_type == 'boolean':
            # Handle case when value comes as string "TRUE"/"FALSE" from database
            if isinstance(value, str) and value.upper() in ['TRUE', 'FALSE']:
                return value.upper() == 'TRUE'

            # Existing logic for other cases
            normalized_value = str(value).strip().lower()
            true_values = ['true', '1', 'yes', 'on', 't', 'y']
            false_values = ['false', '0', 'no', 'off', 'f', 'n']

            if normalized_value in true_values:
                return True
            elif normalized_value in false_values:
                return False
            else:
                return False

        elif db_type == 'number':
            try:
                if '.' in str(value):
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                return 0
        elif db_type == 'json':
            try:
                if isinstance(value, str):
                    return json.loads(value)
                return value
            except json.JSONDecodeError:
                return []
        elif db_type == 'list':
            # Handle the new 'list' type
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    if ',' in value:
                        return [item.strip() for item in value.split(',')]
                    return [value]
            return value
        else:  # string type
            return str(value)

    def _convert_value(self, value: str, target_type: Any) -> Any:
        """Fallback conversion based on target type"""
        if target_type == bool:
            return self._convert_value_by_type(value, 'boolean')
        elif target_type == int:
            return self._convert_value_by_type(value, 'number')
        elif target_type == float:
            return self._convert_value_by_type(value, 'number')
        elif target_type == list:
            return self._convert_value_by_type(value, 'json')
        else:
            return str(value)

    def refresh_cache(self):
        """Force refresh all cached settings"""
        self._cache.clear()
        self._cache_timestamps.clear()
        self._settings_version = 0
        self._last_settings_check = 0
        logger.info("Configuration cache forcefully refreshed")

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

    @property
    def jwt_secret(self) -> str:
        secret = os.getenv('JWT_SECRET')
        if not secret:
            if not self.debug_mode:
                raise ValueError("JWT_SECRET environment variable is required in production")
            logger.warning("Using default JWT secret - INSECURE FOR PRODUCTION")
            return 'dev-secret-change-in-production-' + secrets.token_urlsafe(32)
        return secret

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', 'HS256')

    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '8001'))

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

    @property
    def rabbitmq_host(self) -> str:
        return self._get_setting('rabbitmq_host', 'rabbitmq')

    @property
    def rabbitmq_port(self) -> int:
        return self._get_setting('rabbitmq_port', 5672)

    @property
    def rabbitmq_user(self) -> str:
        return self._get_setting('rabbitmq_user', 'admin')

    @property
    def rabbitmq_password(self) -> str:
        return self._get_setting('rabbitmq_password', 'admin123')

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

    @property
    def site_name(self) -> str:
        return self._get_setting('site_name', 'Pavitra Trading')

    @property
    def site_description(self) -> str:
        return self._get_setting('site_description', 'Your trusted online shopping destination')

    @property
    def app_name(self) -> str:
        return self._get_setting('app_name', 'Pavitra Trading')

    @property
    def app_description(self) -> str:
        return self._get_setting('app_description', 'E-commerce Platform')

    @property
    def currency(self) -> str:
        return self._get_setting('currency', 'INR')

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
        # IMPORTANT: Default should be False, not True
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

    @property
    def max_upload_size(self) -> int:
        return self._get_setting('max_upload_size', 5242880)

    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_setting('allowed_file_types', ['jpg', 'jpeg', 'png', 'gif', 'webp'])

    @property
    def upload_path(self) -> str:
        return os.getenv('UPLOAD_PATH', '/app/uploads')

    @property
    def free_shipping_threshold(self) -> float:
        return self._get_setting('free_shipping_threshold', 999.0)

    @property
    def return_period_days(self) -> int:
        return self._get_setting('return_period_days', 10)

    @property
    def site_phone(self) -> str:
        return self._get_setting('site_phone', '+91-9711317009')

    @property
    def site_email(self) -> str:
        return self._get_setting('site_email', 'support@pavitraenterprises.com')

    @property
    def business_hours(self) -> Dict[str, str]:
        return self._get_setting('business_hours', {
            'monday_friday': '9am-6pm',
            'saturday': '10am-4pm',
            'sunday': 'Closed'
        })

    @property
    def telegram_notifications(self) -> bool:
        return self._get_setting('telegram_notifications', False)

    @property
    def whatsapp_notifications(self) -> bool:
        return self._get_setting('whatsapp_notifications', False)

    @property
    def telegram_bot_token(self) -> str:
        return self._get_setting('telegram_bot_token', '')

    @property
    def telegram_chat_id(self) -> str:
        return self._get_setting('telegram_chat_id', '')

    @property
    def whatsapp_api_url(self) -> str:
        return self._get_setting('whatsapp_api_url', '')

    @property
    def whatsapp_api_token(self) -> str:
        return self._get_setting('whatsapp_api_token', '')

config = DatabaseConfig()
