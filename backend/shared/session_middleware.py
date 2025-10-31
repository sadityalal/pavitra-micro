from fastapi import Request, Response
from typing import Optional, Callable, Any
from datetime import datetime
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from shared import get_logger
from .session_service import session_service, SessionType, SessionData
from .session_models import SessionCreate

logger = get_logger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.session_cookie_name = "session_id"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        session_id = self._get_session_id(request)
        session = None

        if session_id:
            session = session_service.get_session(session_id)

        if not session:
            session = await self._create_new_session(request)
            if session:
                session_id = session.session_id

        request.state.session = session
        request.state.session_id = session_id

        response = await call_next(request)

        if session and not self._get_session_id(request):
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_id,
                max_age=86400,
                httponly=True,
                secure=not getattr(request.app, 'debug', True),
                samesite="lax"
            )

        return response

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

            return session_service.create_session(session_data)

        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            return None


def get_session(request: Request) -> Optional[SessionData]:
    return getattr(request.state, 'session', None)


def get_session_id(request: Request) -> Optional[str]:
    return getattr(request.state, 'session_id', None)