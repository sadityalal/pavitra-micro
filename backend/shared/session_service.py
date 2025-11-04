import uuid
import json
import time
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from shared import get_logger, db
from .redis_client import redis_client
from .session_models import SessionData, SessionType

logger = get_logger(__name__)


class SessionService:
    def __init__(self):
        self.inactivity_timeout = 1200
        self.guest_session_duration = 86400
        self.user_session_duration = 86400
        self._redis_session_prefix = "session:"
        self._redis_user_session_prefix = "user_session:"
        self._redis_guest_session_prefix = "guest_session:"
        self._rate_limit_prefix = "session_rate_limit:"
        self.max_sessions_per_user = 5
        self.session_rotation_interval = 3600
        self.rate_limit_attempts = 100
        self.rate_limit_window = 60

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def _rate_limit_key(self, identifier: str) -> str:
        return f"{self._rate_limit_prefix}{identifier}"

    def _user_session_mapping_key(self, user_id: int, session_id: str) -> str:
        return f"{self._redis_user_session_prefix}{user_id}:{session_id}"

    def _guest_session_mapping_key(self, guest_id: str, session_id: str) -> str:
        return f"{self._redis_guest_session_prefix}{guest_id}:{session_id}"

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
            return True

    def _cleanup_old_user_sessions(self, user_id: int):
        try:
            user_sessions = []
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.keys(pattern)
            for key in mapping_keys:
                try:
                    session_id = redis_client.get(key)
                    if session_id:
                        session = self.get_session(session_id)
                        if session:
                            user_sessions.append((session_id, session.created_at))
                except Exception as e:
                    logger.debug(f"Error processing session mapping {key}: {e}")
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
            if not redis_client.ping():
                logger.error("Redis is not connected - cannot create session")
                return None

            client_ip = session_data.get('ip_address', 'unknown')

            if not self._check_rate_limit(f"create:{client_ip}"):
                logger.warning(f"Rate limit exceeded for session creation from IP: {client_ip}")
                return None

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

            session_dict = {
                'session_id': session_id,
                'session_type': session.session_type.value,
                'user_id': session.user_id,
                'guest_id': session.guest_id,
                'cart_items': session.cart_items,
                'created_at': session.created_at.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'expires_at': session.expires_at.isoformat(),
                'ip_address': session.ip_address,
                'user_agent': session.user_agent
            }

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

            # Store session mappings
            if session.user_id:
                mapping_key = self._user_session_mapping_key(session.user_id, session_id)
                redis_client.setex(mapping_key, self.user_session_duration, session_id)
            elif session.guest_id:
                mapping_key = self._guest_session_mapping_key(session.guest_id, session_id)
                redis_client.setex(mapping_key, self.guest_session_duration, session_id)

            logger.info(f"Created {session.session_type.value} session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}", exc_info=True)
            return None

    def get_session(self, session_id: str, request_ip: str = None, request_user_agent: str = None) -> Optional[
        SessionData]:
        try:
            if not session_id:
                return None

            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                logger.debug(f"Session not found in Redis: {session_id}")
                return None

            session_dict = json.loads(data)

            # Check if session is expired
            expires_at_str = session_dict.get('expires_at')
            if not expires_at_str:
                logger.debug(f"Session missing expires_at: {session_id}")
                return None

            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if datetime.utcnow() > expires_at:
                logger.debug(f"Session expired: {session_id}")
                self.delete_session(session_id)
                return None

            # Parse datetime strings
            def parse_iso_datetime(dt_str):
                if not dt_str:
                    return datetime.utcnow()
                dt_str = str(dt_str).replace('Z', '+00:00')
                try:
                    return datetime.fromisoformat(dt_str)
                except ValueError:
                    try:
                        return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%f')
                    except ValueError:
                        try:
                            return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S')
                        except ValueError:
                            logger.warning(f"Failed to parse datetime: {dt_str}, using current time")
                            return datetime.utcnow()

            session_dict['created_at'] = parse_iso_datetime(session_dict.get('created_at'))
            session_dict['last_activity'] = parse_iso_datetime(session_dict.get('last_activity'))
            session_dict['expires_at'] = parse_iso_datetime(session_dict.get('expires_at'))

            # Convert session_type string to enum
            session_type_str = session_dict.get('session_type', 'guest')
            session_dict['session_type'] = SessionType.USER if session_type_str == 'user' else SessionType.GUEST

            # Ensure cart_items is a dict
            if session_dict.get('cart_items') is None:
                session_dict['cart_items'] = {}

            # Create SessionData object
            session = SessionData(**session_dict)

            # Validate session origin if provided
            if request_ip and request_user_agent:
                if not self.validate_session_origin(session, request_ip, request_user_agent):
                    logger.warning(f"Session origin validation failed for {session_id}")
                    return None

            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}", exc_info=True)
            return None

    def validate_session_origin(self, session: SessionData, request_ip: str, request_user_agent: str) -> bool:
        try:
            # Allow sessions from same IP (relaxed validation for shared sessions)
            if session.ip_address and session.ip_address != request_ip:
                logger.debug(
                    f"Session IP mismatch: {session.ip_address} vs {request_ip} - allowing for shared sessions")
            return True
        except Exception as e:
            logger.error(f"Session origin validation failed: {e}")
            return True

    def update_session_activity(self, session_id: str) -> bool:
        """Update session activity without causing recursion"""
        try:
            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                return False

            session_dict = json.loads(data)

            # Update last_activity directly in the dict
            session_dict['last_activity'] = datetime.utcnow().isoformat()

            # Determine expiry based on session type
            session_type_str = session_dict.get('session_type', 'guest')
            expiry_seconds = self.user_session_duration if session_type_str == 'user' else self.guest_session_duration

            # Save updated session data
            success = redis_client.setex(
                key,
                expiry_seconds,
                json.dumps(session_dict)
            )

            return success

        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False

    def migrate_guest_to_user_session(self, guest_session_id: str, user_id: int) -> Optional[SessionData]:
        try:
            guest_session = self.get_session(guest_session_id)
            if not guest_session or guest_session.session_type != SessionType.GUEST:
                return None

            # Update existing session to user type
            return self.update_session_data(guest_session_id, {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None
            })

        except Exception as e:
            logger.error(f"Failed to migrate guest session to user: {e}")
            return None

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> Optional[SessionData]:
        try:
            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                return None

            session_dict = json.loads(data)

            # Apply updates
            for key, value in updates.items():
                if key in ['session_type', 'user_id', 'guest_id', 'cart_items']:
                    if key == 'session_type' and isinstance(value, SessionType):
                        session_dict[key] = value.value
                    else:
                        session_dict[key] = value

            # Update last_activity
            session_dict['last_activity'] = datetime.utcnow().isoformat()

            # Determine expiry
            session_type_str = session_dict.get('session_type', 'guest')
            expiry_seconds = self.user_session_duration if session_type_str == 'user' else self.guest_session_duration

            # Save updated session
            success = redis_client.setex(key, expiry_seconds, json.dumps(session_dict))

            if not success:
                return None

            # Update mappings if user_id or guest_id changed
            if 'user_id' in updates:
                user_id = updates['user_id']
                if user_id:
                    mapping_key = self._user_session_mapping_key(user_id, session_id)
                    redis_client.setex(mapping_key, self.user_session_duration, session_id)

            if 'guest_id' in updates:
                guest_id = updates['guest_id']
                if guest_id:
                    mapping_key = self._guest_session_mapping_key(guest_id, session_id)
                    redis_client.setex(mapping_key, self.guest_session_duration, session_id)

            # Return updated session
            return self.get_session(session_id)

        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        try:
            # Get session data first to check user_id and guest_id
            session = self.get_session(session_id)

            # Delete main session
            redis_client.delete(self._session_key(session_id))

            # Delete mappings if we have session data
            if session:
                if session.user_id:
                    pattern = f"{self._redis_user_session_prefix}{session.user_id}:*"
                    mapping_keys = redis_client.keys(pattern)
                    if mapping_keys:
                        redis_client.delete(*mapping_keys)

                if session.guest_id:
                    pattern = f"{self._redis_guest_session_prefix}{session.guest_id}:*"
                    mapping_keys = redis_client.keys(pattern)
                    if mapping_keys:
                        redis_client.delete(*mapping_keys)

            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        try:
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.keys(pattern)
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
        """Validate and repair session data if needed"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            repairs_made = False
            updates = {}

            if session.cart_items is None:
                updates['cart_items'] = {}
                repairs_made = True
                logger.info(f"Repaired session {session_id}: cart_items was None")

            if session.session_type not in [SessionType.GUEST, SessionType.USER]:
                updates['session_type'] = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: invalid session_type")

            if session.session_type == SessionType.USER and not session.user_id:
                updates['session_type'] = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: user session without user_id")

            if session.session_type == SessionType.GUEST and not session.guest_id:
                updates['guest_id'] = str(uuid.uuid4())
                repairs_made = True
                logger.info(f"Repaired session {session_id}: guest session without guest_id")

            if repairs_made:
                success = self.update_session_data(session_id, updates)
                if success:
                    logger.info(f"Successfully repaired session {session_id}")
                    return True
                else:
                    logger.error(f"Failed to save repaired session {session_id}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate/repair session {session_id}: {e}")
            return False

    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        try:
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.keys(pattern)
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