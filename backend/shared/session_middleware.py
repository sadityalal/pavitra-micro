from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import uuid
from shared import get_logger, config
from .session_service import session_service, SessionType, SessionData
import re

logger = get_logger(__name__)


class SecureSessionMiddleware:
    def __init__(self, app):
        self.app = app
        self.session_cookie_name = "session_id"
        self.session_header_name = "X-Secure-Session-ID"
        self.security_header_name = "X-Security-Token"
        self.csrf_header_name = "X-CSRF-Token"
        self.session_config = config.get_session_config()
        self._load_cookie_settings()

    def _load_cookie_settings(self):
        try:
            self.cookie_samesite = self.session_config.get('cookie_samesite', 'Lax')
            self.cookie_httponly = self.session_config.get('cookie_httponly', True)
            self.cookie_secure = self.session_config.get('cookie_secure', True)
            self.enable_secure_cookies = self.session_config.get('enable_secure_cookies', True)
        except Exception as e:
            logger.error(f"Failed to load cookie settings: {e}")
            self.cookie_samesite = 'Lax'
            self.cookie_httponly = True
            self.cookie_secure = True
            self.enable_secure_cookies = True

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        response = await self._handle_request(request, scope, receive, send)
        return response

    async def _handle_request(self, request: Request, scope, receive, send):
        try:
            session_id = self._get_session_id(request)
            security_token = request.headers.get(self.security_header_name)
            is_new_session = False
            session = None

            should_handle_session = self._should_handle_session(request)
            logger.debug(
                f"Session handling for {request.url.path}: should_handle={should_handle_session}, session_id={session_id}")

            if should_handle_session:
                # FIRST: Try to get existing session by ID
                if session_id:
                    session = session_service.get_session(
                        session_id,
                        request_ip=request.client.host if request.client else 'unknown',
                        request_user_agent=request.headers.get("user-agent", ""),
                        security_token=security_token
                    )
                    if session:
                        logger.debug(f"✅ Using existing session from ID: {session_id}")
                    else:
                        logger.debug(f"❌ Provided session ID invalid: {session_id}")
                        session_id = None
                        session = None

                # SECOND: If no session found, check for authenticated user
                if not session:
                    try:
                        from .auth_middleware import get_current_user
                        current_user = await get_current_user(request)
                        if current_user and current_user.get('sub'):
                            user_id = int(current_user['sub'])
                            ip_address = request.client.host if request.client else 'unknown'
                            user_agent = request.headers.get("user-agent", "")
                            session = session_service.get_or_create_user_session(user_id, ip_address, user_agent)
                            if session:
                                session_id = session.session_id
                                logger.info(f"🔄 Created/retrieved user session for user {user_id}: {session_id}")
                    except Exception as auth_error:
                        # User not authenticated, continue as guest
                        pass

                # THIRD: Handle guest session (only if no existing session)
                if not session:
                    # Get or create guest ID from cookies
                    guest_id = request.cookies.get("guest_id")
                    if not guest_id:
                        guest_id = str(uuid.uuid4())
                        logger.info(f"🆕 Generated new guest ID: {guest_id}")

                    ip_address = request.client.host if request.client else 'unknown'
                    user_agent = request.headers.get("user-agent", "")

                    # Try to find existing guest session first
                    existing_session = self._find_existing_guest_session(ip_address, user_agent)
                    if existing_session:
                        session = existing_session
                        session_id = session.session_id
                        logger.info(f"🔍 Reusing existing guest session: {session_id}")
                    else:
                        # Create new guest session
                        session = session_service.get_or_create_guest_session(guest_id, ip_address, user_agent)
                        if session:
                            session_id = session.session_id
                            is_new_session = True
                            logger.info(f"🆕 Created new guest session: {session_id}")

                request.state.session = session
                request.state.session_id = session_id
                request.state.is_new_session = is_new_session

            # Continue with the request handling
            async def session_send_wrapper(message):
                if message["type"] == "http.response.start":
                    current_session = getattr(request.state, 'session', None)
                    current_session_id = getattr(request.state, 'session_id', None)
                    current_is_new_session = getattr(request.state, 'is_new_session', False)
                    await self._set_response_headers(message, current_session, current_session_id,
                                                     current_is_new_session, request)
                await send(message)

            response = await self.app(scope, receive, session_send_wrapper)
            return response

        except Exception as e:
            logger.error(f"❌ Secure session middleware error: {e}")
            return await self.app(scope, receive, send)

    def _find_existing_guest_session(self, ip_address: str, user_agent: str) -> Optional[SessionData]:
        try:
            if not redis_client._ensure_connection():
                return None

            pattern = f"{self._redis_session_prefix}*"
            all_keys = redis_client.keys(pattern)
            for key in all_keys:
                try:
                    data = redis_client.get(key)
                    if data:
                        session_dict = json.loads(data)
                        session_type = session_dict.get('session_type')
                        session_ip = session_dict.get('ip_address')
                        session_user_agent = session_dict.get('user_agent')

                        # Check if this is a guest session with matching IP and user agent
                        if (session_type == 'guest' and
                                session_ip == ip_address and
                                session_user_agent == user_agent):
                            # Found matching session, validate it's not expired
                            expires_at = datetime.fromisoformat(session_dict['expires_at'])
                            if datetime.utcnow() < expires_at:
                                session_id = key.replace(self._redis_session_prefix, "")
                                logger.info(f"🔍 Found existing guest session for IP {ip_address}: {session_id}")

                                # Load the full session data
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
                                return session
                except Exception as e:
                    logger.debug(f"Error checking session {key}: {e}")
                    continue
            return None
        except Exception as e:
            logger.error(f"Error finding guest session by IP: {e}")
            return None

    def _get_guest_id(self, request: Request) -> str:
        # Always return the guest_id from cookies, don't generate new one here
        guest_id = request.cookies.get("guest_id")
        if not guest_id:
            guest_id = str(uuid.uuid4())
            logger.info(f"🆕 Generated new guest ID in middleware: {guest_id}")
        return guest_id

    def _get_session_id(self, request: Request) -> Optional[str]:
        try:
            # First try to get session ID from cookies (highest priority)
            session_id = request.cookies.get(self.session_cookie_name)
            if session_id and self._validate_session_id(session_id):
                logger.debug(f"Found session ID in cookies: {session_id}")
                return session_id

            # Then try headers
            header_names = [
                'X-Session-ID', 'x-session-id',
                'X-Secure-Session-ID', 'x-secure-session-id',
                'Session-ID', 'session-id',
                'Authorization'  # Also check Authorization header for Bearer token with session
            ]

            for header_name in header_names:
                header_value = request.headers.get(header_name)
                if header_value:
                    # For Authorization header, check if it's a session token
                    if header_name.lower() == 'authorization' and header_value.startswith('Session '):
                        session_id = header_value[8:].strip()  # Remove 'Session ' prefix
                        if self._validate_session_id(session_id):
                            logger.debug(f"Found session ID in Authorization header: {session_id}")
                            return session_id
                    # For other headers, use directly
                    elif self._validate_session_id(header_value):
                        logger.debug(f"Found session ID in {header_name} header: {header_value}")
                        return header_value

            logger.debug("No valid session ID found in cookies or headers")
            return None
        except Exception as e:
            logger.error(f"Error extracting session ID: {e}")
            return None

    def _validate_session_id(self, session_id: str) -> bool:
        if not session_id or not isinstance(session_id, str):
            return False
        # Allow session IDs that are UUIDs or the secure tokens generated by session service
        uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        secure_token_pattern = r'^[A-Za-z0-9_-]{32,64}$'
        emergency_pattern = r'^(emergency|minimal|error_fallback)_[a-fA-F0-9]+$'

        return (bool(re.match(uuid_pattern, session_id)) or
                bool(re.match(secure_token_pattern, session_id)) or
                bool(re.match(emergency_pattern, session_id)))

    async def _set_response_headers(self, message, session, session_id, is_new_session, request):
        headers = message.get("headers", [])

        # Remove existing session-related headers to avoid duplicates
        headers = [header for header in headers if not (
                header[0] in [b"set-cookie", b"x-session-id", b"x-secure-session-id", b"x-csrf-token"] and
                (self.session_cookie_name.encode() in header[1] if header[0] == b"set-cookie" else True)
        )]

        if session_id:
            headers.append([b"x-secure-session-id", session_id.encode()])
            if session and session.csrf_token:
                headers.append([b"x-csrf-token", session.csrf_token.encode()])
            logger.debug(f"Setting session ID in headers: {session_id}")

        should_set_cookie = (is_new_session or
                             (session_id and self.enable_secure_cookies and
                              not request.cookies.get(self.session_cookie_name) and
                              # Don't set cookie if we're using header-based authentication
                              not request.headers.get('X-Secure-Session-ID') and
                              not request.headers.get('Authorization')))

        if should_set_cookie and session_id:
            cookie_value = self._build_secure_cookie(session_id, session)
            headers.append([b"set-cookie", cookie_value.encode()])
            logger.info(f"Set session cookie: {session_id}")

        if session and session.session_type == SessionType.GUEST and session.guest_id:
            if not request.cookies.get("guest_id"):
                guest_cookie = self._build_guest_cookie(session.guest_id)
                headers.append([b"set-cookie", guest_cookie.encode()])

        headers.extend([
            [b"x-content-type-options", b"nosniff"],
            [b"x-frame-options", b"DENY"],
            [b"x-xss-protection", b"1; mode=block"],
            [b"strict-transport-security", b"max-age=31536000; includeSubDomains"]
        ])

        message["headers"] = headers

    def _build_secure_cookie(self, session_id: str, session: SessionData) -> str:
        if session and session.session_type == SessionType.USER:
            max_age = session_service.user_session_duration
        else:
            max_age = session_service.guest_session_duration

        cookie_parts = [
            f"{self.session_cookie_name}={session_id}",
            f"Max-Age={max_age}",
            f"HttpOnly={str(self.cookie_httponly).lower()}",
            f"SameSite={self.cookie_samesite}",
            "Path=/"
        ]

        if self.cookie_secure and not config.debug_mode:
            cookie_parts.append("Secure")

        return "; ".join(cookie_parts)

    def _build_guest_cookie(self, guest_id: str) -> str:
        max_age = session_service.guest_session_duration
        cookie_parts = [
            f"guest_id={guest_id}",
            f"Max-Age={max_age}",
            f"HttpOnly={str(self.cookie_httponly).lower()}",
            f"SameSite={self.cookie_samesite}",
            "Path=/"
        ]
        if self.cookie_secure and not config.debug_mode:
            cookie_parts.append("Secure")
        return "; ".join(cookie_parts)

    def _should_handle_session(self, request: Request) -> bool:
        path = request.url.path
        no_session_paths = [
            '/health', '/favicon.ico', '/metrics', '/docs', '/redoc',
            '/openapi.json', '/static/', '/api/v1/auth/health',
            '/api/v1/users/health', '/refresh-config', '/debug/'
        ]

        if any(path.startswith(p) for p in no_session_paths):
            return False

        session_required_paths = [
            '/api/v1/users/cart', '/api/v1/auth/login', '/api/v1/auth/register',
            '/api/v1/auth/logout', '/api/v1/auth/refresh', '/checkout',
            '/cart', '/wishlist', '/profile'
        ]

        if any(path.startswith(p) for p in session_required_paths):
            return True

        return True

    @property
    def user_session_duration(self):
        return session_service.user_session_duration

    @property
    def guest_session_duration(self):
        return session_service.guest_session_duration


def get_session(request: Request) -> Optional[SessionData]:
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    return getattr(request.state, 'session_id', None)


def is_new_session(request: Request) -> bool:
    return getattr(request.state, 'is_new_session', False)


SessionMiddleware = SecureSessionMiddleware