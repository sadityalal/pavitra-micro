import mysql.connector
from mysql.connector import Error, pooling
import logging
import os
import sys

# Add the app directory to Python path
sys.path.append('/app')

from shared.utils.config import config

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool = self._create_pool()

    def _create_pool(self):
        """Create database connection pool"""
        try:
            return pooling.MySQLConnectionPool(
                pool_name="pavitra_pool",
                pool_size=5,
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def get_connection(self):
        """Get connection from pool"""
        try:
            connection = self.pool.get_connection()
            if connection.is_connected():
                return connection
        except Error as e:
            logger.error(f"Failed to get database connection: {e}")
            raise


# Global database instance
db = Database()