from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from shared.config import config
from .routes import router

# Setup logging with database-driven log level
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=f"{config.app_name} - Auth Service",
    description=config.app_description,
    version="1.0.0"
)

# CORS from database config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": f"{config.app_name} - Auth Service",
        "environment": "production",
        "debug_mode": config.debug_mode
    }

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('auth')
    logger.info(f"Starting Auth Service on port {port} with log level: {config.log_level}")
    uvicorn.run(app, host="0.0.0.0", port=port)
