import mysql.connector
from mysql.connector import Error
import logging
import os

logger = logging.getLogger(__name__)

class DatabaseConfig:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.database = os.getenv('DB_NAME', 'pavitra_trading')
        self.username = os.getenv('DB_USER', 'pavitra_user')
        self.password = os.getenv('DB_PASSWORD', 'user123')

    def get_connection(self):
        """Create and return database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if connection.is_connected():
                logger.info(f"Database connection established to {self.database}")
                return connection
                
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            raise

# Global database instance
db_config = DatabaseConfig()
