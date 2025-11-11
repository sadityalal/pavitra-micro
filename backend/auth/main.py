from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from shared import config, setup_logging, get_logger, db, cleanup_service  # ADD cleanup_service
from shared.session_middleware import SecureSessionMiddleware
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
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"])
app.add_middleware(SecureSessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8082",
        "http://127.0.0.1:8082",
        "http://localhost:80",
        "http://127.0.0.1:80",
        "https://localhost:443",
        "https://127.0.0.1:443",
        "https://localhost",
        "https://127.0.0.1",
        "https://localhost:3000",
        "https://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Session-ID",
        "X-Secure-Session-ID",
        "X-CSRF-Token",
        "Cookie"
    ],
    expose_headers=["set-cookie", "X-Session-ID", "X-Secure-Session-ID"],
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
    response.headers[
        'Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Secure-Session-ID, X-Security-Token, X-CSRF-Token, Cookie'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    session_id = getattr(request.state, 'session_id', None)
    if session_id:
        response.headers['X-Secure-Session-ID'] = session_id
    return response


@app.options("/{path:path}")
async def secure_options_handler(path: str, request: Request):
    origin = request.headers.get('origin')
    response = JSONResponse(content={"method": "OPTIONS"})
    if origin and origin in config.cors_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
        response.headers[
            'Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Secure-Session-ID, X-Security-Token, X-CSRF-Token'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response


@app.middleware("http")
async def maintenance_mode_middleware(request, call_next):
    maintenance_exempt_paths = [
        "/health", "/docs", "/redoc", "/refresh-config",
        "/api/v1/auth/health", "/api/v1/auth/site-settings",
        "/api/v1/auth/debug/maintenance", "/api/v1/auth/debug/settings"
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
        if hasattr(db, 'redis_client'):
            if db.redis_client.ping():
                logger.info("✅ Redis connection verified")
            else:
                logger.error("❌ Redis connection failed")

        # START CLEANUP SERVICE
        cleanup_service.start_cleanup_task()
        logger.info("✅ Cleanup service started")

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
                "maintenance_mode": config.maintenance_mode,
                "session_service": "active"
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
        "maintenance_mode": config.maintenance_mode,
        "session_management": "secure"
    }


@app.get("/debug/cors-config")
async def debug_cors_config():
    config.refresh_cache()
    return {
        "cors_origins": config.cors_origins,
        "cors_origins_type": str(type(config.cors_origins)),
        "cors_origins_raw": str(config.cors_origins),
        "cache_keys": list(config._cache.keys()) if hasattr(config, '_cache') else "No cache"
    }


# ADD NEW DEBUG ENDPOINTS
@app.get("/debug/redis-health")
async def debug_redis_health():
    try:
        memory_info = redis_client.get_memory_info()
        return {
            "redis_connected": redis_client.ping(),
            "memory_info": memory_info,
            "session_count": len(redis_client.keys('secure_session:*')),
            "rate_limit_count": len(redis_client.keys('*rate_limit*'))
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/debug/cleanup-sessions")
async def debug_cleanup_sessions():
    """Manual session cleanup endpoint"""
    try:
        cleaned = session_service.cleanup_expired_sessions()
        return {
            "message": f"Cleaned up {cleaned} expired sessions",
            "cleaned_count": cleaned
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/emergency/cleanup-redis")
async def emergency_redis_cleanup():
    """Emergency cleanup - use when Redis gets corrupted"""
    try:
        cleaned = cleanup_service.emergency_cleanup()
        return {
            "message": f"Emergency cleanup completed - {cleaned} keys deleted",
            "keys_deleted": cleaned
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = config.get_service_port('auth')
    logger.info(f"🚀 Starting Auth Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower(),
        access_log=True,
        reload=config.debug_mode
    )