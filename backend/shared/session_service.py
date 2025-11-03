import uuid
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from shared import get_logger, redis_client, db
from .session_models import SessionData, SessionType

logger = get_logger(__name__)


class SessionService:
    def __init__(self):
        self.inactivity_timeout = 1200
        self.guest_session_duration = 86400  # 24 hours
        self.user_session_duration = 86400  # 24 hours
        self._redis_session_prefix = "session:"
        self._redis_user_session_prefix = "user_session:"
        self._redis_guest_session_prefix = "guest_session:"
        self._rate_limit_prefix = "session_rate_limit:"
        self.max_sessions_per_user = 5  # Prevent session flooding
        self.session_rotation_interval = 3600  # Rotate sessions every hour
        self.rate_limit_attempts = 10  # Max session operations per minute
        self.rate_limit_window = 60  # 1 minute window

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def _rate_limit_key(self, identifier: str) -> str:
        return f"{self._rate_limit_prefix}{identifier}"

    def _check_rate_limit(self, identifier: str) -> bool:
        try:
            current_time = int(time.time())
            window_start = current_time // self.rate_limit_window
            rate_key = f"{self._rate_limit_key(identifier)}:{window_start}"
            current_attempts = redis_client.incr(rate_key)
            if current_attempts == 1:
                redis_client.expire(rate_key, self.rate_limit_window)
            if current_attempts > self.rate_limit_attempts:
                logger.warning(f"Rate limit exceeded for session operations: {identifier}")
                return False
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Fail open on rate limit errors

    def _cleanup_old_user_sessions(self, user_id: int):
        try:
            user_sessions = []
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            all_keys = redis_client.redis_client.keys(f"{self._redis_session_prefix}*")
            for key in all_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        if session_data.get('user_id') == user_id:
                            session_id = key.replace(self._redis_session_prefix, "")
                            created_at = datetime.fromisoformat(session_data['created_at'])
                            user_sessions.append((session_id, created_at))
                except:
                    continue
            if len(user_sessions) > self.max_sessions_per_user:
                user_sessions.sort(key=lambda x: x[1])
                sessions_to_remove = user_sessions[:-self.max_sessions_per_user]

                for session_id, _ in sessions_to_remove:
                    self.delete_session(session_id)
                    logger.info(f"Cleaned up old session {session_id} for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup old user sessions: {e}")

    def create_session(self, session_data: Dict[str, Any]) -> Optional[SessionData]:
        try:
            client_ip = session_data.get('ip_address', 'unknown')
            if not self._check_rate_limit(f"create:{client_ip}"):
                raise HTTPException(
                    status_code=429,
                    detail="Too many session creation attempts"
                )

            session_id = self.generate_session_id()
            now = datetime.utcnow()

            if session_data.get('session_type') == SessionType.USER:
                expires_at = now + timedelta(seconds=self.user_session_duration)
                user_id = session_data.get('user_id')
                if user_id:
                    self._cleanup_old_user_sessions(user_id)
            else:
                expires_at = now + timedelta(seconds=self.guest_session_duration)

            cart_items = session_data.get('cart_items', {})
            if cart_items is None:
                cart_items = {}

            session = SessionData(
                session_id=session_id,
                session_type=session_data['session_type'],
                user_id=session_data.get('user_id'),
                guest_id=session_data.get('guest_id'),
                cart_items=cart_items,
                created_at=now,
                last_activity=now,
                ip_address=session_data.get('ip_address'),
                user_agent=session_data.get('user_agent'),
                expires_at=expires_at
            )

            session_dict = session.model_dump()
            session_dict['session_type'] = session_dict['session_type'].value
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            key = self._session_key(session_id)
            expiry_seconds = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration

            success = redis_client.setex(
                key,
                expiry_seconds,
                json.dumps(session_dict)
            )

            if not success:
                logger.error(f"Failed to save session to Redis: {session_id}")
                return None

            if session.user_id:
                mapping_key = f"{self._redis_user_session_prefix}{session.user_id}:{session_id}"
                redis_client.setex(
                    mapping_key,
                    self.user_session_duration,
                    session_id
                )
            elif session.guest_id:
                mapping_key = f"{self._redis_guest_session_prefix}{session.guest_id}:{session_id}"
                redis_client.setex(
                    mapping_key,
                    self.guest_session_duration,
                    session_id
                )

            logger.info(
                f"Created {session.session_type.value} session: {session_id} for IP: {session_data.get('ip_address', 'unknown')}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def get_session(self, session_id: str, request_ip: str = None, request_user_agent: str = None) -> Optional[
        SessionData]:
        try:
            # Rate limit session access
            if not self._check_rate_limit(f"access:{session_id}"):
                logger.warning(f"Rate limited session access: {session_id}")
                return None

            if not session_id:
                return None

            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                return None

            session_dict = json.loads(data)
            session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
            session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])
            session_type_str = session_dict.get('session_type', 'guest')
            session_dict['session_type'] = SessionType.USER if session_type_str == 'user' else SessionType.GUEST

            if session_dict.get('cart_items') is None:
                session_dict['cart_items'] = {}

            session_dict['session_id'] = session_id
            session = SessionData(**session_dict)

            if request_ip and request_user_agent:
                if not self.validate_session_origin(session, request_ip, request_user_agent):
                    logger.warning(f"Session origin validation failed for {session_id}")
                    return None

            if self._should_rotate_session(session):
                logger.info(f"Rotating session {session_id} for security")
                return self.rotate_session(session_id)

            self._update_session_activity_only(session_id)

            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def validate_session_origin(self, session: SessionData, request_ip: str, request_user_agent: str) -> bool:
        try:
            if session.ip_address and session.ip_address != request_ip:
                logger.warning(
                    f"Session IP mismatch: {session.ip_address} vs {request_ip} for session {session.session_id}")
                return False
            if session.user_agent and session.user_agent != request_user_agent:
                logger.warning(f"Session User-Agent mismatch for session {session.session_id}")

            return True
        except Exception as e:
            logger.error(f"Session origin validation failed: {e}")
            return True  # Fail open on validation errors

    def _should_rotate_session(self, session: SessionData) -> bool:
        """Check if session should be rotated for security"""
        try:
            session_age = datetime.utcnow() - session.created_at
            return session_age.total_seconds() > self.session_rotation_interval
        except Exception as e:
            logger.error(f"Failed to check session rotation: {e}")
            return False

    def rotate_session(self, old_session_id: str) -> Optional[SessionData]:
        """Rotate session ID to prevent session fixation"""
        try:
            old_session = self.get_session(old_session_id)
            if not old_session:
                return None

            new_session = self.create_session({
                'session_type': old_session.session_type,
                'user_id': old_session.user_id,
                'guest_id': old_session.guest_id,
                'cart_items': old_session.cart_items,
                'ip_address': old_session.ip_address,
                'user_agent': old_session.user_agent
            })

            if new_session:
                self.delete_session(old_session_id)
                logger.info(f"Successfully rotated session {old_session_id} -> {new_session.session_id}")

            return new_session
        except Exception as e:
            logger.error(f"Failed to rotate session {old_session_id}: {e}")
            return None

    def _update_session_activity_only(self, session_id: str) -> bool:
        try:
            if not self._check_rate_limit(f"activity:{session_id}"):
                return False

            session = self.get_session(session_id)
            if not session:
                return False

            session.last_activity = datetime.utcnow()
            session_dict = session.model_dump()
            session_dict['session_type'] = session_dict['session_type'].value
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration
            key = self._session_key(session_id)

            return redis_client.setex(
                key,
                expiry,
                json.dumps(session_dict)
            )

        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False

    def update_session_activity(self, session_id: str) -> bool:
        return self._update_session_activity_only(session_id)

    def migrate_guest_to_user_session(self, guest_session_id: str, user_id: int) -> Optional[SessionData]:
        """Migrate guest session to user session and merge carts"""
        try:
            if not self._check_rate_limit(f"migrate:{user_id}"):
                return None

            guest_session = self.get_session(guest_session_id)
            if not guest_session or guest_session.session_type != SessionType.GUEST:
                return None

            user_session = self.get_session_by_user_id(user_id)
            merged_cart_items = {}

            if user_session and user_session.cart_items:
                merged_cart_items.update(user_session.cart_items)

            if guest_session.cart_items:
                for item_key, guest_item in guest_session.cart_items.items():
                    if item_key in merged_cart_items:
                        merged_cart_items[item_key]['quantity'] += guest_item['quantity']
                    else:
                        merged_cart_items[item_key] = guest_item

            session_data = {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None,
                'ip_address': guest_session.ip_address,
                'user_agent': guest_session.user_agent,
                'cart_items': merged_cart_items
            }

            new_session = self.create_session(session_data)
            self.delete_session(guest_session_id)
            if user_session:
                self.delete_session(user_session.session_id)

            logger.info(f"Successfully migrated guest session {guest_session_id} to user {user_id}")
            return new_session

        except Exception as e:
            logger.error(f"Failed to migrate guest session to user: {e}")
            return None

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        try:
            if not self._check_rate_limit(f"update:{session_id}"):
                return False
            session = self.get_session(session_id)
            if not session:
                return False
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.last_activity = datetime.utcnow()
            session_dict = session.model_dump()
            session_dict['session_type'] = session_dict['session_type'].value
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()
            key = self._session_key(session_id)
            expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration
            success = redis_client.setex(key, expiry, json.dumps(session_dict))
            if success and 'user_id' in updates:
                if session.user_id:
                    mapping_key = f"{self._redis_user_session_prefix}{session.user_id}:{session_id}"
                    redis_client.setex(mapping_key, self.user_session_duration, session_id)
            if success and 'guest_id' in updates:
                if session.guest_id:
                    mapping_key = f"{self._redis_guest_session_prefix}{session.guest_id}:{session_id}"
                    redis_client.setex(mapping_key, self.guest_session_duration, session_id)
            return success
        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            redis_client.delete(self._session_key(session_id))
            if session.user_id:
                # Delete all session mappings for this user
                pattern = f"{self._redis_user_session_prefix}{session.user_id}:*"
                mapping_keys = redis_client.redis_client.keys(pattern)
                if mapping_keys:
                    redis_client.redis_client.delete(*mapping_keys)
            if session.guest_id:
                # Delete all session mappings for this guest
                pattern = f"{self._redis_guest_session_prefix}{session.guest_id}:*"
                mapping_keys = redis_client.redis_client.keys(pattern)
                if mapping_keys:
                    redis_client.redis_client.delete(*mapping_keys)

            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        try:
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.redis_client.keys(pattern)
            if not mapping_keys:
                return None
            latest_session = None
            for key in mapping_keys:
                session_id = redis_client.get(key)
                if session_id:
                    session = self.get_session(session_id)
                    if session and (not latest_session or session.created_at > latest_session.created_at):
                        latest_session = session

            return latest_session
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None

    def validate_and_repair_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            repairs_made = False
            if session.cart_items is None:
                session.cart_items = {}
                repairs_made = True
                logger.info(f"Repaired session {session_id}: cart_items was None")

            if session.session_type not in [SessionType.GUEST, SessionType.USER]:
                session.session_type = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: invalid session_type")

            if session.session_type == SessionType.USER and not session.user_id:
                session.session_type = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: user session without user_id")

            if session.session_type == SessionType.GUEST and not session.guest_id:
                session.guest_id = str(uuid.uuid4())
                repairs_made = True
                logger.info(f"Repaired session {session_id}: guest session without guest_id")

            if repairs_made:
                session_dict = session.model_dump()
                session_dict['session_type'] = session_dict['session_type'].value
                session_dict['created_at'] = session_dict['created_at'].isoformat()
                session_dict['last_activity'] = session_dict['last_activity'].isoformat()
                session_dict['expires_at'] = session_dict['expires_at'].isoformat()

                expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration
                key = self._session_key(session_id)

                success = redis_client.setex(
                    key,
                    expiry,
                    json.dumps(session_dict)
                )

                if success:
                    logger.info(f"Successfully repaired session {session_id}")
                else:
                    logger.error(f"Failed to save repaired session {session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to validate/repair session {session_id}: {e}")
            return False

    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user (useful for password changes, etc.)"""
        try:
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.redis_client.keys(pattern)

            sessions_invalidated = 0
            for key in mapping_keys:
                session_id = redis_client.get(key)
                if session_id and self.delete_session(session_id):
                    sessions_invalidated += 1

            logger.info(f"Invalidated {sessions_invalidated} sessions for user {user_id}")
            return sessions_invalidated > 0
        except Exception as e:
            logger.error(f"Failed to invalidate all sessions for user {user_id}: {e}")
            return False


session_service = SessionService()