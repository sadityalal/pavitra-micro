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
            'frontend_settings': [],
            'session_settings': []
        }
        env_required = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'JWT_SECRET']
        for env_var in env_required:
            if not os.getenv(env_var):
                missing_configs['environment_variables'].append(env_var)
        all_site_settings = self._get_all_site_settings()
        if not all_site_settings:
            missing_configs['site_settings'].append('ALL_SITE_SETTINGS')
        else:
            critical_site_settings = ['log_level', 'debug_mode', 'maintenance_mode']
            for setting in critical_site_settings:
                if setting not in all_site_settings:
                    missing_configs['site_settings'].append(setting)
        all_frontend_settings = self._get_all_frontend_settings()
        if not all_frontend_settings:
            missing_configs['frontend_settings'].append('ALL_FRONTEND_SETTINGS')
        else:
            critical_frontend_settings = ['site_name', 'default_currency', 'currency_symbol']
            for setting in critical_frontend_settings:
                if setting not in all_frontend_settings:
                    missing_configs['frontend_settings'].append(setting)
        all_session_settings = self._get_all_session_settings()
        if not all_session_settings:
            missing_configs['session_settings'].append('ALL_SESSION_SETTINGS')
        else:
            critical_session_settings = ['session_inactivity_timeout', 'user_session_duration',
                                         'guest_session_duration']
            for setting in critical_session_settings:
                if setting not in all_session_settings:
                    missing_configs['session_settings'].append(setting)
        return missing_configs
    def _get_all_site_settings(self) -> Dict[str, Any]:
        db = self._get_db()
        if not db:
            return {}
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_key, setting_value, setting_type FROM site_settings")
            results = cursor.fetchall()
            settings = {}
            for row in results:
                settings[row['setting_key']] = self._convert_value_by_type(row['setting_value'], row['setting_type'])
            return settings
        except Exception as e:
            logger.error(f"Failed to get all site settings: {e}")
            return {}
        finally:
            if connection and connection.is_connected():
                connection.close()
    def _get_all_frontend_settings(self) -> Dict[str, Any]:
        db = self._get_db()
        if not db:
            return {}
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_key, setting_value, setting_type FROM frontend_settings")
            results = cursor.fetchall()
            settings = {}
            for row in results:
                settings[row['setting_key']] = self._convert_value_by_type(row['setting_value'], row['setting_type'])
            return settings
        except Exception as e:
            logger.error(f"Failed to get all frontend settings: {e}")
            return {}
        finally:
            if connection and connection.is_connected():
                connection.close()
    def _get_all_session_settings(self) -> Dict[str, Any]:
        db = self._get_db()
        if not db:
            return {}
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_key, setting_value, setting_type FROM session_settings")
            results = cursor.fetchall()
            settings = {}
            for row in results:
                settings[row['setting_key']] = self._convert_value_by_type(row['setting_value'], row['setting_type'])
            return settings
        except Exception as e:
            logger.error(f"Failed to get all session settings: {e}")
            return {}
        finally:
            if connection and connection.is_connected():
                connection.close()
    def is_configuration_complete(self) -> bool:
        missing_configs = self.validate_all_configurations()
        return (
                len(missing_configs['environment_variables']) == 0 and
                len(missing_configs['site_settings']) == 0 and
                len(missing_configs['frontend_settings']) == 0 and
                len(missing_configs['session_settings']) == 0
        )
    def get_configuration_status(self) -> Dict[str, Any]:
        missing_configs = self.validate_all_configurations()
        site_count = len(self._get_all_site_settings())
        frontend_count = len(self._get_all_frontend_settings())
        session_count = len(self._get_all_session_settings())
        status = {
            'is_complete': self.is_configuration_complete(),
            'missing_configurations': missing_configs,
            'available_settings': {
                'site_settings_count': site_count,
                'frontend_settings_count': frontend_count,
                'session_settings_count': session_count,
                'total_settings': site_count + frontend_count + session_count
            },
            'summary': {
                'total_missing': (
                        len(missing_configs['environment_variables']) +
                        len(missing_configs['site_settings']) +
                        len(missing_configs['frontend_settings']) +
                        len(missing_configs['session_settings'])
                ),
                'environment_variables_missing': len(missing_configs['environment_variables']),
                'site_settings_missing': len(missing_configs['site_settings']),
                'frontend_settings_missing': len(missing_configs['frontend_settings']),
                'session_settings_missing': len(missing_configs['session_settings'])
            }
        }
        return status
    def _get_db(self):
        if self._db is None:
            try:
                # Import at function level to avoid circular import
                import sys
                if 'shared.database' in sys.modules:
                    from shared.database import db
                    self._db = db
                    logger.info("Database instance loaded in config")
                else:
                    logger.warning("Database module not available yet")
                    return None
            except ImportError as e:
                logger.error(f"Failed to import database module: {e}")
                return None
            except Exception as e:
                logger.error(f"Failed to get database instance in config: {e}")
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
                    COALESCE((SELECT MAX(updated_at) FROM frontend_settings), '1970-01-01'),
                    COALESCE((SELECT MAX(updated_at) FROM session_settings), '1970-01-01')
                )) as last_update
            """)
            result = cursor.fetchone()
            if result and result['last_update']:
                last_update = result['last_update']
                if hasattr(last_update, 'timestamp'):
                    new_version = int(last_update.timestamp())
                else:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(str(last_update).replace('Z', '+00:00'))
                        new_version = int(dt.timestamp())
                    except (ValueError, AttributeError):
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
                value = self._convert_value_by_type(result['setting_value'], result['setting_type'])
                self._cache[key] = value
                self._cache_timestamps[key] = current_time
                logger.debug(f"Loaded setting {key} from site_settings: {value}")
                return value
            return default
        except Exception as e:
            logger.debug(f"Failed to get {key} from site_settings: {e}, using default: {default}")
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
            logger.debug(f"Failed to get frontend setting {key}: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()
    def _get_session_setting(self, key: str, default: Any = None) -> Any:
        self._check_settings_version()
        current_time = time.time()
        cache_key = f"session_{key}"
        if (cache_key in self._cache and
                cache_key in self._cache_timestamps and
                current_time - self._cache_timestamps[cache_key] < self._cache_duration):
            return self._cache[cache_key]
        env_key = f"SESSION_{key.upper()}"
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
                FROM session_settings
                WHERE setting_key = %s
            """, (key,))
            result = cursor.fetchone()
            if result:
                value = self._convert_value_by_type(result['setting_value'], result['setting_type'])
                self._cache[cache_key] = value
                self._cache_timestamps[cache_key] = current_time
                logger.debug(f"Loaded session setting {key} from session_settings: {value}")
                return value
            return default
        except Exception as e:
            logger.debug(f"Failed to get session setting {key}: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()
    def _convert_value_by_type(self, value: str, db_type: str) -> Any:
        if value is None:
            return None
        if db_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
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
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    if ',' in value:
                        return [item.strip() for item in value.split(',')]
                    return [value]
            return value
        else:
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
    def refresh_session_config(self):
        session_keys = [k for k in self._cache.keys() if k.startswith('session_')]
        for key in session_keys:
            self._cache.pop(key, None)
            self._cache_timestamps.pop(key, None)
        logger.info("Session configuration cache refreshed")
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
    @property
    def enable_reviews(self) -> bool:
        return self._get_setting('enable_reviews', True)
    @property
    def enable_wishlist(self) -> bool:
        return self._get_setting('enable_wishlist', True)
    @property
    def enable_guest_checkout(self) -> bool:
        return self._get_setting('enable_guest_checkout', True)
    @property
    def max_cart_quantity_per_product(self) -> int:
        return self._get_setting('max_cart_quantity_per_product', 10)
    @property
    def max_cart_items_total(self) -> int:
        return self._get_setting('max_cart_items_total', 50)
    @property
    def cart_session_timeout_minutes(self) -> int:
        return self._get_setting('cart_session_timeout_minutes', 30)
    @property
    def debug_mode(self) -> bool:
        return self._get_setting('debug_mode', False)
    @property
    def app_debug(self) -> bool:
        return self._get_setting('app_debug', False)
    @property
    def log_level(self) -> str:
        return self._get_setting('log_level', 'INFO')
    @property
    def cors_origins(self) -> List[str]:
        return self._get_setting('cors_origins', [])
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
        return self._get_setting('sms_notifications', False)
    @property
    def push_notifications(self) -> bool:
        return self._get_setting('push_notifications', False)
    @property
    def telegram_notifications(self) -> bool:
        return self._get_setting('telegram_notifications', False)
    @property
    def whatsapp_notifications(self) -> bool:
        return self._get_setting('whatsapp_notifications', False)
    @property
    def max_upload_size(self) -> int:
        return self._get_setting('max_upload_size', 5242880)
    @property
    def allowed_file_types(self) -> List[str]:
        return self._get_setting('allowed_file_types', [])
    @property
    def refund_policy_days(self) -> int:
        return self._get_setting('refund_policy_days', 30)
    @property
    def auto_refund_enabled(self) -> bool:
        return self._get_setting('auto_refund_enabled', True)
    @property
    def refund_processing_fee(self) -> float:
        return self._get_setting('refund_processing_fee', 0.0)
    @property
    def maintenance_mode(self) -> bool:
        return self._get_setting('maintenance_mode', False)
    @property
    def app_name(self) -> str:
        return self.get_frontend_setting('app_name', 'Pavitra Trading')
    @property
    def app_description(self) -> str:
        return self.get_frontend_setting('app_description', 'Your trusted online shopping destination')
    @property
    def email_from(self) -> str:
        return self.get_frontend_setting('email_from', 'noreply@pavitra-trading.com')
    @property
    def email_from_name(self) -> str:
        return self.get_frontend_setting('email_from_name', 'Pavitra Trading')
    @property
    def default_currency(self) -> str:
        return self.get_frontend_setting('default_currency', 'INR')
    @property
    def supported_currencies(self) -> List[str]:
        return self.get_frontend_setting('supported_currencies', [])
    @property
    def default_country(self) -> str:
        return self.get_frontend_setting('default_country', 'IN')
    @property
    def default_gst_rate(self) -> float:
        return self.get_frontend_setting('default_gst_rate', 18.0)
    @property
    def site_name(self) -> str:
        return self.get_frontend_setting('site_name', 'Pavitra Trading')
    @property
    def site_description(self) -> str:
        return self.get_frontend_setting('site_description', 'Your trusted online shopping destination')
    @property
    def currency(self) -> str:
        return self.get_frontend_setting('currency', 'INR')
    @property
    def currency_symbol(self) -> str:
        return self.get_frontend_setting('currency_symbol', '₹')
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
        return self.get_frontend_setting('min_order_amount', 0.0)
    @property
    def free_shipping_min_amount(self) -> float:
        return self.get_frontend_setting('free_shipping_min_amount', 500.0)
    @property
    def free_shipping_threshold(self) -> float:
        return self.get_frontend_setting('free_shipping_threshold', 999.0)
    @property
    def return_period_days(self) -> int:
        return self.get_frontend_setting('return_period_days', 10)
    def get_session_config(self) -> Dict[str, Any]:
        return {
            'inactivity_timeout': self._get_session_setting('session_inactivity_timeout', 1800),
            'guest_session_duration': self._get_session_setting('guest_session_duration', 86400),
            'user_session_duration': self._get_session_setting('user_session_duration', 2592000),
            'max_session_age': self._get_session_setting('max_session_age', 604800),
            'session_timeout': self._get_session_setting('session_timeout', 3600),
            'max_sessions_per_user': self._get_session_setting('max_sessions_per_user', 5),
            'session_rotation_interval': self._get_session_setting('session_rotation_interval', 3600),
            'session_cleanup_interval': self._get_session_setting('session_cleanup_interval', 86400),
            'session_rate_limit_attempts': self._get_session_setting('session_rate_limit_attempts', 10),
            'session_rate_limit_window': self._get_session_setting('session_rate_limit_window', 60),
            'rate_limit_login_attempts': self._get_session_setting('rate_limit_login_attempts', 10),
            'rate_limit_login_window': self._get_session_setting('rate_limit_login_window', 900),
            'rate_limit_session_create': self._get_session_setting('rate_limit_session_create', 5),
            'rate_limit_session_access': self._get_session_setting('rate_limit_session_access', 50),
            'rate_limit_session_update': self._get_session_setting('rate_limit_session_update', 20),
            'rate_limit_session_delete': self._get_session_setting('rate_limit_session_delete', 10),
            'max_login_attempts': self._get_session_setting('max_login_attempts', 5),
            'login_lockout_minutes': self._get_session_setting('login_lockout_minutes', 15),
            'login_rate_limit_window': self._get_session_setting('login_rate_limit_window', 900),
            'max_failed_attempts': self._get_session_setting('max_failed_attempts', 5),
            'failed_attempts_window': self._get_session_setting('failed_attempts_window', 900),
            'token_expiry_hours': self._get_session_setting('token_expiry_hours', 24),
            'enable_csrf_protection': self._get_session_setting('enable_csrf_protection', True),
            'enable_ip_validation': self._get_session_setting('enable_ip_validation', True),
            'enable_user_agent_validation': self._get_session_setting('enable_user_agent_validation', True),
            'enable_session_rotation': self._get_session_setting('enable_session_rotation', True),
            'require_security_token': self._get_session_setting('require_security_token', True),
            'enable_secure_cookies': self._get_session_setting('enable_secure_cookies', True),
            'enable_session_fingerprinting': self._get_session_setting('enable_session_fingerprinting', True),
            'cookie_samesite': self._get_session_setting('cookie_samesite', 'Strict'),
            'cookie_httponly': self._get_session_setting('cookie_httponly', True),
            'cookie_secure': self._get_session_setting('cookie_secure', True)
        }
    def get_security_config(self) -> Dict[str, Any]:
        session_config = self.get_session_config()
        return {k: v for k, v in session_config.items() if any(
            term in k for term in ['enable', 'require', 'cookie', 'max_failed', 'failed_attempts']
        )}
config = DatabaseConfig()