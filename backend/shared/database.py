import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, Any
import logging
import time
from contextlib import contextmanager
from .config import config

logger = logging.getLogger(__name__)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance
    
    def _initialize_pool(self):
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                pool_name="pavitra_pool",
                pool_size=10,
                pool_reset_session=True,
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
                autocommit=True,
                connection_timeout=30,
                buffered=True
            )
            logger.info("Database connection pool created successfully")
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            connection = self.connection_pool.get_connection()
            if connection.is_connected():
                return connection
            else:
                logger.warning("Got disconnected connection, retrying...")
                return self.connection_pool.get_connection()
        except Error as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise
    
    @contextmanager
    def get_cursor(self, dictionary: bool = True):
        """Context manager for database cursor"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except Error as e:
            logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[Any]:
        """Execute a query and return results"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return cursor.rowcount
        except Error as e:
            logger.error(f"Query execution error: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Error as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database instance
db = Database()
