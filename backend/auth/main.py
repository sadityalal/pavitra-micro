from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
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
# Need to fix this hardcoded urls from config.py and site-settings table
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
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
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
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
    # Skip maintenance check for health endpoints and docs
    maintenance_exempt_paths = [
        "/health", "/docs", "/redoc", "/refresh-config",
        "/api/v1/auth/health", "/api/v1/auth/site-settings",
        "/api/v1/auth/debug/maintenance", "/api/v1/auth/debug/settings"
    ]
    
    if any(request.url.path.startswith(path) for path in maintenance_exempt_paths):
        response = await call_next(request)
        return response
    
    # Check maintenance mode with fresh config
    config.refresh_cache()
    
    # DEBUG: Log the actual value and type
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
        "message": f"{config.app_name} - Auth Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production",
        "maintenance_mode": config.maintenance_mode
    }
## DEBUG
@app.get("/debug/cors-config")
async def debug_cors_config():
    config.refresh_cache()  # Force refresh
    return {
        "cors_origins": config.cors_origins,
        "cors_origins_type": str(type(config.cors_origins)),
        "cors_origins_raw": str(config.cors_origins),
        "cache_keys": list(config._cache.keys()) if hasattr(config, '_cache') else "No cache"
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
