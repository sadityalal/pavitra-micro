from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from shared import config, setup_logging, get_logger, db
from shared.session_middleware import SecureSessionMiddleware, get_session_id
from .routes import router
import os

setup_logging("product-service")
logger = get_logger(__name__)

app = FastAPI(
    title=f"{config.app_name if config.app_name else 'Product Service'} - Product Service",
    description=config.app_description if config.app_description else "Product management service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0"])
app.add_middleware(SecureSessionMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins if config.cors_origins else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Secure-Session-ID",
        "X-Security-Token",
        "X-CSRF-Token",
        "Cookie"
    ],
    expose_headers=["set-cookie"],
    max_age=600,
)


@app.middleware("http")
async def validate_product_requests(request: Request, call_next):
    user_agent = request.headers.get("user-agent", "").lower()
    suspicious_agents = ["sqlmap", "nikto", "metasploit", "nmap"]
    if any(agent in user_agent for agent in suspicious_agents):
        logger.warning(f"Suspicious user agent blocked: {user_agent}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if request.method in ["POST", "PUT"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith(("application/json", "multipart/form-data")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content type"
            )

    response = await call_next(request)
    return response


@app.middleware("http")
async def secure_cors_headers(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get('origin')
    if origin and config.cors_origins and origin in config.cors_origins:
        response.headers['Access-Control-Allow-Origin'] = origin

    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers[
        'Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-Secure-Session-ID, X-Security-Token, X-CSRF-Token, Cookie'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Max-Age'] = '600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    session_id = get_session_id(request)
    if session_id:
        response.headers['X-Secure-Session-ID'] = session_id

    return response


@app.options("/{path:path}")
async def secure_options_handler(path: str, request: Request):
    origin = request.headers.get('origin')
    response = JSONResponse(content={"method": "OPTIONS"})
    if origin and config.cors_origins and origin in config.cors_origins:
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
        "/api/v1/products/health", "/api/v1/products/site-settings",
        "/api/v1/products/debug/maintenance", "/api/v1/products/debug/settings"
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


app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")
app.include_router(router, prefix="/api/v1/products")


@app.get("/health")
async def health():
    try:
        health_data = db.health_check()
        if health_data.get('status') == 'healthy':
            return {
                "status": "healthy",
                "service": "product",
                "database": "connected",
                "app_name": config.app_name if config.app_name else "Product Service",
                "maintenance_mode": config.maintenance_mode if config.maintenance_mode is not None else False
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
        "maintenance_mode": config.maintenance_mode if config.maintenance_mode is not None else False,
        "timestamp": "updated"
    }


@app.get("/")
async def root():
    return {
        "message": f"{config.app_name if config.app_name else 'Product Service'} - Product Service",
        "version": "1.0.0",
        "environment": "development" if config.debug_mode else "production",
        "maintenance_mode": config.maintenance_mode if config.maintenance_mode is not None else False
    }


if __name__ == "__main__":
    import uvicorn

    port = config.get_service_port('product')
    logger.info(f"Starting Service on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level=config.log_level.lower() if config.log_level else "info",
        access_log=True,
        reload=config.debug_mode if config.debug_mode is not None else True
    )