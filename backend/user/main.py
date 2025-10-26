from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from shared import config, setup_logging, get_logger, db
from .routes import router

# Setup logging
setup_logging("user-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name} - User Service",
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
    # DEBUG: Log what we're checking
    logger.info(f"DEBUG Middleware: maintenance_mode={config.maintenance_mode}, path={request.url.path}")

    if config.maintenance_mode and request.url.path not in ["/health", "/docs", "/redoc"]:
        logger.warning(f"Maintenance mode blocking: {request.url.path}")
        raise HTTPException(
            status_code=503,
            detail="Service is under maintenance"
        )
    response = await call_next(request)
    return response

app.include_router(router, prefix="/api/v1/users")

@app.get("/health")
async def health():
    try:
        db.health_check()
        app_name = config.app_name

        return {
            "status": "healthy",
            "service": "user",
            "database": "connected",
            "app_name": app_name,
            "maintenance_mode": config.maintenance_mode,
            "maintenance_mode_type": str(type(config.maintenance_mode))
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unhealthy"
        )

# ADD THIS ENDPOINT TO REFRESH CONFIG CACHE
@app.post("/refresh-config")
async def refresh_config():
    """Force refresh configuration cache"""
    config.refresh_cache()
    return {
        "message": "Configuration cache refreshed",
        "maintenance_mode": config.maintenance_mode,
        "maintenance_mode_type": str(type(config.maintenance_mode))
    }

@app.get("/")
async def root():
    return {
        "message": f"{config.app_name} - User Service",
        "version": "1.0.0",
        "environment": config.debug_mode and "development" or "production",
        "maintenance_mode": config.maintenance_mode
    }

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('user')
    logger.info(f"Starting User Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )