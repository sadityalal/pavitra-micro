import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from shared import get_logger, redis_client
from .session_models import SessionData, SessionType

logger = get_logger(__name__)


class SessionService:
    def __init__(self):
        self.inactivity_timeout = 1200  # 20 minutes in seconds
        self.guest_session_duration = 86400  # 24 hours for guest sessions
        self.user_session_duration = 86400  # 24 hours for user sessions

    def generate_session_id(self) -> str:
        return f"session:{uuid.uuid4().hex}"

    def create_session(self, session_data: Dict[str, Any]) -> Optional[SessionData]:
        try:
            session_id = self.generate_session_id()
            now = datetime.utcnow()

            if session_data.get('session_type') == SessionType.USER:
                expires_at = now + timedelta(seconds=self.user_session_duration)
            else:
                expires_at = now + timedelta(seconds=self.guest_session_duration)

            session = SessionData(
                session_id=session_id,
                session_type=session_data['session_type'],
                user_id=session_data.get('user_id'),
                guest_id=session_data.get('guest_id'),
                cart_items=session_data.get('cart_items', {}),
                created_at=now,
                last_activity=now,
                ip_address=session_data.get('ip_address'),
                user_agent=session_data.get('user_agent'),
                expires_at=expires_at
            )

            # Store session in Redis
            key = f"session:{session_id}"
            redis_client.redis_client.setex(
                key,
                self.user_session_duration if session_data.get(
                    'session_type') == SessionType.USER else self.guest_session_duration,
                json.dumps(session.model_dump())
            )

            # Also store user/guest to session mapping
            if session.user_id:
                redis_client.redis_client.setex(
                    f"user_session:{session.user_id}",
                    self.user_session_duration,
                    session_id
                )
            elif session.guest_id:
                redis_client.redis_client.setex(
                    f"guest_session:{session.guest_id}",
                    self.guest_session_duration,
                    session_id
                )

            logger.info(f"Created {session.session_type.value} session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[SessionData]:
        try:
            key = f"session:{session_id}"
            data = redis_client.redis_client.get(key)
            if data:
                session_dict = json.loads(data)
                # Convert string dates back to datetime objects
                session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
                session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
                session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])

                session = SessionData(**session_dict)

                # Update last activity
                self.update_session_activity(session_id)

                return session
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        try:
            session_id = redis_client.redis_client.get(f"user_session:{user_id}")
            if session_id:
                return self.get_session(session_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None

    def get_session_by_guest_id(self, guest_id: str) -> Optional[SessionData]:
        try:
            session_id = redis_client.redis_client.get(f"guest_session:{guest_id}")
            if session_id:
                return self.get_session(session_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for guest {guest_id}: {e}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Update last activity
            session.last_activity = datetime.utcnow()

            # Reset expiration based on activity
            if session.session_type == SessionType.USER:
                new_expiry = self.user_session_duration
            else:
                new_expiry = self.guest_session_duration

            # Update in Redis
            key = f"session:{session_id}"
            redis_client.redis_client.setex(
                key,
                new_expiry,
                json.dumps(session.model_dump())
            )

            return True
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Update session data
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            # Save back to Redis
            key = f"session:{session_id}"
            if session.session_type == SessionType.USER:
                expiry = self.user_session_duration
            else:
                expiry = self.guest_session_duration

            redis_client.redis_client.setex(
                key,
                expiry,
                json.dumps(session.model_dump())
            )

            return True
        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if session:
                # Remove session
                redis_client.redis_client.delete(f"session:{session_id}")

                # Remove mappings
                if session.user_id:
                    redis_client.redis_client.delete(f"user_session:{session.user_id}")
                if session.guest_id:
                    redis_client.redis_client.delete(f"guest_session:{session.guest_id}")

                logger.info(f"Deleted session: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_expired_sessions(self):
        """Clean up expired sessions (to be run periodically)"""
        try:
            # Redis automatically expires keys, but we can clean up mappings
            # This would be called by a background task
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

    def is_session_active(self, session_id: str) -> bool:
        """Check if session exists and is not expired"""
        try:
            return redis_client.redis_client.exists(f"session:{session_id}") > 0
        except Exception as e:
            logger.error(f"Failed to check session activity {session_id}: {e}")
            return False


# Global instance
session_service = SessionService()