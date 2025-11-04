import uuid
import json
import time
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from shared import get_logger, db, config
from .redis_client import redis_client
from .session_models import SessionData, SessionType
import ipaddress
import re

logger = get_logger(__name__)


class SecureSessionService:
    def __init__(self):
        # Load all configuration from database
        self.session_config = config.get_session_config()
        self._load_configuration()

        # Redis key prefixes
        self._redis_session_prefix = "secure_session:"
        self._redis_user_session_prefix = "secure_user_session:"
        self._redis_guest_session_prefix = "secure_guest_session:"
        self._redis_rate_limit_prefix = "secure_rate_limit:"
        self._redis_failed_attempts_prefix = "secure_failed_attempts:"

        # Security tokens
        self._security_token_secret = config.jwt_secret.encode()

    def _load_configuration(self):
        """Load all configuration from database session_settings"""
        try:
            # Session timeouts
            self.inactivity_timeout = self.session_config['inactivity_timeout']
            self.guest_session_duration = self.session_config['guest_session_duration']
            self.user_session_duration = self.session_config['user_session_duration']
            self.max_session_age = self.session_config['max_session_age']

            # Session limits
            self.max_sessions_per_user = self.session_config['max_sessions_per_user']
            self.session_rotation_interval = self.session_config['session_rotation_interval']
            self.session_cleanup_interval = self.session_config['session_cleanup_interval']

            # Rate limiting
            self.rate_limit_attempts = self.session_config['session_rate_limit_attempts']
            self.rate_limit_window = self.session_config['session_rate_limit_window']
            self.rate_limit_attempts_create = self.session_config['rate_limit_session_create']
            self.rate_limit_attempts_access = self.session_config['rate_limit_session_access']
            self.rate_limit_attempts_update = self.session_config['rate_limit_session_update']
            self.rate_limit_attempts_delete = self.session_config['rate_limit_session_delete']

            # Security features
            self.enable_csrf_protection = self.session_config['enable_csrf_protection']
            self.enable_ip_validation = self.session_config['enable_ip_validation']
            self.enable_user_agent_validation = self.session_config['enable_user_agent_validation']
            self.enable_session_rotation = self.session_config['enable_session_rotation']
            self.require_security_token = self.session_config['require_security_token']
            self.enable_session_fingerprinting = self.session_config['enable_session_fingerprinting']

            # Failed attempts tracking
            self.max_failed_attempts = self.session_config['max_failed_attempts']
            self.failed_attempts_window = self.session_config['failed_attempts_window']

            logger.info("Session configuration loaded from database")

        except Exception as e:
            logger.error(f"Failed to load session configuration: {e}")
            # Fallback to safe defaults
            self._set_fallback_config()

    def _set_fallback_config(self):
        """Set fallback configuration if database loading fails"""
        self.inactivity_timeout = 1800
        self.guest_session_duration = 86400
        self.user_session_duration = 2592000
        self.max_session_age = 604800
        self.max_sessions_per_user = 5
        self.session_rotation_interval = 3600
        self.session_cleanup_interval = 86400
        self.rate_limit_attempts = 10
        self.rate_limit_window = 60
        self.enable_csrf_protection = True
        self.enable_ip_validation = True
        self.enable_user_agent_validation = True
        self.enable_session_rotation = True
        self.require_security_token = True
        self.enable_session_fingerprinting = True
        self.max_failed_attempts = 5
        self.failed_attempts_window = 900

    def refresh_configuration(self):
        """Refresh configuration from database"""
        try:
            config.refresh_session_config()
            self.session_config = config.get_session_config()
            self._load_configuration()
            logger.info("Session configuration refreshed from database")
        except Exception as e:
            logger.error(f"Failed to refresh session configuration: {e}")

    def _generate_secure_id(self) -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)

    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_urlsafe(16)

    def _generate_security_token(self, session_id: str, ip_address: str) -> str:
        """Generate security token for session validation"""
        data = f"{session_id}:{ip_address}:{int(time.time())}"
        return hmac.new(
            self._security_token_secret,
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    def _validate_security_token(self, session_id: str, ip_address: str, token: str) -> bool:
        """Validate security token"""
        expected_token = self._generate_security_token(session_id, ip_address)
        return hmac.compare_digest(expected_token, token)

    def _calculate_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """Calculate session fingerprint for additional security"""
        data = f"{user_agent}:{ipaddress.ip_address(ip_address).packed.hex()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def _rate_limit_key(self, identifier: str) -> str:
        return f"{self._redis_rate_limit_prefix}{identifier}"

    def _failed_attempts_key(self, identifier: str) -> str:
        return f"{self._redis_failed_attempts_prefix}{identifier}"

    def _check_rate_limit(self, identifier: str, operation: str) -> bool:
        """Enhanced rate limiting with operation-specific limits from database"""
        try:
            current_time = int(time.time())
            window_start = current_time // self.rate_limit_window

            # Get limits from configuration
            limits = {
                "create": self.rate_limit_attempts_create,
                "access": self.rate_limit_attempts_access,
                "update": self.rate_limit_attempts_update,
                "delete": self.rate_limit_attempts_delete
            }

            limit = limits.get(operation, self.rate_limit_attempts)
            rate_key = f"{self._rate_limit_key(identifier)}:{operation}:{window_start}"

            current_attempts = redis_client.incr(rate_key)
            if current_attempts == 1:
                redis_client.expire(rate_key, self.rate_limit_window)

            if current_attempts > limit:
                logger.warning(f"Rate limit exceeded for {operation}: {identifier}")
                return False
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True

    def _check_failed_attempts(self, identifier: str) -> bool:
        """Check if too many failed attempts"""
        try:
            fail_key = self._failed_attempts_key(identifier)
            failures = redis_client.get(fail_key)
            if failures and int(failures) >= self.max_failed_attempts:
                logger.warning(f"Too many failed attempts for: {identifier}")
                return False
            return True
        except Exception as e:
            logger.error(f"Failed attempts check failed: {e}")
            return True

    def _record_failed_attempt(self, identifier: str):
        """Record failed attempt"""
        try:
            fail_key = self._failed_attempts_key(identifier)
            current_failures = redis_client.incr(fail_key)
            if current_failures == 1:
                redis_client.expire(fail_key, self.failed_attempts_window)
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")

    def _cleanup_old_user_sessions(self, user_id: int):
        """Clean up old sessions for user"""
        try:
            user_sessions = []
            all_keys = redis_client.keys(f"{self._redis_session_prefix}*")

            for key in all_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        if session_data.get('user_id') == user_id:
                            session_id = key.replace(self._redis_session_prefix, "")
                            created_at = datetime.fromisoformat(session_data['created_at'])
                            user_sessions.append((session_id, created_at))
                except Exception:
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
        """Create a new secure session using database configuration"""
        try:
            client_ip = session_data.get('ip_address', 'unknown')

            # Security checks
            if not self._check_rate_limit(f"create:{client_ip}", "create"):
                return None

            if not self._check_failed_attempts(f"create:{client_ip}"):
                return None

            # Generate secure session ID
            session_id = self._generate_secure_id()
            now = datetime.utcnow()

            # Determine session type and expiration using database configuration
            if session_data.get('session_type') == SessionType.USER:
                expires_at = now + timedelta(seconds=self.user_session_duration)
                user_id = session_data.get('user_id')
                if user_id:
                    self._cleanup_old_user_sessions(user_id)
            else:
                expires_at = now + timedelta(seconds=self.guest_session_duration)

            # Generate security tokens if enabled
            security_token = None
            if self.require_security_token:
                security_token = self._generate_security_token(session_id, client_ip)

            csrf_token = None
            if self.enable_csrf_protection:
                csrf_token = self._generate_csrf_token()

            fingerprint = None
            if self.enable_session_fingerprinting:
                fingerprint = self._calculate_fingerprint(
                    session_data.get('user_agent', ''),
                    client_ip
                )

            # Create session object
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
                ip_address=client_ip,
                user_agent=session_data.get('user_agent'),
                expires_at=expires_at,
                security_token=security_token,
                csrf_token=csrf_token,
                fingerprint=fingerprint
            )

            # Store in Redis
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

            # Store mappings for user/guest
            if session.user_id:
                mapping_key = f"{self._redis_user_session_prefix}{session.user_id}:{session_id}"
                redis_client.setex(mapping_key, self.user_session_duration, session_id)
            elif session.guest_id:
                mapping_key = f"{self._redis_guest_session_prefix}{session.guest_id}:{session_id}"
                redis_client.setex(mapping_key, self.guest_session_duration, session_id)

            logger.info(f"Created secure {session.session_type.value} session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create secure session: {e}")
            self._record_failed_attempt(f"create:{session_data.get('ip_address', 'unknown')}")
            return None

    def get_session(self, session_id: str, request_ip: str = None, request_user_agent: str = None,
                    security_token: str = None) -> Optional[SessionData]:
        """Retrieve and validate session with security checks using database configuration"""
        try:
            # Security checks
            if not self._check_rate_limit(f"access:{session_id}", "access"):
                return None

            if not self._check_failed_attempts(f"access:{session_id}"):
                return None

            if not session_id or len(session_id) < 32:
                logger.warning("Invalid session ID format")
                return None

            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                logger.warning(f"Session not found: {session_id}")
                return None

            # Parse session data
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

            # Security validations using database configuration
            if not self._validate_session_security(session, request_ip, request_user_agent, security_token):
                logger.warning(f"Session security validation failed: {session_id}")
                self._record_failed_attempt(f"access:{session_id}")
                return None

            # Check if session needs rotation
            if self.enable_session_rotation and self._should_rotate_session(session):
                logger.info(f"Rotating session for security: {session_id}")
                return self.rotate_session(session_id)

            # Update activity
            self._update_session_activity_only(session_id)

            return session

        except Exception as e:
            logger.error(f"Failed to get secure session {session_id}: {e}")
            self._record_failed_attempt(f"access:{session_id}")
            return None

    def _validate_session_security(self, session: SessionData, request_ip: str, request_user_agent: str,
                                   security_token: str) -> bool:
        """Comprehensive session security validation using database configuration"""
        try:
            # Check expiration
            if datetime.utcnow() > session.expires_at:
                logger.warning("Session expired")
                return False

            # Validate security token if enabled
            if self.require_security_token and security_token:
                if not self._validate_security_token(session.session_id, request_ip, security_token):
                    logger.warning("Invalid security token")
                    return False

            # IP address validation if enabled
            if self.enable_ip_validation and session.ip_address and request_ip and session.ip_address != request_ip:
                try:
                    session_ip = ipaddress.ip_address(session.ip_address)
                    request_ip_obj = ipaddress.ip_address(request_ip)

                    # For IPv4, check first two octets match
                    if session_ip.version == 4 and request_ip_obj.version == 4:
                        session_parts = str(session_ip).split('.')[:2]
                        request_parts = str(request_ip_obj).split('.')[:2]
                        if session_parts != request_parts:
                            logger.warning(f"IP network mismatch: {session.ip_address} vs {request_ip}")
                            return False
                except ValueError:
                    logger.warning("Invalid IP address format")
                    return False

            # User agent fingerprint validation if enabled
            if self.enable_user_agent_validation and request_user_agent and session.fingerprint:
                expected_fingerprint = self._calculate_fingerprint(request_user_agent, request_ip)
                if session.fingerprint != expected_fingerprint:
                    logger.warning("User agent fingerprint mismatch")
                    # Don't block entirely for user agent changes, but log it
                    logger.info(f"User agent changed for session {session.session_id}")

            return True

        except Exception as e:
            logger.error(f"Session security validation failed: {e}")
            return False

    def _should_rotate_session(self, session: SessionData) -> bool:
        """Check if session should be rotated for security"""
        try:
            session_age = datetime.utcnow() - session.created_at
            return session_age.total_seconds() > self.session_rotation_interval
        except Exception as e:
            logger.error(f"Failed to check session rotation: {e}")
            return False

    def rotate_session(self, old_session_id: str) -> Optional[SessionData]:
        """Rotate session ID for security"""
        try:
            if not self._check_rate_limit(f"rotate:{old_session_id}", "update"):
                return None

            old_session = self.get_session(old_session_id)
            if not old_session:
                return None

            # Create new session with same data
            new_session_data = {
                'session_type': old_session.session_type,
                'user_id': old_session.user_id,
                'guest_id': old_session.guest_id,
                'cart_items': old_session.cart_items,
                'ip_address': old_session.ip_address,
                'user_agent': old_session.user_agent
            }

            new_session = self.create_session(new_session_data)
            if new_session:
                self.delete_session(old_session_id)
                logger.info(f"Successfully rotated session {old_session_id} -> {new_session.session_id}")
            return new_session

        except Exception as e:
            logger.error(f"Failed to rotate session {old_session_id}: {e}")
            return None

    def _update_session_activity_only(self, session_id: str) -> bool:
        """Update session activity timestamp"""
        try:
            if not self._check_rate_limit(f"activity:{session_id}", "update"):
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
        """Public method to update session activity"""
        return self._update_session_activity_only(session_id)

    def migrate_guest_to_user_session(self, guest_session_id: str, user_id: int) -> Optional[SessionData]:
        """Migrate guest session to user session with security checks"""
        try:
            if not self._check_rate_limit(f"migrate:{user_id}", "update"):
                return None

            guest_session = self.get_session(guest_session_id)
            if not guest_session or guest_session.session_type != SessionType.GUEST:
                return None

            # Get existing user session if any
            user_session = self.get_session_by_user_id(user_id)

            # Merge cart items
            merged_cart_items = {}
            if user_session and user_session.cart_items:
                merged_cart_items.update(user_session.cart_items)
            if guest_session.cart_items:
                for item_key, guest_item in guest_session.cart_items.items():
                    if item_key in merged_cart_items:
                        merged_cart_items[item_key]['quantity'] += guest_item['quantity']
                    else:
                        merged_cart_items[item_key] = guest_item

            # Create new user session
            session_data = {
                'session_type': SessionType.USER,
                'user_id': user_id,
                'guest_id': None,
                'ip_address': guest_session.ip_address,
                'user_agent': guest_session.user_agent,
                'cart_items': merged_cart_items
            }

            new_session = self.create_session(session_data)

            # Clean up old sessions
            self.delete_session(guest_session_id)
            if user_session:
                self.delete_session(user_session.session_id)

            logger.info(f"Successfully migrated guest session {guest_session_id} to user {user_id}")
            return new_session

        except Exception as e:
            logger.error(f"Failed to migrate guest session to user: {e}")
            return None

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data with security validation"""
        try:
            if not self._check_rate_limit(f"update:{session_id}", "update"):
                return False

            session = self.get_session(session_id)
            if not session:
                return False

            # Validate updates
            allowed_updates = {'cart_items', 'user_agent'}
            for key in updates:
                if key not in allowed_updates:
                    logger.warning(f"Attempt to update restricted session field: {key}")
                    return False

            # Apply updates
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
            return success

        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Delete session with security checks"""
        try:
            if not self._check_rate_limit(f"delete:{session_id}", "delete"):
                return False

            session = self.get_session(session_id)
            if not session:
                return False

            # Delete session and mappings
            redis_client.delete(self._session_key(session_id))

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

            logger.info(f"Deleted secure session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        """Get latest session for user"""
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
        """Validate and repair session data"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            repairs_made = False

            # Fix common issues
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

            # Save repairs
            if repairs_made:
                session_dict = session.model_dump()
                session_dict['session_type'] = session_dict['session_type'].value
                session_dict['created_at'] = session_dict['created_at'].isoformat()
                session_dict['last_activity'] = session_dict['last_activity'].isoformat()
                session_dict['expires_at'] = session_dict['expires_at'].isoformat()

                expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration
                key = self._session_key(session_id)

                success = redis_client.setex(key, expiry, json.dumps(session_dict))
                if success:
                    logger.info(f"Successfully repaired secure session {session_id}")
                else:
                    logger.error(f"Failed to save repaired secure session {session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to validate/repair secure session {session_id}: {e}")
            return False

    def invalidate_all_user_sessions(self, user_id: int) -> bool:
        """Invalidate all sessions for a user"""
        try:
            pattern = f"{self._redis_user_session_prefix}{user_id}:*"
            mapping_keys = redis_client.keys(pattern)
            sessions_invalidated = 0

            for key in mapping_keys:
                session_id = redis_client.get(key)
                if session_id and self.delete_session(session_id):
                    sessions_invalidated += 1

            logger.info(f"Invalidated {sessions_invalidated} secure sessions for user {user_id}")
            return sessions_invalidated > 0

        except Exception as e:
            logger.error(f"Failed to invalidate all secure sessions for user {user_id}: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (for cron job)"""
        try:
            pattern = f"{self._redis_session_prefix}*"
            all_keys = redis_client.keys(pattern)
            cleaned_count = 0

            for key in all_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        session_data = json.loads(data)
                        expires_at = datetime.fromisoformat(session_data['expires_at'])
                        if datetime.utcnow() > expires_at:
                            session_id = key.replace(self._redis_session_prefix, "")
                            if self.delete_session(session_id):
                                cleaned_count += 1
                except Exception as e:
                    logger.error(f"Error cleaning up session {key}: {e}")
                    continue

            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            return cleaned_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0


# Global instance
session_service = SecureSessionService()