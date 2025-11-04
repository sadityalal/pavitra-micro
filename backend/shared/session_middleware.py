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
        self.session_cookie_name = "secure_session_id"
        self.session_header_name = "X-Secure-Session-ID"
        self.security_header_name = "X-Security-Token"
        self.csrf_header_name = "X-CSRF-Token"

        # Load cookie settings from database configuration
        self.session_config = config.get_session_config()
        self._load_cookie_settings()

    def _load_cookie_settings(self):
        """Load cookie settings from database configuration"""
        try:
            self.cookie_samesite = self.session_config.get('cookie_samesite', 'Strict')
            self.cookie_httponly = self.session_config.get('cookie_httponly', True)
            self.cookie_secure = self.session_config.get('cookie_secure', True)
            self.enable_secure_cookies = self.session_config.get('enable_secure_cookies', True)
        except Exception as e:
            logger.error(f"Failed to load cookie settings: {e}")
            # Fallback to secure defaults
            self.cookie_samesite = 'Strict'
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
        """Handle request with secure session management"""
        try:
            # Get session ID from headers or cookies
            session_id = self._get_session_id(request)
            security_token = request.headers.get(self.security_header_name)
            is_new_session = False
            session = None

            # Validate existing session
            if session_id:
                session = session_service.get_session(
                    session_id,
                    request_ip=request.client.host if request.client else 'unknown',
                    request_user_agent=request.headers.get("user-agent", ""),
                    security_token=security_token
                )

                if not session:
                    session_id = None
                    logger.warning(f"Invalid session ID provided: {session_id}")

            # Create new session if needed
            if not session:
                should_create_session = self._should_create_session(request)
                if should_create_session:
                    session = await self._create_new_session(request)
                    if session:
                        session_id = session.session_id
                        is_new_session = True
                        logger.info(f"Created new secure shared session: {session_id}")
                else:
                    logger.debug("Skipping session creation")

            # Set session in request state
            request.state.session = session
            request.state.session_id = session_id
            request.state.is_new_session = is_new_session

            # Process request
            async def session_send_wrapper(message):
                if message["type"] == "http.response.start":
                    await self._set_response_headers(
                        message, session, session_id, is_new_session, request
                    )
                await send(message)

            return await self.app(scope, receive, session_send_wrapper)

        except Exception as e:
            logger.error(f"Secure session middleware error: {e}")
            # Fallback to original app
            return await self.app(scope, receive, send)

    def _get_session_id(self, request: Request) -> Optional[str]:
        """Get session ID from request with validation"""
        session_id = request.headers.get(self.session_header_name)
        if session_id and self._validate_session_id(session_id):
            logger.debug(f"Got session ID from header: {session_id}")
            return session_id

        session_id = request.cookies.get(self.session_cookie_name)
        if session_id and self._validate_session_id(session_id):
            logger.debug(f"Got session ID from cookie: {session_id}")
            return session_id

        logger.debug("No valid session ID found in request")
        return None

    def _validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format"""
        return bool(re.match(r'^[A-Za-z0-9_-]{32,64}$', session_id))

    async def _set_response_headers(self, message, session, session_id, is_new_session, request):
        """Set session-related response headers"""
        headers = message.get("headers", [])

        # Remove existing session headers
        headers = [header for header in headers if not (
                header[0] in [b"set-cookie", b"x-session-id", b"x-csrf-token"] and
                (self.session_cookie_name.encode() in header[1] if header[0] == b"set-cookie" else True)
        )]

        # Set new session cookie if needed
        if is_new_session and session and session_id and self.enable_secure_cookies:
            cookie_value = self._build_secure_cookie(session_id, session)
            headers.append([b"set-cookie", cookie_value.encode()])
            logger.info(f"Set secure session cookie: {session_id}")

        # Set session headers
        if session_id:
            headers.append([b"x-session-id", session_id.encode()])
            if session and session.csrf_token:
                headers.append([b"x-csrf-token", session.csrf_token.encode()])
            logger.debug(f"Forwarding secure session ID: {session_id}")

        # Security headers
        headers.extend([
            [b"x-content-type-options", b"nosniff"],
            [b"x-frame-options", b"DENY"],
            [b"x-xss-protection", b"1; mode=block"],
            [b"strict-transport-security", b"max-age=31536000; includeSubDomains"]
        ])

        message["headers"] = headers

    def _build_secure_cookie(self, session_id: str, session: SessionData) -> str:
        """Build secure HTTP cookie using database configuration"""
        max_age = session_service.user_session_duration if session.session_type == SessionType.USER else session_service.guest_session_duration

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

    def _should_create_session(self, request: Request) -> bool:
        """Determine if a session should be created"""
        # Skip for certain paths
        if request.url.path in ['/health', '/favicon.ico', '/metrics']:
            return False

        # Skip for OPTIONS requests
        if request.method == 'OPTIONS':
            return False

        # Only create sessions for frontend requests
        has_frontend_indicators = any([
            request.headers.get('origin'),
            request.headers.get('referer'),
            'text/html' in request.headers.get('accept', ''),
            request.headers.get('sec-fetch-mode') == 'navigate',
            request.headers.get('x-requested-with') == 'XMLHttpRequest'
        ])

        return has_frontend_indicators

    async def _create_new_session(self, request: Request) -> Optional[SessionData]:
        """Create a new secure session"""
        try:
            # Determine session type
            session_type = SessionType.GUEST
            user_id = None
            guest_id = str(uuid.uuid4())

            # Check for authentication
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from .security import verify_token
                    token = auth_header[7:]
                    payload = verify_token(token)
                    if payload:
                        session_type = SessionType.USER
                        user_id = int(payload['sub'])
                        guest_id = None
                        logger.info(f"Creating user session for user_id: {user_id}")
                except Exception as e:
                    logger.warning(f"Token verification failed: {e}")

            # Create session data
            session_data = {
                'session_type': session_type,
                'user_id': user_id,
                'guest_id': guest_id,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent", ""),
                'cart_items': {}
            }

            session = session_service.create_session(session_data)
            if session:
                logger.info(f"Created new secure {session_type.value} session: {session.session_id}")
                return session
            else:
                logger.error("Failed to create secure session - session service returned None")
                return None

        except Exception as e:
            logger.error(f"Failed to create new secure session: {e}")
            return None

    @property
    def user_session_duration(self):
        return session_service.user_session_duration

    @property
    def guest_session_duration(self):
        return session_service.guest_session_duration


def get_session(request: Request) -> Optional[SessionData]:
    """Get session from request state"""
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    """Get session ID from request state"""
    return getattr(request.state, 'session_id', None)


def is_new_session(request: Request) -> bool:
    """Check if session is new"""
    return getattr(request.state, 'is_new_session', False)


# For backward compatibility
SessionMiddleware = SecureSessionMiddleware