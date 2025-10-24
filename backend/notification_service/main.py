from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging
from shared.utils.config import config
from shared.database.database import db
import mysql.connector
from mysql.connector import Error

logging.basicConfig(level=getattr(logging, config.log_level))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Notification Service",
    debug=config.app_debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EmailNotification(BaseModel):
    to: str
    subject: str
    message: str


@app.get("/")
async def root():
    return {"message": "Notification Service is running!", "environment": config.app_env}


@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "service": "notification",
            "environment": config.app_env,
            "users_count": user_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "notification",
            "environment": config.app_env
        }


@app.post("/send-email")
async def send_email(notification: EmailNotification):
    try:
        # Log email sending (in production, integrate with actual email service)
        logger.info(f"Sending email to {notification.to}: {notification.subject}")

        return {
            "message": "Email sent successfully",
            "to": notification.to,
            "environment": config.app_env
        }
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv('PORT', config.get_service_port('NOTIFICATION')))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        workers=2
    )