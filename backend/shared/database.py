import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, Any, Dict, List
import logging
import time
from contextlib import contextmanager
from .config import config

logger = logging.getLogger(__name__)


class Database:  # KEEP ORIGINAL NAME
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize_pool()
        return cls._instance

    def _initialize_pool(self):
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
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
                    autocommit=False,
                    connection_timeout=30,
                    buffered=True,
                    use_pure=True,
                    charset='utf8mb4',
                    collation='utf8mb4_unicode_ci',
                    connect_timeout=10,
                )

                # Test connection
                test_conn = self.get_connection()
                test_conn.ping(reconnect=True, attempts=3, delay=1)
                test_conn.close()

                logger.info("Database connection pool created successfully")
                return

            except Error as e:
                logger.error(f"Error creating connection pool (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.critical("Failed to create database connection pool after retries")
                    raise

    def get_connection(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                connection = self.connection_pool.get_connection()
                if connection.is_connected():
                    connection.ping(reconnect=False, attempts=1, delay=0)
                    return connection
                else:
                    connection.close()
                    logger.warning(f"Got disconnected connection, retry {attempt + 1}/{max_retries}")
            except Error as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("Failed to get database connection after retries")
                    raise

        raise Error("Failed to get database connection")

    @contextmanager
    def get_cursor(self, dictionary: bool = True):
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
                try:
                    connection.rollback()
                except Error:
                    pass
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except Error:
                    pass
            if connection:
                try:
                    connection.close()
                except Error:
                    pass

    def execute_query(self, query: str, params: tuple = None, dictionary: bool = True) -> Optional[Any]:
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if params and not isinstance(params, (tuple, list)):
            raise ValueError("Parameters must be a tuple or list")

        try:
            with self.get_cursor(dictionary=dictionary) as cursor:
                cursor.execute(query, params or ())
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return cursor.rowcount
        except Error as e:
            logger.error(f"Query execution error: {e}")
            return None

    def execute_many(self, query: str, params_list: list):
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            for params in params_list:
                cursor.execute(query, params)

            connection.commit()
            return True
        except Error as e:
            logger.error(f"Batch execution error: {e}")
            if connection:
                try:
                    connection.rollback()
                except Error:
                    pass
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Error:
                    pass
            if connection:
                try:
                    connection.close()
                except Error:
                    pass

    def health_check(self) -> Dict[str, Any]:
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1 as health")
                basic_health = cursor.fetchone()

                pool_status = {
                    'pool_size': self.connection_pool.pool_size,
                    'active_connections': len(self.connection_pool._cnx_queue._queue),
                    'pool_name': self.connection_pool.pool_name
                }

                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as users_count,
                        (SELECT COUNT(*) FROM products) as products_count,
                        (SELECT COUNT(*) FROM orders) as orders_count,
                        NOW() as server_time
                """)
                db_stats = cursor.fetchone()

                return {
                    'status': 'healthy',
                    'basic_health': basic_health['health'] == 1,
                    'pool_status': pool_status,
                    'database_stats': db_stats,
                    'timestamp': time.time()
                }

        except Error as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }

    def safe_query(self, query: str, params: tuple = None, max_rows: int = 1000) -> Optional[Any]:
        query_upper = query.strip().upper()
        if not query_upper.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
            raise ValueError("Invalid query type")

        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
            query += f" LIMIT {max_rows}"

        return self.execute_query(query, params)


db = Database()