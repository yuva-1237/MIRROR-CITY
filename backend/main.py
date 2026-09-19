import os
import sys
import asyncio
import time
import uuid
# Add parent directory to path so database imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("backend")
logger.info("Starting Mirror City Backend...")


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from configs.config import settings
from middleware.rate_limit import RateLimitMiddleware

# Import API routers
from api.auth import router as auth_router
from api.scenarios import router as scenarios_router
from api.simulations import router as simulations_router
from api.reports import router as reports_router
from api.admin import router as admin_router
from api.ws import router as ws_router
from api.incidents import router as incidents_router
from api.live_metrics import router as live_metrics_router
from api.geospatial import router as geospatial_router
from api.evaluations import router as evaluations_router

from services.city_clock import city_clock
from services.ws_manager import ws_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade AI-powered Smart City Digital Twin and Scenario Planner."
)

# CORS configuration
origins_env = os.getenv("ALLOWED_ORIGINS")
if origins_env:
    origins = [x.strip() for x in origins_env.split(",") if x.strip()]
else:
    origins = [
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|172\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rate limiting (per-IP sliding window) --------------------------------
app.add_middleware(RateLimitMiddleware)

# --- Request-ID middleware: attach X-Request-ID to every response ---------
class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = str(uuid.uuid4())[:8]
        # Attach the request ID to request state so structured logger can read it
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

app.add_middleware(RequestIdMiddleware)

# --- Structured Logging middleware: logs requests, user, and execution time -----
class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Try to get user identity if JWT present in Authorization header
        user_id = "anonymous"
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                from configs.security import decode_access_token
                payload = decode_access_token(token)
                if payload:
                    user_id = payload.get("sub", "unknown")
            except Exception:
                pass

        req_id = getattr(request.state, "request_id", "unknown")

        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            logger.info(
                f"Request: ID={req_id} User={user_id} Method={request.method} "
                f"Path={request.url.path} Status={response.status_code} "
                f"Time={process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Unhandled Exception: ID={req_id} Method={request.method} Path={request.url.path} "
                f"Error={str(e)} Time={process_time:.4f}s",
                exc_info=True
            )
            raise e

app.add_middleware(StructuredLoggingMiddleware)

# Mount API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(scenarios_router, prefix=settings.API_V1_STR)
app.include_router(simulations_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(live_metrics_router, prefix=settings.API_V1_STR)
app.include_router(geospatial_router, prefix=settings.API_V1_STR)
app.include_router(evaluations_router, prefix=settings.API_V1_STR)

import time
from sqlalchemy import text
from database.connection import SessionLocal, init_schema
from database.schema import User, Scenario

START_TIME = time.time()

@app.on_event("startup")
def startup_event():
    # Bootstrap dual-mode database schema (SQLite / PostGIS)
    try:
        init_schema()
    except Exception as e:
        logger.error(f"Error initializing schema on startup: {e}")
    # Start the continuous digital twin simulation clock
    city_clock.start()
    # Start background live traffic poller if enabled
    try:
        from real_data_pipeline import start_background_traffic_poller
        start_background_traffic_poller()
    except Exception as e:
        logger.warning(f"Note on starting background traffic poller: {e}")

@app.on_event("shutdown")
def shutdown_event():
    # Stop the continuous digital twin clock
    city_clock.stop()
    # Stop background traffic poller
    try:
        from real_data_pipeline import stop_background_traffic_poller
        stop_background_traffic_poller()
    except Exception as e:
        pass


@app.get("/")
@app.get("/health")
@app.get("/status")
@app.get("/ready")
@app.get("/live")
def health_check():
    """Simple top-level health probe returning detailed status."""
    return compile_detailed_health()

@app.get("/api/health")
@app.get("/api/health/detailed")
def api_health_detailed():
    """Full per-subsystem health breakdown used by the SystemHealthPanel and external monitors."""
    return compile_detailed_health()

def compile_detailed_health() -> dict:
    uptime = int(time.time() - START_TIME)

    # 1. Database check
    db_status = "healthy"
    db_error = None
    user_count, scenario_count = 0, 0
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        user_count = db.query(User).count()
        scenario_count = db.query(Scenario).count()
        db.close()
    except Exception as e:
        db_status = "unreachable"
        db_error = str(e)

    # 2. Redis check
    redis_status = "not_configured"
    redis_url = os.getenv("REDIS_URL") or os.getenv("REDIS_HOST")
    if redis_url:
        try:
            import redis
            r = redis.Redis.from_url(redis_url, socket_timeout=1.0) if "://" in redis_url else redis.Redis(host=redis_url, socket_timeout=1.0)
            if r.ping():
                redis_status = "healthy"
            else:
                redis_status = "unreachable"
        except Exception as re:
            redis_status = f"unreachable: {str(re)}"

    # 3. AI Coordinator status
    ai_status = "active" if city_clock.running else "inactive"
    agent_status = {}
    try:
        if city_clock.coordinator and city_clock.coordinator.live_agents:
            agent_status = {k: "active" for k in city_clock.coordinator.live_agents.keys()}
    except Exception as ae:
        agent_status = {"error": str(ae)}

    # 4. Connected AI Providers
    ai_providers = {
        "gemini": bool(settings.GEMINI_API_KEY.strip()) if settings.GEMINI_API_KEY else False,
        "openai": bool(settings.OPENAI_API_KEY.strip()) if settings.OPENAI_API_KEY else False,
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    }

    # 5. Active services list
    active_services = []
    if city_clock.running:
        active_services.append("city_clock")
    if city_clock.simulator:
        active_services.append("sensor_simulator")
    try:
        from services.weather_service import weather_service
        if weather_service:
            active_services.append("weather_service")
    except Exception:
        pass
    active_services.append("rate_limiter")
    active_services.append("request_id_middleware")

    # Overall status
    overall_status = "healthy"
    if db_status != "healthy":
        overall_status = "degraded"
    if ai_status != "active":
        overall_status = "degraded"

    return {
        "status": overall_status,
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "uptime_seconds": uptime,
        "uptime_human": f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s",
        "components": {
            "api": {
                "status": "healthy",
                "authentication": "configured" if settings.JWT_SECRET else "missing_secret"
            },
            "database": {
                "status": db_status,
                "users_registered": user_count,
                "scenarios_loaded": scenario_count,
                "error": db_error
            },
            "redis": {
                "status": redis_status
            },
            "ai_coordinator": {
                "status": ai_status,
                "agents": agent_status,
                "tick": city_clock.tick_count
            },
            "ai_providers": ai_providers,
            "active_services": active_services,
            "websocket_bus": {
                "status": "active" if len(ws_manager.active_connections) >= 0 else "inactive",
                "active_connections": len(ws_manager.active_connections)
            }
        }
    }

@app.get("/api/ping")
def api_ping():
    return {"pong": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
