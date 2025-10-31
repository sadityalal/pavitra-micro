import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from shared import get_logger, redis_client
from .session_models import SessionData, SessionType

logger = get_logger(__name__)


class SessionService:
    def __init__(self):
        self.inactivity_timeout = 1200
        self.guest_session_duration = 86400
        self.user_session_duration = 86400

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

            # FIX: Properly serialize datetime objects for Redis
            session_dict = session.model_dump()
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            key = f"session:{session_id}"
            redis_client.redis_client.setex(
                key,
                self.user_session_duration if session_data.get(
                    'session_type') == SessionType.USER else self.guest_session_duration,
                json.dumps(session_dict)
            )

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
                # FIX: Properly deserialize datetime objects from Redis
                session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
                session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
                session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])

                session = SessionData(**session_dict)
                # FIX: Remove the recursive call - update activity separately
                self._update_session_activity_only(session_id)
                return session
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def _update_session_activity_only(self, session_id: str) -> bool:
        """Update session activity without recursion"""
        try:
            key = f"session:{session_id}"
            data = redis_client.redis_client.get(key)
            if not data:
                return False

            session_dict = json.loads(data)
            session_dict['last_activity'] = datetime.utcnow().isoformat()

            # Determine expiry based on session type
            if session_dict.get('session_type') == 'user':
                expiry = self.user_session_duration
            else:
                expiry = self.guest_session_duration

            redis_client.redis_client.setex(
                key,
                expiry,
                json.dumps(session_dict)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False

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

            session.last_activity = datetime.utcnow()

            # FIX: Properly serialize for Redis storage
            session_dict = session.model_dump()
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            if session.session_type == SessionType.USER:
                new_expiry = self.user_session_duration
            else:
                new_expiry = self.guest_session_duration

            key = f"session:{session_id}"
            redis_client.redis_client.setex(
                key,
                new_expiry,
                json.dumps(session_dict)
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

            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            session.last_activity = datetime.utcnow()

            # FIX: Proper serialization
            session_dict = session.model_dump()
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            key = f"session:{session_id}"
            if session.session_type == SessionType.USER:
                expiry = self.user_session_duration
            else:
                expiry = self.guest_session_duration

            redis_client.redis_client.setex(
                key,
                expiry,
                json.dumps(session_dict)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if session:
                redis_client.redis_client.delete(f"session:{session_id}")
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
        try:
            # FIX: This would need a more sophisticated approach for production
            # Currently relying on Redis TTL
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

    def is_session_active(self, session_id: str) -> bool:
        try:
            return redis_client.redis_client.exists(f"session:{session_id}") > 0
        except Exception as e:
            logger.error(f"Failed to check session activity {session_id}: {e}")
            return False

    # NEW: Added method for cart migration
    def merge_carts(self, source_session_id: str, target_session_id: str) -> bool:
        try:
            source_session = self.get_session(source_session_id)
            target_session = self.get_session(target_session_id)

            if not source_session or not target_session:
                return False

            source_cart = source_session.cart_items.copy() if source_session.cart_items else {}
            target_cart = target_session.cart_items.copy() if target_session.cart_items else {}

            # Merge carts - for duplicate items, sum quantities
            for product_key, item_data in source_cart.items():
                if product_key in target_cart:
                    target_cart[product_key]['quantity'] += item_data['quantity']
                else:
                    target_cart[product_key] = item_data

            success = self.update_session_data(target_session_id, {"cart_items": target_cart})
            if success:
                # Delete the source session after successful merge
                self.delete_session(source_session_id)
                logger.info(f"Merged cart from {source_session_id} to {target_session_id}")

            return success
        except Exception as e:
            logger.error(f"Failed to merge carts: {e}")
            return False

    def validate_and_repair_session(self, session_id: str) -> bool:
        """Validate session data and repair if necessary"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Ensure cart_items is always a dict, never None
            if session.cart_items is None:
                session.cart_items = {}
                self.update_session_data(session_id, {"cart_items": {}})
                logger.info(f"Repaired session {session_id}: cart_items was None")

            # Ensure session_type is valid
            if session.session_type not in [SessionType.GUEST, SessionType.USER]:
                session.session_type = SessionType.GUEST
                self.update_session_data(session_id, {"session_type": SessionType.GUEST})
                logger.info(f"Repaired session {session_id}: invalid session_type")

            return True
        except Exception as e:
            logger.error(f"Failed to validate/repair session {session_id}: {e}")
            return False


session_service = SessionService()