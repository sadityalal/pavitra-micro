import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from shared import get_logger, redis_client, db
from .session_models import SessionData, SessionType

logger = get_logger(__name__)


class SessionService:
    def __init__(self):
        self.inactivity_timeout = 1200
        self.guest_session_duration = 86400  # 24 hours
        self.user_session_duration = 86400  # 24 hours
        self._redis_session_prefix = "session:"
        self._redis_user_session_prefix = "user_session:"
        self._redis_guest_session_prefix = "guest_session:"

    def generate_session_id(self) -> str:
        return uuid.uuid4().hex

    def _session_key(self, session_id: str) -> str:
        return f"{self._redis_session_prefix}{session_id}"

    def create_session(self, session_data: Dict[str, Any]) -> Optional[SessionData]:
        try:
            session_id = self.generate_session_id()
            now = datetime.utcnow()

            if session_data.get('session_type') == SessionType.USER:
                expires_at = now + timedelta(seconds=self.user_session_duration)
            else:
                expires_at = now + timedelta(seconds=self.guest_session_duration)

            # Ensure cart_items is always a dict
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
                ip_address=session_data.get('ip_address'),
                user_agent=session_data.get('user_agent'),
                expires_at=expires_at
            )

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

            # Store user/guest session mapping
            if session.user_id:
                redis_client.setex(
                    f"{self._redis_user_session_prefix}{session.user_id}",
                    self.user_session_duration,
                    session_id
                )
            elif session.guest_id:
                redis_client.setex(
                    f"{self._redis_guest_session_prefix}{session.guest_id}",
                    self.guest_session_duration,
                    session_id
                )

            logger.info(f"Created {session.session_type.value} session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def get_session(self, session_id: str) -> Optional[SessionData]:
        try:
            if not session_id:
                return None

            key = self._session_key(session_id)
            data = redis_client.get(key)

            if not data:
                return None

            session_dict = json.loads(data)

            # Convert string dates back to datetime objects
            session_dict['created_at'] = datetime.fromisoformat(session_dict['created_at'])
            session_dict['last_activity'] = datetime.fromisoformat(session_dict['last_activity'])
            session_dict['expires_at'] = datetime.fromisoformat(session_dict['expires_at'])

            # Convert session_type string back to enum
            session_type_str = session_dict.get('session_type', 'guest')
            session_dict['session_type'] = SessionType.USER if session_type_str == 'user' else SessionType.GUEST

            # Ensure cart_items is never None
            if session_dict.get('cart_items') is None:
                session_dict['cart_items'] = {}

            session_dict['session_id'] = session_id

            session = SessionData(**session_dict)

            # Update activity timestamp
            self._update_session_activity_only(session_id)

            return session

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def _update_session_activity_only(self, session_id: str) -> bool:
        try:
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

    def migrate_guest_to_user_session(self, guest_session_id: str, user_id: int) -> Optional[SessionData]:
        """Migrate guest session to user session and merge carts"""
        try:
            guest_session = self.get_session(guest_session_id)
            if not guest_session or guest_session.session_type != SessionType.GUEST:
                return None

            # Get existing user session if any
            user_session = self.get_session_by_user_id(user_id)

            # Merge cart items
            merged_cart_items = {}

            # Add user's existing cart items
            if user_session and user_session.cart_items:
                merged_cart_items.update(user_session.cart_items)

            # Add guest cart items, merging quantities for same products
            if guest_session.cart_items:
                for item_key, guest_item in guest_session.cart_items.items():
                    if item_key in merged_cart_items:
                        # Merge quantities for same product
                        merged_cart_items[item_key]['quantity'] += guest_item['quantity']
                    else:
                        # Add new item
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

            # Delete old guest session
            self.delete_session(guest_session_id)

            # Delete old user session if it existed
            if user_session:
                self.delete_session(user_session.session_id)

            logger.info(f"Successfully migrated guest session {guest_session_id} to user {user_id}")
            return new_session

        except Exception as e:
            logger.error(f"Failed to migrate guest session to user: {e}")
            return None

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
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

            success = redis_client.setex(
                key,
                expiry,
                json.dumps(session_dict)
            )

            # Update user/guest mapping if user_id or guest_id changed
            if success and 'user_id' in updates:
                if session.user_id:
                    redis_client.setex(
                        f"{self._redis_user_session_prefix}{session.user_id}",
                        self.user_session_duration,
                        session_id
                    )
            if success and 'guest_id' in updates:
                if session.guest_id:
                    redis_client.setex(
                        f"{self._redis_guest_session_prefix}{session.guest_id}",
                        self.guest_session_duration,
                        session_id
                    )

            return success

        except Exception as e:
            logger.error(f"Failed to update session data {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            # Delete session data
            redis_client.delete(self._session_key(session_id))

            # Delete mappings
            if session.user_id:
                redis_client.delete(f"{self._redis_user_session_prefix}{session.user_id}")
            if session.guest_id:
                redis_client.delete(f"{self._redis_guest_session_prefix}{session.guest_id}")

            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def get_session_by_user_id(self, user_id: int) -> Optional[SessionData]:
        try:
            session_id = redis_client.get(f"{self._redis_user_session_prefix}{user_id}")
            if session_id:
                return self.get_session(session_id)
            return None
        except Exception as e:
            logger.error(f"Failed to get session for user {user_id}: {e}")
            return None

    def validate_and_repair_session(self, session_id: str) -> bool:
        """Validate session data and repair any inconsistencies"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False

            repairs_made = False

            # Repair: Ensure cart_items is never None
            if session.cart_items is None:
                session.cart_items = {}
                repairs_made = True
                logger.info(f"Repaired session {session_id}: cart_items was None")

            # Repair: Ensure session_type is valid
            if session.session_type not in [SessionType.GUEST, SessionType.USER]:
                session.session_type = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: invalid session_type")

            # Repair: Ensure user_id and guest_id are consistent with session_type
            if session.session_type == SessionType.USER and not session.user_id:
                session.session_type = SessionType.GUEST
                repairs_made = True
                logger.info(f"Repaired session {session_id}: user session without user_id")

            if session.session_type == SessionType.GUEST and not session.guest_id:
                session.guest_id = str(uuid.uuid4())
                repairs_made = True
                logger.info(f"Repaired session {session_id}: guest session without guest_id")

            # Save repairs if any were made
            if repairs_made:
                session_dict = session.model_dump()
                session_dict['session_type'] = session_dict['session_type'].value
                session_dict['created_at'] = session_dict['created_at'].isoformat()
                session_dict['last_activity'] = session_dict['last_activity'].isoformat()
                session_dict['expires_at'] = session_dict['expires_at'].isoformat()

                expiry = self.user_session_duration if session.session_type == SessionType.USER else self.guest_session_duration
                key = self._session_key(session_id)

                success = redis_client.setex(
                    key,
                    expiry,
                    json.dumps(session_dict)
                )

                if success:
                    logger.info(f"Successfully repaired session {session_id}")
                else:
                    logger.error(f"Failed to save repaired session {session_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to validate/repair session {session_id}: {e}")
            return False


session_service = SessionService()