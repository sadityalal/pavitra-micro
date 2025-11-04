from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, Callable, Any
from datetime import datetime
import uuid
from shared import get_logger, config
from .session_service import session_service, SessionType, SessionData

logger = get_logger(__name__)


class SessionMiddleware:
    def __init__(self, app):
        self.app = app
        self.session_cookie_name = "session_id"
        self.cookie_domain = None  # Set this if you need cross-subdomain sessions

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        session_id = self._get_session_id(request)
        session = None
        is_new_session = False

        # Try to get existing session first
        if session_id:
            session = session_service.get_session(
                session_id,
                request_ip=request.client.host if request.client else 'unknown',
                request_user_agent=request.headers.get("user-agent", "")
            )
            if session:
                logger.debug(f"✅ Retrieved existing session: {session_id}")
                # Update session activity
                session_service.update_session_activity(session_id)
            else:
                logger.debug(f"❌ Session not found: {session_id}")
                session_id = None

        # Only create new session if no valid session exists
        if not session:
            session = await self._create_new_session(request)
            if session:
                session_id = session.session_id
                is_new_session = True
                logger.info(f"🆕 Created new {session.session_type.value} session: {session_id}")
            else:
                logger.error("❌ Failed to create new session")

        request.state.session = session
        request.state.session_id = session_id

        async def session_send_wrapper(message):
            if message["type"] == "http.response.start":
                # Always set cookie to ensure it's available across services
                if session_id:
                    headers = message.get("headers", [])
                    cookie_value = self._build_cookie_value(session_id)
                    # Remove any existing session cookie
                    headers = [header for header in headers
                               if not (header[0] == b"set-cookie" and
                                       self.session_cookie_name.encode() in header[1])]
                    headers.append([b"set-cookie", cookie_value.encode()])
                    message["headers"] = headers
                    logger.debug(f"🔗 Set session cookie: {session_id}")
            await send(message)

        try:
            await self.app(scope, receive, session_send_wrapper)
        except Exception as e:
            logger.error(f"Session middleware error: {e}")
            await self.app(scope, receive, send)

    def _get_session_id(self, request: Request) -> Optional[str]:
        # Check cookie first
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id

        return None

    def _build_cookie_value(self, session_id: str) -> str:
        cookie_value = f"{self.session_cookie_name}={session_id}; Max-Age=86400; HttpOnly; SameSite=lax; Path=/"
        if self.cookie_domain:
            cookie_value += f"; Domain={self.cookie_domain}"
        if not config.debug_mode:
            cookie_value += "; Secure"
        return cookie_value

    async def _create_new_session(self, request: Request) -> Optional[SessionData]:
        try:
            session_type = SessionType.GUEST
            user_id = None
            guest_id = str(uuid.uuid4())

            # Check if we have a JWT token to create user session
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
            return session

        except Exception as e:
            logger.error(f"Failed to create new session: {e}", exc_info=True)
            return None


def get_session(request: Request) -> Optional[SessionData]:
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    return getattr(request.state, 'session_id', None)