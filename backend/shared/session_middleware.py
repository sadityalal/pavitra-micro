from fastapi import Request, Response
from typing import Optional, Callable, Any
from datetime import datetime
import uuid
from shared import get_logger
from .session_service import session_service, SessionType, SessionData

logger = get_logger(__name__)


class SessionMiddleware:
    def __init__(self, app):
        self.app = app
        self.session_cookie_name = "session_id"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        session_id = self._get_session_id(request)
        session = None
        is_new_session = False

        # Get or create session
        if session_id:
            session = session_service.get_session(session_id)

        if not session:
            session = await self._create_new_session(request)
            if session:
                session_id = session.session_id
                is_new_session = True

        # Attach session to request state
        request.state.session = session
        request.state.session_id = session_id

        # Create response wrapper to set cookies
        async def send_wrapper(message):
            if message["type"] == "http.response.start" and is_new_session and session:
                # Add Set-Cookie header
                headers = message.get("headers", [])
                cookie_value = f"{self.session_cookie_name}={session_id}; Max-Age=86400; HttpOnly; SameSite=lax"
                if not request.app.debug:
                    cookie_value += "; Secure"
                headers.append([b"set-cookie", cookie_value.encode()])
                message["headers"] = headers
                logger.info(f"✅ Set session cookie for new {session.session_type.value} session: {session_id}")
            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _get_session_id(self, request: Request) -> Optional[str]:
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Session "):
            return auth_header[8:]
        return None

    async def _create_new_session(self, request: Request) -> Optional[SessionData]:
        try:
            session_type = SessionType.GUEST
            user_id = None
            guest_id = str(uuid.uuid4())

            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                from .auth_middleware import verify_token
                token = auth_header[7:]
                payload = verify_token(token)
                if payload:
                    session_type = SessionType.USER
                    user_id = int(payload['sub'])
                    guest_id = None

            session_data = {
                'session_type': session_type,
                'user_id': user_id,
                'guest_id': guest_id,
                'ip_address': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get("user-agent"),
                'cart_items': {}
            }

            session = session_service.create_session(session_data)
            if session:
                logger.info(f"✅ Created new {session_type.value} session: {session.session_id}")
            return session

        except Exception as e:
            logger.error(f"❌ Failed to create new session: {e}")
            return None


def get_session(request: Request) -> Optional[SessionData]:
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    return getattr(request.state, 'session_id', None)