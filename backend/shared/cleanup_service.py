import time
import threading
from shared import get_logger, redis_client
from shared.session_service import session_service

logger = get_logger(__name__)


class CleanupService:
    def __init__(self):
        self.running = False
        self.cleanup_interval = 3600  # 1 hour

    def start_cleanup_task(self):
        """Start background cleanup task"""
        self.running = True
        thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        thread.start()
        logger.info("✅ Cleanup service started")

    def _cleanup_loop(self):
        while self.running:
            try:
                logger.info("🔄 Running scheduled cleanup...")
                self.cleanup_expired_sessions()
                self.cleanup_old_rate_limits()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"❌ Cleanup loop error: {e}")
                time.sleep(300)  # Wait 5 minutes on error

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            cleaned = session_service.cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"✅ Cleaned up {cleaned} expired sessions")
        except Exception as e:
            logger.error(f"❌ Session cleanup failed: {e}")

    def cleanup_old_rate_limits(self):
        """Clean up old rate limiting keys"""
        try:
            patterns = [
                "auth_rate_limit:*",
                "rate_limit:*",
                "login_fails:*",
                "login_lockout:*",
                "secure_rate_limit:*",
                "token_blacklist:*"
            ]

            total_cleaned = 0
            for pattern in patterns:
                try:
                    keys = redis_client.keys(pattern)
                    for key in keys:
                        ttl = redis_client.redis_client.ttl(key)
                        if ttl == -1:  # No TTL set (shouldn't happen)
                            redis_client.delete(key)
                            total_cleaned += 1
                except Exception as e:
                    logger.warning(f"Error cleaning pattern {pattern}: {e}")
                    continue

            if total_cleaned > 0:
                logger.info(f"✅ Cleaned up {total_cleaned} old rate limit keys")

        except Exception as e:
            logger.error(f"❌ Rate limit cleanup failed: {e}")

    def emergency_cleanup(self):
        """Emergency cleanup - use when Redis gets corrupted"""
        try:
            patterns = [
                "secure_session:*",
                "secure_user_session:*",
                "secure_guest_session:*",
                "auth_rate_limit:*",
                "rate_limit:*",
                "login_fails:*",
                "login_lockout:*",
                "token_blacklist:*"
            ]

            total_deleted = 0
            for pattern in patterns:
                keys = redis_client.keys(pattern)
                if keys:
                    deleted = redis_client.delete(*keys)
                    total_deleted += deleted

            logger.info(f"🚨 Emergency cleanup completed: {total_deleted} keys deleted")
            return total_deleted
        except Exception as e:
            logger.error(f"❌ Emergency cleanup failed: {e}")
            return 0


cleanup_service = CleanupService()