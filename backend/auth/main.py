from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from shared import config, setup_logging, get_logger, db
from .routes import router

# Setup logging
setup_logging("auth-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name} - Auth Service",
    description=config.app_description,
    version="1.0.0",
    docs_url="/docs" if not config.maintenance_mode else None,
    redoc_url="/redoc" if not config.maintenance_mode else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Maintenance mode check
@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    if config.maintenance_mode and request.url.path not in ["/health", "/docs", "/redoc"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is under maintenance"
        )
    response = await call_next(request)
    return response

app.include_router(router, prefix="/api/v1/auth")

@app.get("/health")
async def health():
    try:
        # Check database connection
        db.health_check()
        
        # Check if service can access site_settings
        app_name = config.app_name
        
        return {
            "status": "healthy",
            "service": "auth",
            "database": "connected",
            "app_name": app_name
        }
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
        "environment": config.debug_mode and "development" or "production"
    }

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('auth')
    logger.info(f"Starting Auth Service on port {port}")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level=config.log_level.lower()
    )
