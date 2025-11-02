import threading
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from shared import config, setup_logging, get_logger, db
from shared.session_middleware import SessionMiddleware
from .business_routes import router as business_router
from .message_consumer import notification_consumer
from .routes import router

setup_logging("notification-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name} - Notification Service",
    description=config.app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Need to fix this hardcoded urls from config.py and site-settings table
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
app.add_middleware(SessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ],
    max_age=600,
)

@app.middleware("http")
async def secure_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get('origin')
    if origin and origin in config.cors_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
    elif config.cors_origins and config.cors_origins[0] == '*':
        response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Guest-Id, Cookie'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.options("/{path:path}")
async def secure_options_handler(path: str, request: Request):
    origin = request.headers.get('origin')
    response = JSONResponse(content={"method": "OPTIONS"})
    if origin and origin in config.cors_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    maintenance_exempt_paths = [
        "/health", "/docs", "/redoc", "/refresh-config",
        "/api/v1/notifications/health", "/api/v1/notifications/debug/test"
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
        
        # Start message consumer in background thread
        def start_consumer():
            notification_consumer.start_consuming()
        
        consumer_thread = threading.Thread(target=start_consumer, daemon=True)
        consumer_thread.start()
        logger.info("✅ Notification consumer started in background thread")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

app.include_router(router, prefix="/api/v1/notifications")
app.include_router(business_router, prefix="/api/v1/notifications")

@app.get("/health")
async def health():
    try:
        health_data = db.health_check()
        if health_data.get('status') == 'healthy':
            return {
                "status": "healthy",
                "service": "notification",
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
        "message": f"{config.app_name} - Notification Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production",
        "maintenance_mode": config.maintenance_mode
    }


if __name__ == "__main__":
    import uvicorn

    port = config.get_service_port('notification')  # or 'product', 'user'
    logger.info(f"🚀 Starting Service on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        access_log=True,
        reload=config.debug_mode  # Auto-reload in debug mode
    )
