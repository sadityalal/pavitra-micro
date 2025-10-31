from fastapi import Request, Response
from typing import Optional, Callable
from datetime import datetime
import uuid
from shared import get_logger
from .session_service import session_service, SessionType, SessionData
from .session_models import SessionCreate

logger = get_logger(__name__)


class SessionMiddleware:
    def __init__(self):
        self.session_cookie_name = "session_id"

    async def __call__(self, request: Request, call_next: Callable):
        # Try to get session ID from cookie or header
        session_id = self._get_session_id(request)
        session = None

        if session_id:
            session = session_service.get_session(session_id)

        # Create new session if none exists or existing session is invalid
        if not session:
            session = await self._create_new_session(request)
            if session:
                session_id = session.session_id

        # Attach session to request state
        request.state.session = session
        request.state.session_id = session_id

        # Process the request
        response = await call_next(request)

        # Set session cookie if new session was created
        if session and not self._get_session_id(request):
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_id,
                max_age=86400,  # 24 hours
                httponly=True,
                secure=not request.app.debug,  # Secure in production
                samesite="lax"
            )

        return response

    def _get_session_id(self, request: Request) -> Optional[str]:
        # Try cookie first
        session_id = request.cookies.get(self.session_cookie_name)
        if session_id:
            return session_id

        # Try header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Session "):
            return auth_header[8:]

        return None

    async def _create_new_session(self, request: Request) -> Optional[SessionData]:
        try:
            # Determine session type
            session_type = SessionType.GUEST
            user_id = None
            guest_id = str(uuid.uuid4())

            # Check if user is authenticated via JWT
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
                'ip_address': request.client.host,
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