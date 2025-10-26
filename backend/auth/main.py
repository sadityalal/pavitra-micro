from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from shared import config, setup_logging, get_logger, db
from .routes import router

setup_logging("auth-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name} - Auth Service",
    description=config.app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database connection during startup"""
    logger.info("🔄 Initializing database connection on startup...")
    try:
        db.initialize()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

app.include_router(router, prefix="/api/v1/auth")

@app.get("/health")
async def health():
    try:
        health_data = db.health_check()
        if health_data.get('status') == 'healthy':
            return {
                "status": "healthy",
                "service": "auth",
                "database": "connected",
                "app_name": config.app_name
            }
        else:
            logger.error(f"Database health check failed: {health_data.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy - database connection failed"
            )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/")
async def root():
    return {
        "message": f"{config.app_name} - Auth Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production"
    }

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('auth')
    logger.info(f"🚀 Starting Auth Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )