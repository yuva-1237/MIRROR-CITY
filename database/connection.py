"""
Dual-mode database layer: SQLite (dev) / PostGIS (production).

This module is the ONLY place that knows which database is running.
Every service and API route consumes `engine`, `SessionLocal`, and `get_db`
so switching DATABASE_MODE in .env changes the whole app with zero code edits.

PostGIS mode gives you:
  - Geometry(POINT, 4326) columns + GiST spatial indexes
  - ST_DWithin radial queries (replaces Python haversine loops)
  - city_code partitioning via composite indexes (multi-city twins)

SQLite mode keeps the identical table/column contract using plain lat/lng
floats, so the ORM code path is the same. Spatial queries route through
`spatial_within_radius`, which dispatches ST_DWithin or haversine.
"""

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from configs.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
IS_POSTGIS = settings.DATABASE_MODE == "postgis"
# Backward-compatibility alias
is_postgres = IS_POSTGIS


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------
if IS_POSTGIS:
    engine = create_engine(
        settings.POSTGIS_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )
else:
    # Use SQLITE_PATH or fallback to DATABASE_PATH/DATABASE_URL
    sqlite_target = settings.SQLITE_PATH
    if not sqlite_target and settings.DATABASE_PATH:
        sqlite_target = settings.DATABASE_PATH
    
    sqlite_url = f"sqlite:///{sqlite_target}" if not sqlite_target.startswith("sqlite:") else sqlite_target
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
    )


@event.listens_for(engine, "connect")
def _on_connect(dbapi_conn, _record):
    """Per-connection setup. PostGIS: make sure the extension exists."""
    if IS_POSTGIS:
        try:
            cur = dbapi_conn.cursor()
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            cur.close()
        except Exception as e:
            logger.warning(f"PostGIS extension initialization notice: {e}")


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Schema bootstrap (idempotent).
# Maps to schema.py models; this DDL shows the spatial contract both modes honour.
# ---------------------------------------------------------------------------
POSTGIS_DDL = """
CREATE TABLE IF NOT EXISTS cities (
    id SERIAL PRIMARY KEY,
    city_code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    center GEOMETRY(POINT, 4326) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cities_center ON cities USING GIST (center);

CREATE TABLE IF NOT EXISTS spatial_nodes (
    id BIGSERIAL PRIMARY KEY,
    city_code VARCHAR(32) NOT NULL,
    osm_id BIGINT,
    geom GEOMETRY(POINT, 4326) NOT NULL,
    elevation_m REAL,
    node_type VARCHAR(32)
);
CREATE INDEX IF NOT EXISTS idx_nodes_geom ON spatial_nodes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_nodes_city ON spatial_nodes (city_code, id);

CREATE TABLE IF NOT EXISTS traffic_observations (
    id BIGSERIAL PRIMARY KEY,
    city_code VARCHAR(32) NOT NULL,
    corridor VARCHAR(64) NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    speed_kmh REAL NOT NULL,
    congestion_pct REAL NOT NULL,
    source VARCHAR(16) NOT NULL,          -- live_api | calibrated | simulated
    raw_payload JSONB,
    CONSTRAINT uq_traffic_obs_pg UNIQUE (city_code, corridor, observed_at)
);
CREATE INDEX IF NOT EXISTS idx_traffic_city_time ON traffic_observations (city_code, observed_at DESC);

CREATE TABLE IF NOT EXISTS eval_runs (
    id BIGSERIAL PRIMARY KEY,
    model_name VARCHAR(64) NOT NULL,
    baseline_name VARCHAR(64) NOT NULL,
    trained_window_start TIMESTAMPTZ NOT NULL,
    trained_window_end TIMESTAMPTZ NOT NULL,
    evaluated_window_end TIMESTAMPTZ NOT NULL,   -- must be > trained_window_end (no leakage)
    mae REAL NOT NULL,
    rmse REAL NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""

SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(128) NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS spatial_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_code VARCHAR(32) NOT NULL,
    osm_id INTEGER,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    elevation_m REAL,
    node_type VARCHAR(32)
);
CREATE INDEX IF NOT EXISTS idx_nodes_city ON spatial_nodes (city_code, id);
CREATE TABLE IF NOT EXISTS traffic_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_code VARCHAR(32) NOT NULL,
    corridor VARCHAR(64) NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    speed_kmh REAL NOT NULL,
    congestion_pct REAL NOT NULL,
    source VARCHAR(16) NOT NULL,
    raw_payload TEXT,
    CONSTRAINT uq_traffic_obs_sqlite UNIQUE (city_code, corridor, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_traffic_city_time ON traffic_observations (city_code, observed_at DESC);
CREATE TABLE IF NOT EXISTS eval_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name VARCHAR(64) NOT NULL,
    baseline_name VARCHAR(64) NOT NULL,
    trained_window_start TIMESTAMP NOT NULL,
    trained_window_end TIMESTAMP NOT NULL,
    evaluated_window_end TIMESTAMP NOT NULL,
    mae REAL NOT NULL,
    rmse REAL NOT NULL,
    config_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_schema() -> None:
    """Idempotent bootstrap. Called from seed.py and on app startup."""
    with engine.begin() as conn:
        for stmt in (POSTGIS_DDL if IS_POSTGIS else SQLITE_DDL).split(";"):
            if stmt.strip():
                conn.execute(text(stmt))
    
    # Also ensure all SQLAlchemy ORM models (users, scenarios, etc.) are registered
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database schema initialized in {settings.DATABASE_MODE} mode.")


# Backward-compatibility alias
def init_spatial_db() -> None:
    """Alias for init_schema() for existing callers."""
    init_schema()


# ---------------------------------------------------------------------------
# Unified spatial query — same signature, different physics per mode
# ---------------------------------------------------------------------------
def spatial_within_radius(
    session: Session,
    city_code: str,
    lat: float,
    lng: float,
    radius_m: float,
    limit: int = 500,
):
    """Return nodes within radius_m of (lat, lng).

    PostGIS: ST_DWithin on the geometry index (fast at city scale).
    SQLite: haversine fallback (fine for dev-sized graphs).
    """
    if IS_POSTGIS:
        return session.execute(
            text("""
                SELECT id, ST_Y(geom) AS lat, ST_X(geom) AS lng, elevation_m, node_type
                FROM spatial_nodes
                WHERE city_code = :city
                  AND ST_DWithin(geom::geography,
                                 ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                                 :radius)
                LIMIT :limit
            """),
            {"city": city_code, "lat": lat, "lng": lng, "radius": radius_m, "limit": limit},
        ).mappings().all()

    from math import asin, cos, radians, sin, sqrt

    rows = session.execute(
        text("SELECT id, lat, lng, elevation_m, node_type FROM spatial_nodes WHERE city_code = :city"),
        {"city": city_code},
    ).mappings().all()

    def _hav(r):
        dlat, dlng = radians(r["lat"] - lat), radians(r["lng"] - lng)
        a = sin(dlat / 2) ** 2 + cos(radians(lat)) * cos(radians(r["lat"])) * sin(dlng / 2) ** 2
        return 2 * 6371000 * asin(sqrt(a))

    return [r for r in rows if _hav(r) <= radius_m][:limit]


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
