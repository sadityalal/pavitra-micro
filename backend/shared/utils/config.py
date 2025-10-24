import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    def __init__(self):
        # Load base .env file
        load_dotenv()
        
        # Load environment-specific file
        env = os.getenv('APP_ENV', 'development')
        env_file = f'.env.{env}'
        
        if os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            print(f"Warning: Environment file {env_file} not found, using defaults")
    
    @property
    def app_env(self) -> str:
        return os.getenv('APP_ENV', 'development')
    
    @property
    def app_debug(self) -> bool:
        return os.getenv('APP_DEBUG', 'False').lower() == 'true'
    
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
    def jwt_secret(self) -> str:
        return os.getenv('JWT_SECRET', 'fallback-secret-key')
    
    @property
    def cors_origins(self) -> list:
        origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000')
        return [origin.strip() for origin in origins.split(',')]
    
    def get_service_port(self, service_name: str) -> int:
        port_key = f"{service_name.upper()}_SERVICE_PORT"
        default_ports = {
            'AUTH': 8001,
            'PRODUCT': 8002,
            'ORDER': 8003,
            'USER': 8004,
            'PAYMENT': 8005,
            'NOTIFICATION': 8006
        }
        return int(os.getenv(port_key, default_ports.get(service_name, 8000)))

# Global config instance
config = Config()
