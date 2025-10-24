import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime

sys.path.append('/app')
from shared.utils.config import config
from shared.database.database import db
from shared.utils.logger import get_notification_logger
from shared.security.role_checker import allow_admin, allow_authenticated

logger = get_notification_logger()

app = FastAPI(
    title="Notification Service - Pavitra Trading",
    description="Email and Notification Service",
    version="1.0.0"
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
    template_id: Optional[str] = None

class SMSNotification(BaseModel):
    to: str
    message: str

class PushNotification(BaseModel):
    user_id: int
    title: str
    message: str
    data: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "Notification Service - Pavitra Trading", "environment": config.app_env}

@app.get("/health")
async def health():
    try:
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM newsletter_subscriptions")
        subscription_count = cursor.fetchone()[0]
        cursor.close()
        connection.close()
        
        return {
            "status": "healthy",
            "service": "notification",
            "environment": config.app_env,
            "subscriptions_count": subscription_count
        }
    except Error as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "notification",
            "environment": config.app_env
        }

@app.post("/send-email")
async def send_email(
    notification: EmailNotification,
    payload: dict = Depends(allow_authenticated)
):
    try:
        # Simulate email sending
        # In production, integrate with SMTP service like SendGrid, AWS SES
        logger.info(f"Email sent to {notification.to}: {notification.subject}")
        
        # Log the notification
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO notification_logs (type, recipient, subject, message, status)
            VALUES (%s, %s, %s, %s, %s)
        """, ("email", notification.to, notification.subject, notification.message, "sent"))
        connection.commit()
        connection.close()
        
        return {
            "message": "Email sent successfully",
            "to": notification.to,
            "subject": notification.subject
        }
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

@app.post("/send-sms")
async def send_sms(
    notification: SMSNotification,
    payload: dict = Depends(allow_authenticated)
):
    try:
        # Simulate SMS sending
        # In production, integrate with SMS service like Twilio, MSG91
        logger.info(f"SMS sent to {notification.to}: {notification.message}")
        
        # Log the notification
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO notification_logs (type, recipient, message, status)
            VALUES (%s, %s, %s, %s)
        """, ("sms", notification.to, notification.message, "sent"))
        connection.commit()
        connection.close()
        
        return {
            "message": "SMS sent successfully",
            "to": notification.to
        }
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send SMS")

@app.post("/order-confirmation/{order_id}")
async def send_order_confirmation(
    order_id: int,
    payload: dict = Depends(allow_authenticated)
):
    connection = None
    try:
        user_id = int(payload.get("sub"))
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get order details
        cursor.execute("""
            SELECT o.*, u.email, u.first_name, u.phone
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s AND o.user_id = %s
        """, (order_id, user_id))
        
        order = cursor.fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Send email confirmation
        email_subject = f"Order Confirmation - {order['order_number']}"
        email_message = f"""
        Dear {order['first_name']},
        
        Thank you for your order! Your order has been confirmed.
        
        Order Details:
        - Order Number: {order['order_number']}
        - Total Amount: ₹{order['total_amount']}
        - Status: {order['status']}
        
        We will notify you when your order is shipped.
        
        Thank you for shopping with Pavitra Trading!
        """
        
        # Simulate sending email
        logger.info(f"Order confirmation email sent for order: {order['order_number']}")
        
        # Send SMS confirmation
        sms_message = f"Your order {order['order_number']} is confirmed. Amount: ₹{order['total_amount']}. Thank you!"
        logger.info(f"Order confirmation SMS sent for order: {order['order_number']}")
        
        return {
            "message": "Order confirmation sent successfully",
            "order_number": order['order_number'],
            "email_sent": True,
            "sms_sent": True
        }
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

@app.post("/admin/bulk-email", dependencies=[Depends(allow_admin)])
async def send_bulk_email(
    emails: List[str] = Body(...),
    subject: str = Body(...),
    message: str = Body(...),
    payload: dict = Depends(allow_admin)
):
    try:
        admin_id = payload.get("sub")
        
        # Simulate bulk email sending
        for email in emails:
            logger.info(f"Bulk email sent to {email}: {subject}")
        
        logger.info(f"Bulk email sent to {len(emails)} recipients by admin {admin_id}")
        
        return {
            "message": f"Bulk email sent to {len(emails)} recipients",
            "recipients_count": len(emails)
        }
    except Exception as e:
        logger.error(f"Bulk email sending failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to send bulk email")

@app.get("/admin/notification-logs", dependencies=[Depends(allow_admin)])
async def get_notification_logs(
    skip: int = 0,
    limit: int = 50,
    notification_type: Optional[str] = None
):
    connection = None
    try:
        connection = db.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM notification_logs"
        params = []
        
        if notification_type:
            query += " WHERE type = %s"
            params.append(notification_type)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        logs = cursor.fetchall()
        
        return logs
    except Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('NOTIFICATION')
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
