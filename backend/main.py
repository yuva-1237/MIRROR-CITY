import os
import sys
import asyncio
import time
import uuid
# Add parent directory to path so database imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

from services.city_clock import city_clock
from services.ws_manager import ws_manager

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise-grade AI-powered Smart City Digital Twin and Scenario Planner."
)

# CORS configuration
origins = [
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Alternative Next.js port
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response

app.add_middleware(RequestIdMiddleware)

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

import time
from database.connection import SessionLocal
from database.schema import User, Scenario

START_TIME = time.time()

@app.on_event("startup")
def startup_event():
    # Start the continuous digital twin simulation clock
    city_clock.start()

@app.on_event("shutdown")
def shutdown_event():
    # Stop the continuous digital twin clock
    city_clock.stop()

@app.get("/")
@app.get("/health")
def health_check():
    # Simple top-level health probe
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        db_status = "degraded"
        
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "live_simulation": "active" if city_clock.running else "inactive",
        "uptime_seconds": int(time.time() - START_TIME)
    }

@app.get("/api/health")
def api_health_check():
    # Detailed diagnostic health probe
    db_status = "healthy"
    user_count = 0
    scenario_count = 0
    db_error = None
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        user_count = db.query(User).count()
        scenario_count = db.query(Scenario).count()
        db.close()
    except Exception as e:
        db_status = "unreachable"
        db_error = str(e)

    # Inspect AI coordinator agents
    agent_status = {}
    try:
        from services.city_clock import city_clock
        if city_clock.coordinator and city_clock.coordinator.live_agents:
            agent_status = {
                k: "loaded" for k in city_clock.coordinator.live_agents.keys()
            }
    except Exception as ae:
        agent_status = {"error": str(ae)}

    return {
        "status": "healthy" if db_status == "healthy" and not db_error else "unhealthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "uptime_seconds": int(time.time() - START_TIME),
        "components": {
            "database": {
                "status": db_status,
                "users_registered": user_count,
                "scenarios_loaded": scenario_count,
                "error": db_error
            },
            "ai_coordinator": {
                "status": "active" if city_clock.running else "inactive",
                "agents": agent_status
            },
            "websocket_bus": {
                "active_connections": len(ws_manager.active_connections)
            }
        }
    }

@app.get("/api/health/detailed")
def api_health_detailed():
    """Full per-subsystem health breakdown used by SystemHealthPanel in the UI."""
    uptime = int(time.time() - START_TIME)

    # Database
    db_status = "healthy"
    user_count, scenario_count, db_error = 0, 0, None
    try:
        db = SessionLocal()
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        user_count     = db.query(User).count()
        scenario_count = db.query(Scenario).count()
        db.close()
    except Exception as e:
        db_status = "unreachable"
        db_error  = str(e)

    # AI agents
    agent_status: dict = {}
    anomaly_count = 0
    try:
        if city_clock.coordinator and city_clock.coordinator.live_agents:
            agent_status = {k: "active" for k in city_clock.coordinator.live_agents.keys()}
    except Exception as ae:
        agent_status = {"error": str(ae)}

    # Data quality from last tick (if available)
    weather_source = "unknown"
    try:
        from services.weather_service import weather_service
        weather_source = "live_api" if weather_service.api_key and not weather_service._circuit_open else "simulation"
    except Exception:
        pass

    ws_count = len(ws_manager.active_connections)

    overall = "healthy"
    if db_status != "healthy":
        overall = "degraded"
    if not city_clock.running:
        overall = "degraded"

    return {
        "status":         overall,
        "uptime_seconds": uptime,
        "uptime_human":   f"{uptime // 3600}h {(uptime % 3600) // 60}m {uptime % 60}s",
        "components": {
            "database": {
                "status":            db_status,
                "users_registered":  user_count,
                "scenarios_loaded":  scenario_count,
                "error":             db_error,
            },
            "ai_coordinator": {
                "status": "active" if city_clock.running else "inactive",
                "agents": agent_status,
                "tick":   city_clock.tick_count,
            },
            "websocket_bus": {
                "status":             "active" if ws_count >= 0 else "inactive",
                "active_connections": ws_count,
            },
            "weather_service": {
                "status": weather_source,
                "circuit_breaker": "open" if getattr(
                    __import__('services.weather_service', fromlist=['weather_service']).weather_service,
                    '_circuit_open', False
                ) else "closed",
            },
            "rate_limiter": {
                "status": "active",
            },
        }
    }

@app.get("/api/ping")
def api_ping():
    return {"pong": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
