from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import uuid
from shared import get_logger, config
from .session_service import session_service, SessionType, SessionData

logger = get_logger(__name__)


class SessionMiddleware:
    def __init__(self, app):
        self.app = app
        self.session_cookie_name = "shared_session_id"
        self.session_header_name = "X-Session-ID"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        session_id = self._get_session_id(request)
        session = None
        is_new_session = False

        # If we have a session ID, try to get the session
        if session_id:
            session = session_service.get_session(
                session_id,
                request_ip=request.client.host if request.client else 'unknown',
                request_user_agent=request.headers.get("user-agent", "")
            )

            # If session is invalid, clear the ID
            if not session:
                session_id = None
                logger.warning(f"Invalid session ID provided: {session_id}")

        # If no valid session exists, create one ONLY in user service
        if not session:
            # Only create sessions in user service (not auth service)
            should_create_session = self._should_create_session(request)
            if should_create_session:
                session = await self._create_new_session(request)
                if session:
                    session_id = session.session_id
                    is_new_session = True
                    logger.info(f"🆕 Created primary shared session: {session_id}")
            else:
                # For auth service or other services, don't create new sessions
                logger.debug("Skipping session creation - not user service")

        request.state.session = session
        request.state.session_id = session_id

        async def session_send_wrapper(message):
            if message["type"] == "http.response.start":
                # Only set cookie if we have a valid session AND it's a new session
                # AND this is the user service (primary session creator)
                should_set_cookie = (
                        is_new_session and
                        session and
                        self._is_user_service_response(request)
                )

                if should_set_cookie:
                    headers = message.get("headers", [])
                    # Remove any existing session cookies
                    headers = [header for header in headers
                               if not (header[0] == b"set-cookie" and
                                       self.session_cookie_name.encode() in header[1])]

                    cookie_value = self._build_cookie_value(session_id)
                    headers.append([b"set-cookie", cookie_value.encode()])
                    message["headers"] = headers

                    logger.info(f"🍪 Set shared session cookie: {session_id}")

                # Always include session ID in headers for microservices coordination
                if session_id:
                    headers = message.get("headers", [])
                    # Remove any existing session headers
                    headers = [header for header in headers
                               if not (header[0] == b"x-session-id")]
                    headers.append([b"x-session-id", session_id.encode()])
                    message["headers"] = headers
                    logger.debug(f"📤 Forwarding session ID: {session_id}")

            await send(message)

        try:
            await self.app(scope, receive, session_send_wrapper)
        except Exception as e:
            logger.error(f"Shared session middleware error: {e}")
            await self.app(scope, receive, send)

    def _get_session_id(self, request: Request) -> Optional[str]:
        # Priority 1: Header (for microservice communication)
        session_id = request.headers.get(self.session_header_name)
        if session_id:
            logger.debug(f"Got session ID from header: {session_id}")
            return session_id

        # Priority 2: Cookie (for frontend communication)
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            logger.debug(f"Got session ID from cookie: {session_id}")
            return session_id

        logger.debug("No session ID found in request")
        return None

    def _build_cookie_value(self, session_id: str) -> str:
        cookie_value = f"{self.session_cookie_name}={session_id}; Max-Age=86400; HttpOnly; SameSite=lax; Path=/"
        if not config.debug_mode:
            cookie_value += "; Secure"
        return cookie_value

    def _should_create_session(self, request: Request) -> bool:
        """Determine if this service should create a new session"""
        # Only user service should create sessions
        if not self._is_user_service_request(request):
            return False

        # Don't create sessions for internal health checks
        if request.url.path in ['/health', '/favicon.ico']:
            return False

        # Don't create sessions for options requests
        if request.method == 'OPTIONS':
            return False

        # Check if this is likely a frontend request
        has_frontend_headers = any([
            request.headers.get('origin'),
            request.headers.get('referer'),
            'text/html' in request.headers.get('accept', ''),
            request.headers.get('sec-fetch-mode') == 'navigate'
        ])

        return has_frontend_headers

    def _is_user_service_request(self, request: Request) -> bool:
        """Check if this request is for the user service"""
        # Check if this is a user service endpoint
        user_service_paths = ['/api/v1/users/', '/cart', '/wishlist', '/profile']
        return any(request.url.path.startswith(path) for path in user_service_paths)

    def _is_user_service_response(self, request: Request) -> bool:
        """Check if this response is from the user service"""
        return self._is_user_service_request(request)

    async def _create_new_session(self, request: Request) -> Optional[SessionData]:
        try:
            session_type = SessionType.GUEST
            user_id = None
            guest_id = str(uuid.uuid4())

            # Check for JWT token to create user session
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
                logger.info(f"Created new shared {session_type.value} session: {session.session_id}")
                return session
            else:
                logger.error("Failed to create shared session - session service returned None")
                return None

        except Exception as e:
            logger.error(f"Failed to create new shared session: {e}")
            return None


def get_session(request: Request) -> Optional[SessionData]:
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    return getattr(request.state, 'session_id', None)