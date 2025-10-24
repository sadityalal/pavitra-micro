import mysql.connector
from mysql.connector import Error, pooling
import logging
import os

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None
        self._create_pool()
    
    def _get_db_config(self):
        """Get database configuration without circular imports"""
        return {
            'host': os.getenv('DB_HOST', 'mysql'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'database': os.getenv('DB_NAME', 'pavitra_trading'),
            'user': os.getenv('DB_USER', 'pavitra_app'),
            'password': os.getenv('DB_PASSWORD', 'app123')
        }
    
    def _create_pool(self):
        try:
            db_config = self._get_db_config()
            self.pool = pooling.MySQLConnectionPool(
                pool_name="pavitra_pool",
                pool_size=10,
                host=db_config['host'],
                port=db_config['port'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info("Database connection pool created successfully")
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def get_connection(self):
        try:
            connection = self.pool.get_connection()
            if connection.is_connected():
                return connection
        except Error as e:
            logger.error(f"Failed to get database connection: {e}")
            raise

db = Database()
