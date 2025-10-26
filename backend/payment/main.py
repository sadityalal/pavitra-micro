from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from shared import config, setup_logging, get_logger, db
from .routes import router

setup_logging("payment-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name} - Payment Service",
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

@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    maintenance_exempt_paths = [
        "/health", "/docs", "/redoc", "/refresh-config",
        "/api/v1/payments/health", "/api/v1/payments/webhook",
        "/api/v1/payments/debug/maintenance", "/api/v1/payments/debug/settings"
    ]
    
    if any(request.url.path.startswith(path) for path in maintenance_exempt_paths):
        response = await call_next(request)
        return response
    
    config.refresh_cache()
    logger.info(f"DEBUG Middleware: maintenance_mode={config.maintenance_mode}, type={type(config.maintenance_mode)}")
    
    if config.maintenance_mode:
        logger.warning(f"Maintenance mode blocking request to: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is under maintenance. Please try again later."
        )
    
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("🔄 Initializing database connection on startup...")
    try:
        db.initialize()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

app.include_router(router, prefix="/api/v1/payments")

@app.get("/health")
async def health():
    try:
        health_data = db.health_check()
        if health_data.get('status') == 'healthy':
            return {
                "status": "healthy",
                "service": "payment",
                "database": "connected",
                "app_name": config.app_name,
                "maintenance_mode": config.maintenance_mode
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

@app.post("/refresh-config")
async def refresh_config():
    config.refresh_cache()
    return {
        "message": "Configuration cache refreshed",
        "maintenance_mode": config.maintenance_mode,
        "timestamp": "updated"
    }

@app.get("/")
async def root():
    return {
        "message": f"{config.app_name} - Payment Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production",
        "maintenance_mode": config.maintenance_mode
    }

if __name__ == "__main__":
    import uvicorn
    port = config.get_service_port('payment')
    logger.info(f"🚀 Starting Payment Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower()
    )
