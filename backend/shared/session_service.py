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
        self.session_config = config.get_session_config()
        self._load_configuration()
        self._redis_session_prefix = "secure_session:"
        self._redis_user_session_prefix = "secure_user_session:"
        self._redis_guest_session_prefix = "secure_guest_session:"
        self._redis_rate_limit_prefix = "secure_rate_limit:"
        self._redis_failed_attempts_prefix = "secure_failed_attempts:"
        self._redis_user_primary_session = "user_primary_session:"
        self._security_token_secret = config.jwt_secret.encode()

    def _load_configuration(self):
        try:
            self.inactivity_timeout = self.session_config['inactivity_timeout']
            self.guest_session_duration = self.session_config['guest_session_duration']
            self.user_session_duration = self.session_config['user_session_duration']
            self.max_session_age = self.session_config['max_session_age']
            self.max_sessions_per_user = self.session_config['max_sessions_per_user']
            self.session_rotation_interval = self.session_config['session_rotation_interval']
            self.session_cleanup_interval = self.session_config['session_cleanup_interval']
            self.rate_limit_attempts = self.session_config['session_rate_limit_attempts']
            self.rate_limit_window = self.session_config['session_rate_limit_window']
            self.rate_limit_attempts_create = self.session_config['rate_limit_session_create']
            self.rate_limit_attempts_access = self.session_config['rate_limit_session_access']
            self.rate_limit_attempts_update = self.session_config['rate_limit_session_update']
            self.rate_limit_attempts_delete = self.session_config['rate_limit_session_delete']
            self.enable_csrf_protection = self.session_config['enable_csrf_protection']
            self.enable_ip_validation = self.session_config['enable_ip_validation']
            self.enable_user_agent_validation = self.session_config['enable_user_agent_validation']
            self.enable_session_rotation = self.session_config['enable_session_rotation']
            self.require_security_token = self.session_config['require_security_token']
            self.enable_session_fingerprinting = self.session_config['enable_session_fingerprinting']
            self.max_failed_attempts = self.session_config['max_failed_attempts']
            self.failed_attempts_window = self.session_config['failed_attempts_window']
            logger.info("Session configuration loaded from database")
        except Exception as e:
            logger.error(f"Failed to load session configuration: {e}")
            self._set_fallback_config()

    def _set_fallback_config(self):
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
        try:
            config.refresh_session_config()
            self.session_config = config.get_session_config()
            self._load_configuration()
            logger.info("Session configuration refreshed from database")
        except Exception as e:
            logger.error(f"Failed to refresh session configuration: {e}")

    def _generate_secure_id(self) -> str:
        return secrets.token_urlsafe(32)

    def _generate_csrf_token(self) -> str:
        return secrets.token_urlsafe(16)

    def _generate_security_token(self, session_id: str, ip_address: str) -> str:
        data = f"{session_id}:{ip_address}:{int(time.time())}"
        return hmac.new(
            self._security_token_secret,
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    def _validate_security_token(self, session_id: str, ip_address: str, token: str) -> bool:
        expected_token = self._generate_security_token(session_id, ip_address)
        return hmac.compare_digest(expected_token, token)

    def _calculate_fingerprint(self, user_agent: str, ip_address: str) -> str:
        data = f"{user_agent}:{ipaddress.ip_address(ip_address).packed.hex()}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def _rate_limit_key(self, identifier: str) -> str:
        return f"{self._redis_rate_limit_prefix}{identifier}"

    def _failed_attempts_key(self, identifier: str) -> str:
        return f"{self._redis_failed_attempts_prefix}{identifier}"

    def _check_rate_limit(self, identifier: str, operation: str) -> bool:
        try:
            if operation == "create":
                return True
            if not redis_client._ensure_connection():
                return True
            current_time = int(time.time())
            window_start = current_time // self.rate_limit_window
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
        try:
            if not redis_client._ensure_connection():
                return True
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
        try:
            if redis_client._ensure_connection():
                fail_key = self._failed_attempts_key(identifier)
                current_failures = redis_client.incr(fail_key)
                if current_failures == 1:
                    redis_client.expire(fail_key, self.failed_attempts_window)
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")

    def _cleanup_old_user_sessions(self, user_id: int):
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

    def get_or_create_user_session(self, user_id: int, ip_address: str, user_agent: str) -> Optional[SessionData]:
        """Get existing user session or create new one - ONE SESSION PER USER"""
        try:
            # First, try to get existing session for this user
            existing_session = self.get_session_by_user_id(user_id)

            if existing_session:
                logger.info(f"✅ Using existing session for user {user_id}: {existing_session.session_id}")

                # Update IP addresses list if this is a new IP
                if ip_address and ip_address not in existing_session.ip_addresses:
                    existing_session.ip_addresses.append(ip_address)
                    self._update_session_data(existing_session.session_id, {
                        'ip_addresses': existing_session.ip_addresses,
                        'ip_address': ip_address,  # Update current IP
                        'user_agent': user_agent
                    })

                # Update activity
                self.update_session_activity(existing_session.session_id)
                return existing_session
            else:
                # Create new session for user
                logger.info(f"🆕 Creating new session for user {user_id}")
                session_data = {
                    'session_type': SessionType.USER,
                    'user_id': user_id,
                    'guest_id': None,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'cart_items': {},
                    'ip_addresses': [ip_address] if ip_address else []
                }
                return self.create_session(session_data)

        except Exception as e:
            logger.error(f"Failed to get or create user session: {e}")
            return None

    # In backend/shared/session_service.py

    def get_or_create_guest_session(self, guest_id: str, ip_address: str, user_agent: str) -> Optional[SessionData]:
        try:
            # First try to get session by guest_id
            existing_session = self.get_session_by_guest_id(guest_id)
            if existing_session:
                logger.info(f"✅ Using existing guest session: {existing_session.session_id}")
                # Update activity and IP info
                if ip_address and ip_address not in existing_session.ip_addresses:
                    existing_session.ip_addresses.append(ip_address)
                    self._update_session_data(existing_session.session_id, {
                        'ip_addresses': existing_session.ip_addresses,
                        'ip_address': ip_address,
                        'user_agent': user_agent
                    })
                self.update_session_activity(existing_session.session_id)
                return existing_session

            # If no session by guest_id, try to find by IP/user_agent
            existing_by_ip = self.find_guest_session_by_ip(ip_address, user_agent)
            if existing_by_ip:
                logger.info(f"🔍 Found guest session by IP: {existing_by_ip.session_id}")
                # Update guest_id to maintain consistency
                self._update_session_data(existing_by_ip.session_id, {
                    'guest_id': guest_id
                })
                self.update_session_activity(existing_by_ip.session_id)
                return existing_by_ip

            # Create new guest session
            logger.info(f"🆕 Creating new guest session for guest_id: {guest_id}")
            session_data = {
                'session_type': SessionType.GUEST,
                'user_id': None,
                'guest_id': guest_id,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'cart_items': {},
                'ip_addresses': [ip_address] if ip_address else []
            }
            return self.create_session(session_data)

        except Exception as e:
            logger.error(f"Failed to get or create guest session: {e}")
            # Emergency fallback
            return self._create_emergency_session(guest_id, ip_address, user_agent)

    def create_session(self, session_data: Dict[str, Any]) -> Optional[SessionData]:
        try:
            session_id = self._generate_secure_id()
            now = datetime.utcnow()

            if session_data.get('session_type') == SessionType.USER:
                expires_at = now + timedelta(seconds=self.user_session_duration)
                user_id = session_data.get('user_id')
                if user_id:
                    self._cleanup_old_user_sessions(user_id)
            else:
                expires_at = now + timedelta(seconds=self.guest_session_duration)

            # ENSURE CART_ITEMS IS PROPERLY INITIALIZED - FIX FOR GUEST CART
            cart_items = session_data.get('cart_items', {})
            if cart_items is None:
                cart_items = {}
            elif not isinstance(cart_items, dict):
                logger.warning(f"Cart items is not a dict, converting: {type(cart_items)}")
                cart_items = {}

            security_token = None
            if self.require_security_token and session_data.get('ip_address'):
                security_token = self._generate_security_token(session_id, session_data.get('ip_address', 'unknown'))

            csrf_token = None
            if self.enable_csrf_protection:
                csrf_token = self._generate_csrf_token()

            fingerprint = None
            if self.enable_session_fingerprinting and session_data.get('user_agent') and session_data.get('ip_address'):
                fingerprint = self._calculate_fingerprint(
                    session_data.get('user_agent', ''),
                    session_data.get('ip_address', 'unknown')
                )

            ip_addresses = session_data.get('ip_addresses', [])
            current_ip = session_data.get('ip_address')
            if current_ip and current_ip not in ip_addresses:
                ip_addresses.append(current_ip)

            session = SessionData(
                session_id=session_id,
                session_type=session_data['session_type'],
                user_id=session_data.get('user_id'),
                guest_id=session_data.get('guest_id', str(uuid.uuid4())),
                cart_items=cart_items,  # USE THE ENSURED CART_ITEMS
                created_at=now,
                last_activity=now,
                ip_address=session_data.get('ip_address', 'unknown'),
                user_agent=session_data.get('user_agent', ''),
                expires_at=expires_at,
                security_token=security_token,
                csrf_token=csrf_token,
                fingerprint=fingerprint,
                ip_addresses=ip_addresses
            )

            session_dict = session.model_dump()
            session_dict['session_type'] = session_dict['session_type'].value
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            # ENSURE CART_ITEMS IS SAVED PROPERLY
            if session_dict.get('cart_items') is None:
                session_dict['cart_items'] = {}

            key = self._session_key(session_id)
            expiry_seconds = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration

            redis_success = False
            try:
                if redis_client._ensure_connection():
                    redis_success = redis_client.setex(
                        key,
                        expiry_seconds,
                        json.dumps(session_dict, default=str)  # ADD default=str FOR BETTER SERIALIZATION
                    )
                    if redis_success:
                        logger.info(
                            f"✅ SessionService: Created {session.session_type.value} session: {session_id} with {len(cart_items)} cart items")
                    else:
                        logger.error(f"❌ SessionService: Failed to save session to Redis: {session_id}")
            except Exception as redis_error:
                logger.warning(f"Redis error but continuing: {redis_error}")

            if session.user_id and redis_client._ensure_connection():
                user_session_key = f"{self._redis_user_session_prefix}{session.user_id}"
                redis_client.setex(user_session_key, expiry_seconds, session_id)

            if session.guest_id and redis_client._ensure_connection():
                guest_session_key = f"{self._redis_guest_session_prefix}{session.guest_id}"
                redis_client.setex(guest_session_key, expiry_seconds, session_id)

            return session

        except Exception as e:
            logger.error(f"❌ Failed to create session: {e}")
            # Emergency fallback session
            emergency_id = f"emergency_{uuid.uuid4().hex}"
            return SessionData(
                session_id=emergency_id,
                session_type=session_data.get('session_type', SessionType.GUEST),
                user_id=session_data.get('user_id'),
                guest_id=session_data.get('guest_id', str(uuid.uuid4())),
                cart_items=session_data.get('cart_items', {}),  # Ensure cart_items in emergency session
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                ip_address=session_data.get('ip_address', 'unknown'),
                user_agent=session_data.get('user_agent', ''),
                expires_at=datetime.utcnow() + timedelta(hours=24),
                security_token=None,
                csrf_token=None,
                fingerprint=None,
                ip_addresses=[session_data.get('ip_address', 'unknown')]
            )

    def get_session(self, session_id: str, request_ip: str = None, request_user_agent: str = None,
                    security_token: str = None) -> Optional[SessionData]:
        try:
            if not session_id:
                logger.debug("No session ID provided")
                return None

            if not redis_client._ensure_connection():
                logger.warning("Redis not available for session retrieval")
                return None

            key = self._session_key(session_id)
            data = redis_client.get(key)

            if data:
                try:
                    session_dict = json.loads(data)
                    logger.info(f"🔍 DEBUG: Loading session {session_id}")
                    logger.info(f"🔍 DEBUG: Raw cart_items: {session_dict.get('cart_items')}")
                    logger.info(f"🔍 DEBUG: Cart items type: {type(session_dict.get('cart_items'))}")

                    # Convert string dates back to datetime objects
                    session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
                    session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
                    session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])

                    # Convert session type string to enum
                    session_type_str = session_dict.get('session_type', 'guest')
                    session_dict['session_type'] = SessionType.USER if session_type_str == 'user' else SessionType.GUEST

                    # Ensure cart_items is never None
                    if session_dict.get('cart_items') is None:
                        logger.warning(f"❌ DEBUG: Cart items is None, setting to empty dict")
                        session_dict['cart_items'] = {}
                    else:
                        logger.info(f"✅ DEBUG: Cart items preserved: {len(session_dict['cart_items'])} items")

                    # Ensure ip_addresses is never None
                    if session_dict.get('ip_addresses') is None:
                        session_dict['ip_addresses'] = []

                    session_dict['session_id'] = session_id

                    logger.info(
                        f"🔍 DEBUG: Session dict before SessionData creation: cart_items = {session_dict.get('cart_items')}")

                    # Create SessionData object
                    session = SessionData(**session_dict)
                    logger.info(f"✅ DEBUG: Session created successfully with {len(session.cart_items)} cart items")

                    # Validate session security
                    if not self._validate_session_security(session, request_ip, request_user_agent, security_token):
                        logger.warning(f"Session security validation failed for {session_id}")
                        return None

                    # Rotate session if needed
                    if self.enable_session_rotation and self._should_rotate_session(session):
                        logger.info(f"Rotating session {session_id}")
                        return self.rotate_session(session_id)

                    # Update session activity
                    self._update_session_activity_only(session_id)
                    logger.info(f"✅ DEBUG: Final session has {len(session.cart_items)} cart items")
                    return session

                except Exception as parse_error:
                    logger.error(f"Failed to parse session data for {session_id}: {parse_error}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            else:
                logger.debug(f"Session not found in Redis: {session_id}")
                return None

        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def find_guest_session_by_ip(self, ip_address: str, user_agent: str) -> Optional[SessionData]:
        """Find an existing guest session for the given IP address and user agent"""
        try:
            if not redis_client._ensure_connection():
                return None

            # Search for guest sessions with this IP address
            pattern = f"{self._redis_session_prefix}*"
            all_keys = redis_client.keys(pattern)

            for key in all_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        session_dict = json.loads(data)

                        # Check if it's a guest session with matching IP
                        session_type = session_dict.get('session_type')
                        session_ip = session_dict.get('ip_address')
                        session_user_agent = session_dict.get('user_agent')

                        if (session_type == 'guest' and
                                session_ip == ip_address and
                                session_user_agent == user_agent):

                            # Found matching session, validate it's not expired
                            expires_at = datetime.fromisoformat(session_dict['expires_at'])
                            if datetime.utcnow() < expires_at:
                                session_id = key.replace(self._redis_session_prefix, "")

                                # Convert to SessionData object
                                session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
                                session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
                                session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])
                                session_dict['session_type'] = SessionType.GUEST
                                session_dict['session_id'] = session_id

                                if session_dict.get('cart_items') is None:
                                    session_dict['cart_items'] = {}
                                if session_dict.get('ip_addresses') is None:
                                    session_dict['ip_addresses'] = []

                                session = SessionData(**session_dict)
                                logger.info(f"Found existing guest session for IP {ip_address}: {session_id}")
                                return session

                except Exception as e:
                    logger.debug(f"Error checking session {key}: {e}")
                    continue

            return None

        except Exception as e:
            logger.error(f"Error finding guest session by IP: {e}")
            return None


    def _validate_session_security(self, session: SessionData, request_ip: str, request_user_agent: str,
                                   security_token: str) -> bool:
        try:
            if datetime.utcnow() > session.expires_at:
                logger.warning("Session expired")
                return False

            # For user sessions, allow any IP that has been used before
            if session.session_type == SessionType.USER and session.user_id:
                if request_ip and session.ip_addresses:
                    # Allow if this IP has been used before for this session
                    ip_allowed = request_ip in session.ip_addresses
                    if not ip_allowed:
                        logger.info(f"New IP detected for user session: {request_ip}. Adding to allowed IPs.")
                        # Add new IP to allowed list
                        session.ip_addresses.append(request_ip)
                        self._update_session_data(session.session_id, {
                            'ip_addresses': session.ip_addresses,
                            'ip_address': request_ip
                        })
                # For user sessions, we're more permissive with IP changes
                return True

            # For guest sessions, maintain stricter IP validation
            if self.require_security_token and security_token:
                if not self._validate_security_token(session.session_id, request_ip, security_token):
                    logger.warning("Invalid security token")
                    return False

            if self.enable_ip_validation and session.ip_address and request_ip:
                try:
                    # For guest sessions, allow IP changes but track them
                    if request_ip not in session.ip_addresses:
                        session.ip_addresses.append(request_ip)
                        self._update_session_data(session.session_id, {
                            'ip_addresses': session.ip_addresses,
                            'ip_address': request_ip
                        })
                except ValueError:
                    logger.warning("Invalid IP address format")
                    return False

            if self.enable_user_agent_validation and request_user_agent and session.fingerprint:
                expected_fingerprint = self._calculate_fingerprint(request_user_agent, request_ip)
                if session.fingerprint != expected_fingerprint:
                    logger.warning("User agent fingerprint mismatch - session may be compromised")
            return True
        except Exception as e:
            logger.error(f"Session security validation failed: {e}")
            return False

    def _should_rotate_session(self, session: SessionData) -> bool:
        try:
            session_age = datetime.utcnow() - session.created_at
            return session_age.total_seconds() > self.session_rotation_interval
        except Exception as e:
            logger.error(f"Failed to check session rotation: {e}")
            return False

    def _update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Internal method to update specific session fields"""
        try:
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
            return self.update_session_data(session_id, updates)
        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def rotate_session(self, old_session_id: str) -> Optional[SessionData]:
        try:
            if not self._check_rate_limit(f"rotate:{old_session_id}", "update"):
                return None
            old_session = self.get_session(old_session_id)
            if not old_session:
                return None

            new_session_data = {
                'session_type': old_session.session_type,
                'user_id': old_session.user_id,
                'guest_id': old_session.guest_id,
                'cart_items': old_session.cart_items,
                'ip_address': old_session.ip_address,
                'user_agent': old_session.user_agent,
                'ip_addresses': old_session.ip_addresses
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
        return self._update_session_activity_only(session_id)

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        """Get the active session for a user - ONE SESSION PER USER"""
        try:
            if not redis_client._ensure_connection():
                return None

            user_session_key = f"{self._redis_user_session_prefix}{user_id}"
            session_id = redis_client.get(user_session_key)

            if session_id:
                session = self.get_session(session_id)
                if session and session.user_id == user_id:
                    return session
                else:
                    # Clean up invalid mapping
                    redis_client.delete(user_session_key)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None

    def get_session_by_guest_id(self, guest_id: str) -> Optional[SessionData]:
        try:
            if not redis_client._ensure_connection():
                return None

            guest_session_key = f"{self._redis_guest_session_prefix}{guest_id}"
            session_id = redis_client.get(guest_session_key)

            if session_id:
                return self.get_session(session_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for guest {guest_id}: {e}")
            return None

    def migrate_guest_to_user_session(self, guest_session_id: str, user_id: int) -> Optional[SessionData]:
        try:
            if not self._check_rate_limit(f"migrate:{user_id}", "update"):
                return None

            guest_session = self.get_session(guest_session_id)
            if not guest_session or guest_session.session_type != SessionType.GUEST:
                return None

            # Check if user already has a session
            existing_user_session = self.get_session_by_user_id(user_id)
            merged_cart_items = {}

            # Merge cart items from both sessions
            if existing_user_session and existing_user_session.cart_items:
                merged_cart_items.update(existing_user_session.cart_items)

            if guest_session.cart_items:
                for item_key, guest_item in guest_session.cart_items.items():
                    if item_key in merged_cart_items:
                        merged_cart_items[item_key]['quantity'] += guest_item['quantity']
                    else:
                        merged_cart_items[item_key] = guest_item

            # Create or update user session
            if existing_user_session:
                # Update existing user session
                session_data = {
                    'cart_items': merged_cart_items,
                    'ip_address': guest_session.ip_address,
                    'user_agent': guest_session.user_agent
                }
                # Add guest IP to user session's IP list
                if guest_session.ip_address and guest_session.ip_address not in existing_user_session.ip_addresses:
                    session_data['ip_addresses'] = existing_user_session.ip_addresses + [guest_session.ip_address]

                self.update_session_data(existing_user_session.session_id, session_data)
                self.delete_session(guest_session_id)
                logger.info(f"Merged guest session into existing user session for user {user_id}")
                return existing_user_session
            else:
                # Create new user session
                session_data = {
                    'session_type': SessionType.USER,
                    'user_id': user_id,
                    'guest_id': None,
                    'ip_address': guest_session.ip_address,
                    'user_agent': guest_session.user_agent,
                    'cart_items': merged_cart_items,
                    'ip_addresses': guest_session.ip_addresses if guest_session.ip_addresses else [
                        guest_session.ip_address]
                }
                new_session = self.create_session(session_data)
                self.delete_session(guest_session_id)
                logger.info(f"Migrated guest session to new user session for user {user_id}")
                return new_session

        except Exception as e:
            logger.error(f"Failed to migrate guest session to user: {e}")
            return None

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        try:
            if not self._check_rate_limit(f"update:{session_id}", "update"):
                return False

            # Get the current session first
            session = self.get_session(session_id)
            if not session:
                logger.error(f"Session not found for update: {session_id}")
                return False

            # Apply updates to session object
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)

            # Update activity timestamp
            session.last_activity = datetime.utcnow()

            # Convert session to dictionary for Redis storage
            session_dict = session.model_dump()
            session_dict['session_type'] = session_dict['session_type'].value
            session_dict['created_at'] = session_dict['created_at'].isoformat()
            session_dict['last_activity'] = session_dict['last_activity'].isoformat()
            session_dict['expires_at'] = session_dict['expires_at'].isoformat()

            # Ensure cart_items is never None
            if session_dict.get('cart_items') is None:
                session_dict['cart_items'] = {}

            key = self._session_key(session_id)
            expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration

            # Save to Redis with proper error handling
            redis_success = False
            try:
                if redis_client._ensure_connection():
                    redis_success = redis_client.setex(
                        key,
                        expiry,
                        json.dumps(session_dict, default=str)
                    )
                    if redis_success:
                        logger.info(
                            f"✅ SessionService: Successfully updated session {session_id} with {len(updates.get('cart_items', {}))} cart items")
                    else:
                        logger.error(f"❌ SessionService: Redis setex failed for session {session_id}")
                else:
                    logger.error(f"❌ SessionService: Redis not available for session {session_id}")
            except Exception as redis_error:
                logger.error(f"❌ SessionService: Redis error updating session {session_id}: {redis_error}")
                return False

            return redis_success

        except Exception as e:
            logger.error(f"❌ SessionService: Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        try:
            if not self._check_rate_limit(f"delete:{session_id}", "delete"):
                return False

            session = self.get_session(session_id)
            if not session:
                return False

            redis_client.delete(self._session_key(session_id))
            if session.user_id:
                user_session_key = f"{self._redis_user_session_prefix}{session.user_id}"
                redis_client.delete(user_session_key)

            if session.guest_id:
                guest_session_key = f"{self._redis_guest_session_prefix}{session.guest_id}"
                redis_client.delete(guest_session_key)

            logger.info(f"Deleted secure session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

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

            if session.ip_addresses is None:
                session.ip_addresses = [session.ip_address] if session.ip_address else []
                repairs_made = True
                logger.info(f"Repaired session {session_id}: ip_addresses was None")

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
        try:
            session = self.get_session_by_user_id(user_id)
            if session:
                return self.delete_session(session.session_id)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate all secure sessions for user {user_id}: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
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


session_service = SecureSessionService()