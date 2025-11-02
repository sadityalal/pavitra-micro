import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, Any, Dict, List
import logging
import time
from contextlib import contextmanager
from .config import config

logger = logging.getLogger(__name__)


class Database:
    _instance = None
    _pool = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        """Initialize database connection - call this after logging is set up"""
        if not self._initialized:
            self._initialize_pool()
            self._initialized = True

    def _initialize_pool(self):
        max_retries = 3
        retry_delay = 2
        logger.info(
            f"🚀 Attempting to connect to database: {config.db_host}:{config.db_port}, db: {config.db_name}, user: {config.db_user}")

        for attempt in range(max_retries):
            try:
                logger.info(f"📊 Database connection attempt {attempt + 1}/{max_retries}")
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

                # Test the connection
                test_conn = self.connection_pool.get_connection()
                if test_conn.is_connected():
                    logger.info("✅ Database connection successful!")
                    test_conn.ping(reconnect=True, attempts=3, delay=1)
                    test_conn.close()
                    logger.info("🎉 Database connection pool created successfully")
                    self._initialized = True  # Add this line
                    return
                else:
                    logger.error("❌ Database connection failed - not connected")
                    if test_conn:
                        test_conn.close()

            except Error as e:
                logger.error(f"❌ Database connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.critical("💥 Failed to create database connection pool after all retries")
                    self.connection_pool = None
                    raise

    def get_connection(self):
        if not self._initialized:
            self.initialize()

        if not self.connection_pool:
            logger.warning("🔄 Connection pool not initialized, reinitializing...")
            self._initialize_pool()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                connection = self.connection_pool.get_connection()
                if connection and connection.is_connected():
                    # Test connection with a simple query
                    try:
                        connection.ping(reconnect=True, attempts=1, delay=0)
                        return connection
                    except Error:
                        try:
                            connection.close()
                        except:
                            pass
                        continue
                else:
                    try:
                        if connection:
                            connection.close()
                    except:
                        pass
                    logger.warning(f"🔌 Got disconnected connection, retry {attempt + 1}/{max_retries}")

            except Error as e:
                logger.warning(f"🔌 Connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error("💥 Failed to get database connection after retries")
                    try:
                        self._initialize_pool()
                        # One more attempt after reinitialization
                        if self.connection_pool:
                            connection = self.connection_pool.get_connection()
                            if connection and connection.is_connected():
                                return connection
                    except Exception as pool_error:
                        logger.error(f"💥 Pool reinitialization also failed: {pool_error}")
                    raise
                time.sleep(1)  # Wait before retry

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
            logger.error(f"💥 Database error: {e}")
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
            logger.error(f"💥 Query execution error: {e}")
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
            logger.error(f"💥 Batch execution error: {e}")
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

                # FIXED: Safe way to get pool status without accessing internal _queue attribute
                pool_status = {
                    'pool_size': self.connection_pool.pool_size,
                    'pool_name': self.connection_pool.pool_name
                }

                # Try to get active connections count safely
                try:
                    # For newer mysql-connector-python versions
                    if hasattr(self.connection_pool, '_cnx_queue'):
                        active_connections = len(self.connection_pool._cnx_queue)
                    else:
                        active_connections = 'unknown'
                except (AttributeError, TypeError):
                    active_connections = 'unknown'

                pool_status['active_connections'] = active_connections

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
            logger.error(f"💥 Database health check failed: {e}")
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

    def _monitor_connection_health(self):
        """Monitor and repair connection pool health"""
        try:
            if not self.connection_pool:
                return

            # Try to get a connection and immediately return it
            test_conn = None
            try:
                test_conn = self.connection_pool.get_connection()
                if test_conn and test_conn.is_connected():
                    test_conn.ping(reconnect=False)
            except Exception as e:
                logger.warning(f"Connection pool health check failed: {e}")
                # Reinitialize pool if health check fails
                self._initialize_pool()
            finally:
                if test_conn:
                    try:
                        test_conn.close()
                    except:
                        pass
        except Exception as e:
            logger.error(f"Connection health monitoring failed: {e}")


db = Database()