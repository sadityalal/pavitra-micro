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
            original_session_id = session_id

            if session_id:
                session = session_service.get_session(
                    session_id,
                    request_ip=request.client.host if request.client else 'unknown',
                    request_user_agent=request.headers.get("user-agent", ""),
                    security_token=security_token
                )
                if session:
                    logger.debug(f"Using existing session: {session_id}, type: {session.session_type}")
                else:
                    session_id = None
                    logger.debug(f"Invalid session ID provided: {session_id}")

            if not session:
                should_create_session = self._should_create_session(request)
                if should_create_session:
                    session = await self._create_new_guest_session(request)
                    if session:
                        session_id = session.session_id
                        is_new_session = True
                        logger.info(f"✅ Created new guest session: {session_id}")
                else:
                    logger.debug("Skipping session creation for non-browser request")

            request.state.session = session
            request.state.session_id = session_id
            request.state.is_new_session = is_new_session
            request.state.original_session_id = original_session_id

            async def session_send_wrapper(message):
                if message["type"] == "http.response.start":
                    current_session = getattr(request.state, 'session', None)
                    current_session_id = getattr(request.state, 'session_id', None)
                    current_is_new_session = getattr(request.state, 'is_new_session', False)
                    await self._set_response_headers(
                        message, current_session, current_session_id, current_is_new_session, request
                    )
                await send(message)

            try:
                response = await self.app(scope, receive, session_send_wrapper)
                return response
            except Exception as e:
                logger.error(f"Request processing error: {e}")
                raise
        except Exception as e:
            logger.error(f"Secure session middleware error: {e}")
            return await self.app(scope, receive, send)

    def _get_session_id(self, request: Request) -> Optional[str]:
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id and self._validate_session_id(session_id):
            logger.debug(f"Got session ID from cookie: {session_id}")
            return session_id
        session_id = request.headers.get(self.session_header_name)
        if session_id and self._validate_session_id(session_id):
            logger.debug(f"Got session ID from header: {session_id}")
            return session_id
        logger.debug("No valid session ID found in request")
        return None

    def _validate_session_id(self, session_id: str) -> bool:
        return bool(re.match(r'^[A-Za-z0-9_-]{32,64}$', session_id))

    async def _set_response_headers(self, message, session, session_id, is_new_session, request):
        headers = message.get("headers", [])
        original_session_id = getattr(request.state, 'original_session_id', None)
        migrated_session_id = None

        if (session and
                hasattr(session, 'session_id') and
                original_session_id and
                session.session_id != original_session_id):
            migrated_session_id = session.session_id
            logger.info(f"Session migrated from {original_session_id} to {migrated_session_id}")

        final_session_id = migrated_session_id if migrated_session_id else session_id
        headers = [header for header in headers if not (
                header[0] in [b"set-cookie", b"x-session-id", b"x-secure-session-id", b"x-csrf-token"] and
                (self.session_cookie_name.encode() in header[1] if header[0] == b"set-cookie" else True)
        )]

        if final_session_id:
            headers.append([b"x-secure-session-id", final_session_id.encode()])
            if session and session.csrf_token:
                headers.append([b"x-csrf-token", session.csrf_token.encode()])
            logger.debug(f"Setting session ID in headers: {final_session_id}")

        should_set_cookie = (is_new_session or migrated_session_id) and session and self.enable_secure_cookies
        if should_set_cookie:
            cookie_session_id = migrated_session_id if migrated_session_id else final_session_id
            cookie_value = self._build_secure_cookie(cookie_session_id, session)
            headers.append([b"set-cookie", cookie_value.encode()])
            logger.info(f"Set session cookie: {cookie_session_id}")

        headers.extend([
            [b"x-content-type-options", b"nosniff"],
            [b"x-frame-options", b"DENY"],
            [b"x-xss-protection", b"1; mode=block"],
            [b"strict-transport-security", b"max-age=31536000; includeSubDomains"]
        ])

        message["headers"] = headers

    def _build_secure_cookie(self, session_id: str, session: SessionData) -> str:
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
        if request.url.path.startswith('/api/v1/users/cart') or \
                request.url.path.startswith('/api/v1/products'):
            return True

        frontend_paths = ['/', '/products', '/cart', '/checkout', '/login', '/register']
        if any(request.url.path.startswith(path) for path in frontend_paths):
            return True

        no_session_paths = ['/health', '/favicon.ico', '/metrics', '/docs', '/redoc', '/openapi.json', '/static/']
        if any(request.url.path.startswith(path) for path in no_session_paths):
            return False

        has_frontend_indicators = any([
            request.headers.get('origin'),
            request.headers.get('referer'),
            'text/html' in request.headers.get('accept', ''),
            request.headers.get('sec-fetch-mode') == 'navigate',
            request.headers.get('x-requested-with') == 'XMLHttpRequest',
            request.headers.get('user-agent', '').lower() in ['mozilla', 'chrome', 'safari', 'firefox']
        ])
        return has_frontend_indicators

    async def _create_new_guest_session(self, request: Request) -> Optional[SessionData]:
        try:
            guest_id = str(uuid.uuid4())
            session_data = {
                'session_type': SessionType.GUEST,
                'user_id': None,
                'guest_id': guest_id,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent", ""),
                'cart_items': {}
            }

            session = session_service.create_session(session_data)

            if session:
                logger.info(f"✅ Created new guest session: {session.session_id}")
                return session
            else:
                logger.error("❌ Session service returned None, creating emergency session")
                # Emergency fallback - create session directly
                return self._create_emergency_session(request, guest_id)

        except Exception as e:
            logger.error(f"❌ Critical error in guest session creation: {e}")
            return self._create_emergency_session(request, str(uuid.uuid4()))

    def _create_emergency_session(self, request: Request, guest_id: str) -> SessionData:
        """Create an emergency session when all else fails"""
        return SessionData(
            session_id=f"emergency_{guest_id}",
            session_type=SessionType.GUEST,
            user_id=None,
            guest_id=guest_id,
            cart_items={},
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            ip_address=request.client.host if request.client else 'unknown',
            user_agent=request.headers.get("user-agent", ""),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            security_token=None,
            csrf_token=None,
            fingerprint=None
        )

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