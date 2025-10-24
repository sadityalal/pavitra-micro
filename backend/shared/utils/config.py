import os
from dotenv import load_dotenv
from typing import List


class Config:
    def __init__(self):
        self._load_environment()

    def _load_environment(self):
        """Load environment variables from .env file"""
        env = os.getenv('APP_ENV', 'development')
        env_file = f'.env.{env}'

        if os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            print(f"Warning: Environment file {env_file} not found")

    @property
    def app_env(self) -> str:
        return os.getenv('APP_ENV', 'development')

    @property
    def app_debug(self) -> bool:
        return os.getenv('APP_DEBUG', 'false').lower() == 'true'

    @property
    def db_host(self) -> str:
        return os.getenv('DB_HOST', 'localhost')

    @property
    def db_port(self) -> int:
        return int(os.getenv('DB_PORT', '3306'))

    @property
    def db_name(self) -> str:
        return os.getenv('DB_NAME', 'pavitra_trading')

    @property
    def db_user(self) -> str:
        return os.getenv('DB_USER', 'pavitra_user')

    @property
    def db_password(self) -> str:
        return os.getenv('DB_PASSWORD', 'user123')

    @property
    def db_ssl(self) -> bool:
        return os.getenv('DB_SSL', 'false').lower() == 'true'

    @property
    def jwt_secret(self) -> str:
        return os.getenv('JWT_SECRET', 'fallback-secret-key')

    @property
    def jwt_algorithm(self) -> str:
        return os.getenv('JWT_ALGORITHM', 'HS256')

    @property
    def jwt_expiry_minutes(self) -> int:
        return int(os.getenv('JWT_EXPIRY_MINUTES', '30'))

    @property
    def cors_origins(self) -> List[str]:
        origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        return [origin.strip() for origin in origins.split(',')]

    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')

    @property
    def smtp_host(self) -> str:
        return os.getenv('SMTP_HOST', 'smtp.gmail.com')

    @property
    def smtp_port(self) -> int:
        return int(os.getenv('SMTP_PORT', '587'))

    @property
    def smtp_user(self) -> str:
        return os.getenv('SMTP_USER', '')

    @property
    def smtp_pass(self) -> str:
        return os.getenv('SMTP_PASS', '')

    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        return int(os.getenv(port_key, '8000'))


config = Config()