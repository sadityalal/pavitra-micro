import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt

logger = logging.getLogger(__name__)

class EmailVerification:
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
    
    def generate_verification_token(self, email: str, secret_key: str, expiry_minutes: int = 60) -> str:
        """Generate secure email verification token"""
        token_data = {
            "email": email,
            "type": "email_verification",
            "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16)  # Unique token ID
        }
        return jwt.encode(token_data, secret_key, algorithm="HS256")
    
    def verify_token(self, token: str, secret_key: str) -> Optional[str]:
        """Verify email verification token"""
        try:
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            if payload.get("type") != "email_verification":
                return None
            return payload.get("email")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid verification token: {str(e)}")
            return None
    
    def send_verification_email(self, email: str, verification_url: str) -> bool:
        """Send verification email securely"""
        try:
            # Create message
            msg = MimeMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = email
            msg["Subject"] = "Verify Your Email - Pavitra Trading"
            
            # Email body
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; 
                             color: white; text-decoration: none; border-radius: 4px; }}
                    .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; 
                             font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Verify Your Email Address</h2>
                    <p>Thank you for registering with Pavitra Trading!</p>
                    <p>Please click the button below to verify your email address:</p>
                    <p>
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>If the button doesn't work, copy and paste this link in your browser:</p>
                    <p><code>{verification_url}</code></p>
                    <p>This verification link will expire in 1 hour.</p>
                    <div class="footer">
                        <p>If you didn't create an account with Pavitra Trading, please ignore this email.</p>
                        <p>&copy; 2024 Pavitra Trading. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Verification email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email after successful verification"""
        try:
            msg = MimeMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = email
            msg["Subject"] = "Welcome to Pavitra Trading!"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <body>
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Welcome to Pavitra Trading, {name}!</h2>
                    <p>Your email has been successfully verified.</p>
                    <p>You can now enjoy all the features of our platform:</p>
                    <ul>
                        <li>Shop from thousands of products</li>
                        <li>Track your orders</li>
                        <li>Save items to your wishlist</li>
                        <li>Get exclusive deals and offers</li>
                    </ul>
                    <p>Start shopping now: <a href="https://pavitra-trading.com">Visit Store</a></p>
                    <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p>Happy Shopping!<br>The Pavitra Trading Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MimeText(html, "html"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            logger.info(f"Welcome email sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {str(e)}")
            return False
