import bcrypt
import re
from typing import Tuple
import logging
from shared.utils.logger import get_auth_logger

logger = get_auth_logger()

class PasswordSecurity:
    @staticmethod
    def hash_password(password: str) -> str:
        try:
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character"
        
        common_passwords = {'password', '12345678', 'qwerty', 'admin', 'letmein'}
        if password.lower() in common_passwords:
            return False, "Password is too common"
        
        return True, "Password is secure"
