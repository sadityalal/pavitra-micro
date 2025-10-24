import os
import logging
from typing import Any, Optional
from shared.database.database import db

logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self._cache = {}
    
    def _get_from_db(self, key: str, default: Any = None) -> Any:
        """Get setting from database with caching"""
        if key in self._cache:
            return self._cache[key]
        
        connection = None
        try:
            connection = db.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT setting_value FROM site_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            
            if result:
                value = result['setting_value']
                self._cache[key] = value
                return value
            return default
        except Exception as e:
            logger.warning(f"Failed to get {key} from database: {e}, using default: {default}")
            return default
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def _get_bool_from_db(self, key: str, default: bool = False) -> bool:
        value = self._get_from_db(key, str(default).lower())
        return value.lower() == 'true' if isinstance(value, str) else bool(value)
    
    def _get_int_from_db(self, key: str, default: int = 0) -> int:
        value = self._get_from_db(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _get_float_from_db(self, key: str, default: float = 0.0) -> float:
        value = self._get_from_db(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _get_list_from_db(self, key: str, default: list = None) -> list:
        if default is None:
            default = []
        value = self._get_from_db(key)
        if value and isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(',')]
        return default
    
    # App Config - Some settings still from env for bootstrapping
    @property
    def app_env(self) -> str:
        return os.getenv('APP_ENV', 'production')
    
    @property
    def app_debug(self) -> bool:
        return self._get_bool_from_db('app_debug', False)
    
    # Database - From env (needed for initial connection)
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
    
    # JWT - From env (security sensitive)
    @property
    def jwt_secret(self) -> str:
        return os.getenv('JWT_SECRET', 'fallback-secret-change-in-production')
    
    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', 'HS256')
    
    # Application Settings - From Database
    @property
    def log_level(self) -> str:
        return self._get_from_db('log_level', 'INFO')
    
    @property
    def cors_origins(self) -> list:
        return self._get_list_from_db('cors_origins', ['http://localhost:3000'])
    
    @property
    def site_name(self) -> str:
        return self._get_from_db('site_name', 'Pavitra Trading')
    
    @property
    def site_description(self) -> str:
        return self._get_from_db('site_description', 'Your trusted online shopping destination')
    
    @property
    def default_currency(self) -> str:
        return self._get_from_db('default_currency', 'INR')
    
    @property
    def currency_symbol(self) -> str:
        return self._get_from_db('currency_symbol', '₹')
    
    @property
    def supported_currencies(self) -> list:
        return self._get_list_from_db('supported_currencies', ['INR', 'USD', 'GBP', 'EUR'])
    
    @property
    def default_country(self) -> str:
        return self._get_from_db('default_country', 'IN')
    
    @property
    def default_gst_rate(self) -> float:
        return self._get_float_from_db('default_gst_rate', 18.0)
    
    @property
    def enable_guest_checkout(self) -> bool:
        return self._get_bool_from_db('enable_guest_checkout', True)
    
    @property
    def maintenance_mode(self) -> bool:
        return self._get_bool_from_db('maintenance_mode', False)
    
    @property
    def enable_reviews(self) -> bool:
        return self._get_bool_from_db('enable_reviews', True)
    
    @property
    def enable_wishlist(self) -> bool:
        return self._get_bool_from_db('enable_wishlist', True)
    
    @property
    def min_order_amount(self) -> float:
        return self._get_float_from_db('min_order_amount', 0.0)
    
    @property
    def free_shipping_min_amount(self) -> float:
        return self._get_float_from_db('free_shipping_min_amount', 500.0)
    
    @property
    def max_upload_size(self) -> int:
        return self._get_int_from_db('max_upload_size', 5242880)
    
    @property
    def allowed_file_types(self) -> list:
        return self._get_list_from_db('allowed_file_types', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
    
    @property
    def rate_limit_requests(self) -> int:
        return self._get_int_from_db('rate_limit_requests', 100)
    
    @property
    def rate_limit_window(self) -> int:
        return self._get_int_from_db('rate_limit_window', 900)
    
    @property
    def upload_path(self) -> str:
        return os.getenv('UPLOAD_PATH', '/app/uploads')
    
    def get_service_port(self, service_name: str) -> int:
        # Service ports still from env as they're infrastructure related
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '8000'))
    
    def refresh_cache(self):
        """Force refresh of all settings from database"""
        self._cache.clear()

config = Config()
