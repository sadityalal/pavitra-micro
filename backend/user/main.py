from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from shared import config, setup_logging, get_logger, db
from shared.session_middleware import SessionMiddleware
from .notification_routes import router as notification_router
from .routes import router

setup_logging("user-service")
logger = get_logger(__name__)
app = FastAPI(
    title=f"{config.app_name} - User Service",
    description=config.app_description,
    version="1.0.0",
    docs_url="/docs" if not config.maintenance_mode else None,
    redoc_url="/redoc" if not config.maintenance_mode else None
)
# Need to fix this hardcoded urls from config.py and site-settings table
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
app.add_middleware(SessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,  # Make sure this includes your frontend URL
    allow_credentials=True,  # This is crucial
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Guest-Id",  # Add this if you're using guest IDs
        "Cookie"  # Allow cookie headers
    ],
    expose_headers=["set-cookie"],  # Important for session cookies
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

# Notification
app.include_router(notification_router, prefix="/api/v1/users")

@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    # Skip maintenance check for health endpoints and docs
    maintenance_exempt_paths = [
        "/health", "/docs", "/redoc", "/refresh-config", 
        "/api/v1/users/health", "/api/v1/users/debug/test"
    ]
    
    if any(request.url.path.startswith(path) for path in maintenance_exempt_paths):
        response = await call_next(request)
        return response
    
    # Check maintenance mode with fresh config
    config.refresh_cache()
    if config.maintenance_mode:
        logger.warning(f"Maintenance mode blocking request to: {request.url.path}")
        raise HTTPException(
            status_code=503,
            detail="Service is under maintenance. Please try again later."
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
            "environment": "development" if config.debug_mode else "production"
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
    config.refresh_cache()
    return {
        "message": "Configuration cache refreshed",
        "maintenance_mode": config.maintenance_mode,
        "timestamp": "updated"
    }

@app.get("/")
async def root():
    return {
        "message": f"{config.app_name} - User Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production",
        "maintenance_mode": config.maintenance_mode
    }


if __name__ == "__main__":
    import uvicorn

    port = config.get_service_port('auth')  # or 'product', 'user'
    logger.info(f"🚀 Starting Service on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        access_log=True,
        reload=config.debug_mode  # Auto-reload in debug mode
    )