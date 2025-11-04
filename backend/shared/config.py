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
        self._cache_duration = 100
        self._last_settings_check = 0
        self._settings_version = 0
        self._validate_required_settings()

    def _validate_required_settings(self):
        required_settings = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_settings = []
        for setting in required_settings:
            if not os.getenv(setting):
                missing_settings.append(setting)
        if missing_settings and not self.debug_mode:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")
        if not self.debug_mode and not os.getenv('JWT_SECRET'):
            raise ValueError("JWT_SECRET environment variable is required in production")

    def validate_all_configurations(self) -> Dict[str, List[str]]:
        missing_configs = {
            'environment_variables': [],
            'site_settings': [],
            'frontend_settings': []
        }
        env_required = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'JWT_SECRET']
        for env_var in env_required:
            if not os.getenv(env_var):
                missing_configs['environment_variables'].append(env_var)
        site_settings_to_check = [
            'enable_reviews', 'enable_wishlist', 'enable_guest_checkout',
            'max_cart_quantity_per_product', 'max_cart_items_total', 'cart_session_timeout_minutes',
            'debug_mode', 'app_debug', 'log_level', 'cors_origins',
            'rate_limit_requests', 'rate_limit_window',
            'razorpay_test_mode', 'stripe_test_mode', 'razorpay_key_id', 'razorpay_secret',
            'stripe_publishable_key', 'stripe_secret_key',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'telegram_notifications', 'whatsapp_notifications',
            'max_upload_size', 'allowed_file_types',
            'refund_policy_days', 'auto_refund_enabled', 'refund_processing_fee',
            'redis_host', 'redis_port', 'redis_password', 'redis_db',
            'rabbitmq_host', 'rabbitmq_port', 'rabbitmq_user', 'rabbitmq_password',
            'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password',
            'telegram_bot_token', 'telegram_chat_id', 'whatsapp_api_url', 'whatsapp_api_token'
        ]
        for setting in site_settings_to_check:
            try:
                value = self._get_setting(setting, None)
                if value is None or value == '':
                    missing_configs['site_settings'].append(setting)
            except Exception:
                missing_configs['site_settings'].append(setting)
        frontend_settings_to_check = [
            'app_name', 'app_description',
            'email_from', 'email_from_name',
            'default_currency', 'supported_currencies', 'default_country', 'default_gst_rate',
            'site_name', 'site_description', 'currency', 'currency_symbol',
            'site_phone', 'site_email', 'business_hours',
            'min_order_amount', 'free_shipping_min_amount', 'free_shipping_threshold',
            'return_period_days'
        ]
        for setting in frontend_settings_to_check:
            try:
                value = self.get_frontend_setting(setting, None)
                if value is None or value == '':
                    missing_configs['frontend_settings'].append(setting)
            except Exception:
                missing_configs['frontend_settings'].append(setting)
        return missing_configs

    def is_configuration_complete(self) -> bool:
        missing_configs = self.validate_all_configurations()
        return (
                len(missing_configs['environment_variables']) == 0 and
                len(missing_configs['site_settings']) == 0 and
                len(missing_configs['frontend_settings']) == 0
        )

    def get_configuration_status(self) -> Dict[str, Any]:
        missing_configs = self.validate_all_configurations()
        status = {
            'is_complete': self.is_configuration_complete(),
            'missing_configurations': missing_configs,
            'summary': {
                'total_missing': (
                        len(missing_configs['environment_variables']) +
                        len(missing_configs['site_settings']) +
                        len(missing_configs['frontend_settings'])
                ),
                'environment_variables_missing': len(missing_configs['environment_variables']),
                'site_settings_missing': len(missing_configs['site_settings']),
                'frontend_settings_missing': len(missing_configs['frontend_settings'])
            }
        }
        return status

    def _get_db(self):
        if self._db is None:
            try:
                from .database import db
                # Ensure database is initialized
                if not getattr(db, '_initialized', False):
                    db.initialize()
                self._db = db
                logger.info("Database instance loaded and initialized in config")
            except Exception as e:
                logger.error(f"Failed to initialize database in config: {e}")
                return None
        return self._db

    def _check_settings_version(self):
        current_time = time.time()
        if current_time - self._last_settings_check < 5:
            return
        self._last_settings_check = current_time

        db = self._get_db()
        if not db:
            return

        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT MAX(GREATEST(
                    COALESCE((SELECT MAX(updated_at) FROM site_settings), '1970-01-01'),
                    COALESCE((SELECT MAX(updated_at) FROM frontend_settings), '1970-01-01')
                )) as last_update
            """)
            result = cursor.fetchone()
            if result and result['last_update']:
                # Handle both string and datetime objects
                last_update = result['last_update']
                if hasattr(last_update, 'timestamp'):
                    # It's a datetime object
                    new_version = int(last_update.timestamp())
                else:
                    # It's a string, parse it
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                        new_version = int(dt.timestamp())
                    except (ValueError, AttributeError):
                        # Fallback to current time if parsing fails
                        new_version = int(current_time)

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
            return default
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_value, setting_type FROM site_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            if result:
                db_type = result['setting_type']
                value = self._convert_value_by_type(result['setting_value'], db_type)
                self._cache[key] = value
                self._cache_timestamps[key] = current_time
                logger.debug(f"Loaded setting {key} from site_settings: {value}")
                return value
            return default
        except Exception as e:
            if "connection" not in str(e).lower() or "not available" not in str(e).lower():
                logger.warning(f"Failed to get {key} from site_settings: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()

    def get_frontend_setting(self, key: str, default: Any = None) -> Any:
        self._check_settings_version()
        current_time = time.time()
        cache_key = f"frontend_{key}"
        if (cache_key in self._cache and
                cache_key in self._cache_timestamps and
                current_time - self._cache_timestamps[cache_key] < self._cache_duration):
            return self._cache[cache_key]
        # Check environment first
        env_key = key.upper()
        if env_key in os.environ:
            value = os.environ[env_key]
            value = self._convert_value(value, type(default))
            self._cache[cache_key] = value
            self._cache_timestamps[cache_key] = current_time
            return value
        db = self._get_db()
        if not db:
            return default
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT setting_value, setting_type
                FROM frontend_settings
                WHERE setting_key = %s
            """, (key,))
            result = cursor.fetchone()
            if result:
                value = self._convert_value_by_type(result['setting_value'], result['setting_type'])
                self._cache[cache_key] = value
                self._cache_timestamps[cache_key] = current_time
                logger.debug(f"Loaded frontend setting {key} from frontend_settings: {value}")
                return value
            # Fallback to site_settings if not found in frontend_settings
            cursor.execute("SELECT setting_value, setting_type FROM site_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            if result:
                value = self._convert_value_by_type(result['setting_value'], result['setting_type'])
                self._cache[cache_key] = value
                self._cache_timestamps[cache_key] = current_time
                logger.debug(f"Loaded frontend setting {key} from site_settings (fallback): {value}")
                return value
            return default
        except Exception as e:
            logger.warning(f"Failed to get frontend setting {key}: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()

    def _convert_value_by_type(self, value: str, db_type: str) -> Any:
        if value is None:
            return None

        if db_type == 'boolean':
            # Handle case when value comes as string "TRUE"/"FALSE" from database
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            # Handle string values
            if isinstance(value, str):
                normalized_value = value.strip().lower()
                true_values = ['true', '1', 'yes', 'on', 't', 'y']
                false_values = ['false', '0', 'no', 'off', 'f', 'n']
                if normalized_value in true_values:
                    return True
                elif normalized_value in false_values:
                    return False
                else:
                    return False
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
        self._cache.clear()
        self._cache_timestamps.clear()
        self._settings_version = 0
        self._last_settings_check = 0
        logger.info("Configuration cache forcefully refreshed")

    # ===== SITE SETTINGS (Admin-managed microservice environment variables) =====
    @property
    def db_host(self) -> str:
        return os.getenv('DB_HOST', '')

    @property
    def db_port(self) -> int:
        return int(os.getenv('DB_PORT', '0'))

    @property
    def db_name(self) -> str:
        return os.getenv('DB_NAME', '')

    @property
    def db_user(self) -> str:
        return os.getenv('DB_USER', '')

    @property
    def db_password(self) -> str:
        return os.getenv('DB_PASSWORD', '')

    @property
    def jwt_secret(self) -> str:
        secret = os.getenv('JWT_SECRET', '')
        if not secret:
            if not self.debug_mode:
                raise ValueError("JWT_SECRET environment variable is required in production")
            logger.warning("Using default JWT secret - INSECURE FOR PRODUCTION")
            return 'dev-secret-change-in-production-' + secrets.token_urlsafe(32)
        return secret

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', '')

    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '0'))

    @property
    def redis_host(self) -> str:
        return self._get_setting('redis_host', '')

    @property
    def redis_port(self) -> int:
        return self._get_setting('redis_port', 0)

    @property
    def redis_password(self) -> str:
        return self._get_setting('redis_password', '')

    @property
    def redis_db(self) -> int:
        return self._get_setting('redis_db', 0)

    @property
    def rabbitmq_host(self) -> str:
        return self._get_setting('rabbitmq_host', '')

    @property
    def rabbitmq_port(self) -> int:
        return self._get_setting('rabbitmq_port', 0)

    @property
    def rabbitmq_user(self) -> str:
        return self._get_setting('rabbitmq_user', '')

    @property
    def rabbitmq_password(self) -> str:
        return self._get_setting('rabbitmq_password', '')

    @property
    def smtp_host(self) -> str:
        return self._get_setting('smtp_host', '')

    @property
    def smtp_port(self) -> int:
        return self._get_setting('smtp_port', 0)

    @property
    def smtp_username(self) -> str:
        return self._get_setting('smtp_username', '')

    @property
    def smtp_password(self) -> str:
        return self._get_setting('smtp_password', '')

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

    # System behavior controls
    @property
    def enable_reviews(self) -> bool:
        return self._get_setting('enable_reviews', None)

    @property
    def enable_wishlist(self) -> bool:
        return self._get_setting('enable_wishlist', None)

    @property
    def enable_guest_checkout(self) -> bool:
        return self._get_setting('enable_guest_checkout', None)

    # System limits
    @property
    def max_cart_quantity_per_product(self) -> int:
        return self._get_setting('max_cart_quantity_per_product', None)

    @property
    def max_cart_items_total(self) -> int:
        return self._get_setting('max_cart_items_total', None)

    @property
    def cart_session_timeout_minutes(self) -> int:
        return self._get_setting('cart_session_timeout_minutes', None)

    # Operational settings
    @property
    def debug_mode(self) -> bool:
        return self._get_setting('debug_mode', None)

    @property
    def app_debug(self) -> bool:
        return self._get_setting('app_debug', None)

    @property
    def log_level(self) -> str:
        return self._get_setting('log_level', '')

    @property
    def cors_origins(self) -> List[str]:
        return self._get_setting('cors_origins', [])

    # Security/Performance
    @property
    def rate_limit_requests(self) -> int:
        return self._get_setting('rate_limit_requests', None)

    @property
    def rate_limit_window(self) -> int:
        return self._get_setting('rate_limit_window', None)

    # Payment configuration
    @property
    def razorpay_test_mode(self) -> bool:
        return self._get_setting('razorpay_test_mode', None)

    @property
    def stripe_test_mode(self) -> bool:
        return self._get_setting('stripe_test_mode', None)

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

    # Notification controls
    @property
    def email_notifications(self) -> bool:
        return self._get_setting('email_notifications', None)

    @property
    def sms_notifications(self) -> bool:
        return self._get_setting('sms_notifications', None)

    @property
    def push_notifications(self) -> bool:
        return self._get_setting('push_notifications', None)

    @property
    def telegram_notifications(self) -> bool:
        return self._get_setting('telegram_notifications', None)

    @property
    def whatsapp_notifications(self) -> bool:
        return self._get_setting('whatsapp_notifications', None)

    # System limits
    @property
    def max_upload_size(self) -> int:
        return self._get_setting('max_upload_size', None)

    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_setting('allowed_file_types', [])

    # Business rules
    @property
    def refund_policy_days(self) -> int:
        return self._get_setting('refund_policy_days', None)

    @property
    def auto_refund_enabled(self) -> bool:
        return self._get_setting('auto_refund_enabled', None)

    @property
    def refund_processing_fee(self) -> float:
        return self._get_setting('refund_processing_fee', None)

    # ===== FRONTEND SETTINGS (Static content for webpages) =====
    @property
    def app_name(self) -> str:
        return self.get_frontend_setting('app_name', '')

    @property
    def app_description(self) -> str:
        return self.get_frontend_setting('app_description', '')

    @property
    def email_from(self) -> str:
        return self.get_frontend_setting('email_from', '')

    @property
    def email_from_name(self) -> str:
        return self.get_frontend_setting('email_from_name', '')

    @property
    def default_currency(self) -> str:
        return self.get_frontend_setting('default_currency', '')

    @property
    def supported_currencies(self) -> List[str]:
        return self.get_frontend_setting('supported_currencies', [])

    @property
    def default_country(self) -> str:
        return self.get_frontend_setting('default_country', '')

    @property
    def default_gst_rate(self) -> float:
        return self.get_frontend_setting('default_gst_rate', None)

    @property
    def site_name(self) -> str:
        return self.get_frontend_setting('site_name', '')

    @property
    def site_description(self) -> str:
        return self.get_frontend_setting('site_description', '')

    @property
    def currency(self) -> str:
        return self.get_frontend_setting('currency', '')

    @property
    def currency_symbol(self) -> str:
        return self.get_frontend_setting('currency_symbol', '')

    @property
    def site_phone(self) -> str:
        return self.get_frontend_setting('site_phone', '')

    @property
    def site_email(self) -> str:
        return self.get_frontend_setting('site_email', '')

    @property
    def business_hours(self) -> Dict[str, str]:
        return self.get_frontend_setting('business_hours', {})

    @property
    def min_order_amount(self) -> float:
        return self.get_frontend_setting('min_order_amount', None)

    @property
    def free_shipping_min_amount(self) -> float:
        return self.get_frontend_setting('free_shipping_min_amount', None)

    @property
    def free_shipping_threshold(self) -> float:
        return self.get_frontend_setting('free_shipping_threshold', None)

    @property
    def return_period_days(self) -> int:
        return self.get_frontend_setting('return_period_days', None)

    @property
    def maintenance_mode(self) -> bool:
        return self._get_setting('maintenance_mode', None)


config = DatabaseConfig()