from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notification Service")

class EmailNotification(BaseModel):
    to: str
    subject: str
    message: str

@app.get("/")
async def root():
    return {"message": "Notification Service is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification"}

@app.post("/send-email")
async def send_email(notification: EmailNotification):
    logger.info(f"Sending email to {notification.to}")
    return {"message": "Email sent successfully", "to": notification.to}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
