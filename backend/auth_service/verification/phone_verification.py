import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt

# In production, use Twilio or similar service
# from twilio.rest import Client

logger = logging.getLogger(__name__)

class PhoneVerification:
    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        # In development, we'll simulate SMS sending
        self.simulate_sms = True
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    def generate_verification_token(self, phone: str, code: str, secret_key: str, expiry_minutes: int = 10) -> str:
        """Generate secure phone verification token"""
        token_data = {
            "phone": phone,
            "code": code,  # Hashed code in production
            "type": "phone_verification",
            "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)
        }
        return jwt.encode(token_data, secret_key, algorithm="HS256")
    
    def send_verification_sms(self, phone: str, code: str) -> bool:
        """Send verification SMS"""
        try:
            if self.simulate_sms:
                # In development, log the code instead of sending SMS
                logger.info(f"SMS verification code for {phone}: {code}")
                return True
            
            # Production: Use Twilio
            # client = Client(self.account_sid, self.auth_token)
            # message = client.messages.create(
            #     body=f"Your Pavitra Trading verification code is: {code}",
            #     from_=self.phone_number,
            #     to=phone
            # )
            # return message.sid is not None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {str(e)}")
            return False
    
    def verify_code(self, token: str, entered_code: str, secret_key: str) -> Tuple[bool, Optional[str]]:
        """Verify phone verification code"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            
            if payload.get("type") != "phone_verification":
                return False, None
            
            # In production, compare hashed codes
            if payload.get("code") != entered_code:
                return False, None
            
            return True, payload.get("phone")
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid phone verification token: {str(e)}")
            return False, None
