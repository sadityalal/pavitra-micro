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
        self.guest_session_duration = 86400  # 24 hours for guests
        self.user_session_duration = 86400  # 24 hours for users
        self._redis_session_prefix = "session:"
        self._redis_user_session_prefix = "user_session:"
        self._redis_guest_session_prefix = "guest_session:"

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def create_session(self, session_data: Dict[str, Any]) -> Optional[SessionData]:
        try:
            session_id = self.generate_session_id()
            now = datetime.utcnow()

            # ✅ FIX: Proper expiration for both guest and user sessions
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

            # Convert to serializable dict
            session_dict = session.model_dump()
            if isinstance(session_dict.get('session_type'), SessionType):
                session_dict['session_type'] = session_dict['session_type'].value
            else:
                session_dict['session_type'] = str(session_dict.get('session_type')).lower()

            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            # Store in Redis
            key = self._session_key(session_id)
            expiry_seconds = self.user_session_duration if session_dict[
                                                               'session_type'] == SessionType.USER.value else self.guest_session_duration

            redis_client.redis_client.setex(
                key,
                expiry_seconds,
                json.dumps(session_dict)
            )

            # Store mappings for quick lookup
            if session.user_id:
                redis_client.redis_client.setex(
                    f"{self._redis_user_session_prefix}{session.user_id}",
                    self.user_session_duration,
                    session_id
                )
            elif session.guest_id:
                redis_client.redis_client.setex(
                    f"{self._redis_guest_session_prefix}{session.guest_id}",
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
            if not session_id:
                return None

            key = self._session_key(session_id)
            data = redis_client.redis_client.get(key)
            if not data:
                return None

            if isinstance(data, (bytes, bytearray)):
                data = data.decode()

            session_dict = json.loads(data)

            # Convert string dates back to datetime objects
            session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
            session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])

            # Convert session_type string back to enum
            st = session_dict.get('session_type')
            if isinstance(st, str):
                if st.lower() == SessionType.USER.value:
                    session_dict['session_type'] = SessionType.USER
                else:
                    session_dict['session_type'] = SessionType.GUEST

            session_dict['session_id'] = session_id
            session = SessionData(**session_dict)

            # Update activity
            self._update_session_activity_only(session_id)
            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def _update_session_activity_only(self, session_id: str) -> bool:
        try:
            key = self._session_key(session_id)
            data = redis_client.redis_client.get(key)
            if not data:
                return False

            if isinstance(data, (bytes, bytearray)):
                data = data.decode()

            session_dict = json.loads(data)
            session_dict['last_activity'] = datetime.utcnow().isoformat()

            session_type_val = session_dict.get('session_type')
            if isinstance(session_type_val, str) and session_type_val.lower() == SessionType.USER.value:
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
            raw = redis_client.redis_client.get(f"{self._redis_user_session_prefix}{user_id}")
            if not raw:
                return None
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode()
            return self.get_session(raw)
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None

    def get_session_by_guest_id(self, guest_id: str) -> Optional[SessionData]:
        try:
            raw = redis_client.redis_client.get(f"{self._redis_guest_session_prefix}{guest_id}")
            if not raw:
                return None
            if isinstance(raw, (bytes, bytearray)):
                raw = raw.decode()
            return self.get_session(raw)
        except Exception as e:
            logger.error(f"Failed to get session for guest {guest_id}: {e}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            session.last_activity = datetime.utcnow()
            session_dict = session.model_dump()

            if isinstance(session_dict.get('session_type'), SessionType):
                session_dict['session_type'] = session_dict['session_type'].value
            else:
                session_dict['session_type'] = str(session_dict.get('session_type')).lower()

            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            if session.session_type == SessionType.USER:
                new_expiry = self.user_session_duration
            else:
                new_expiry = self.guest_session_duration

            key = self._session_key(session_id)
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
            session_dict = session.model_dump()

            if isinstance(session_dict.get('session_type'), SessionType):
                session_dict['session_type'] = session_dict['session_type'].value
            else:
                session_dict['session_type'] = str(session_dict.get('session_type')).lower()

            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            key = self._session_key(session_id)
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
                redis_client.redis_client.delete(self._session_key(session_id))
                if session.user_id:
                    redis_client.redis_client.delete(f"{self._redis_user_session_prefix}{session.user_id}")
                if session.guest_id:
                    redis_client.redis_client.delete(f"{self._redis_guest_session_prefix}{session.guest_id}")
                logger.info(f"Deleted session: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_expired_sessions(self):
        try:
            # Redis handles TTL automatically
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

    def is_session_active(self, session_id: str) -> bool:
        try:
            return redis_client.redis_client.exists(self._session_key(session_id)) > 0
        except Exception as e:
            logger.error(f"Failed to check session activity {session_id}: {e}")
            return False

    def merge_carts(self, source_session_id: str, target_session_id: str) -> bool:
        try:
            source_session = self.get_session(source_session_id)
            target_session = self.get_session(target_session_id)
            if not source_session or not target_session:
                return False

            source_cart = source_session.cart_items.copy() if source_session.cart_items else {}
            target_cart = target_session.cart_items.copy() if target_session.cart_items else {}

            for product_key, item_data in source_cart.items():
                if product_key in target_cart:
                    target_cart[product_key]['quantity'] += item_data['quantity']
                else:
                    target_cart[product_key] = item_data

            success = self.update_session_data(target_session_id, {"cart_items": target_cart})
            if success:
                self.delete_session(source_session_id)
                logger.info(f"Merged cart from {source_session_id} to {target_session_id}")
            return success

        except Exception as e:
            logger.error(f"Failed to merge carts: {e}")
            return False

    def validate_and_repair_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            if session.cart_items is None:
                session.cart_items = {}
                self.update_session_data(session_id, {"cart_items": {}})
                logger.info(f"Repaired session {session_id}: cart_items was None")

            if session.session_type not in [SessionType.GUEST, SessionType.USER]:
                session.session_type = SessionType.GUEST
                self.update_session_data(session_id, {"session_type": SessionType.GUEST.value})
                logger.info(f"Repaired session {session_id}: invalid session_type")

            return True

        except Exception as e:
            logger.error(f"Failed to validate/repair session {session_id}: {e}")
            return False


session_service = SessionService()