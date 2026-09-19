import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from database.connection import Base



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="Citizen")  # Citizen, Planner, Government Official, Administrator, Researcher
    api_key = Column(String, unique=True, nullable=True)
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scenarios = relationship("Scenario", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")
    incidents = relationship("Incident", back_populates="reporter")

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String, default="sf", index=True)  # multi-city partitioning: 'sf', 'chennai', 'mumbai', etc.
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    baseline_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="proposed")  # baseline, proposed, active
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User", back_populates="scenarios")
    elements = relationship("MapElement", back_populates="scenario", cascade="all, delete-orphan")
    results = relationship("SimulationResult", back_populates="scenario", cascade="all, delete-orphan")

class MapElement(Base):
    __tablename__ = "map_elements"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    city_code = Column(String, default="sf", index=True)
    type = Column(String, nullable=False)  # hospital, metro, green_space, road_widening, flyover, closure
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=True, index=True)  # explicit spatial index coordinates
    lng = Column(Float, nullable=True, index=True)
    location_geojson = Column(Text, nullable=False)  # GeoJSON string for point, line, or polygon
    radius = Column(Float, default=0.0)  # Area of impact in meters
    capacity = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    status = Column(String, default="proposed")  # proposed, active, resolved

    scenario = relationship("Scenario", back_populates="elements")

class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False)
    metrics_json = Column(Text, nullable=False)  # JSON string of output metrics
    recommendations_json = Column(Text, nullable=False)  # JSON string of AI suggestions
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scenario = relationship("Scenario", back_populates="results")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String, default="sf", index=True)
    type = Column(String, nullable=False)  # accident, pothole, flood, power_cut, crime, road_damage, fire, water_leak
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    lat = Column(Float, nullable=True, index=True)
    lng = Column(Float, nullable=True, index=True)
    location_geojson = Column(Text, nullable=False)  # GeoJSON string for position
    status = Column(String, default="reported")  # reported, verified, resolved
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reporter = relationship("User", back_populates="incidents")

class CityMemory(Base):
    __tablename__ = "city_memory"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, nullable=False)  # traffic, flood, weather, economy, healthcare, etc.
    event_type = Column(String, nullable=False)  # sensor_reading, observation, recommendation, collaboration
    message = Column(Text, nullable=False)
    data_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class LiveMetric(Base):
    __tablename__ = "live_metrics"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String, default="sf", index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metrics_json = Column(Text, nullable=False) # overall average congestion, air quality index, power load, flood level, crowd density

class City(Base):
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

class SpatialNode(Base):
    __tablename__ = "spatial_nodes"

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String(32), index=True, nullable=False)
    osm_id = Column(Integer, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    elevation_m = Column(Float, nullable=True)
    node_type = Column(String(32), nullable=True)

class TrafficObservation(Base):
    __tablename__ = "traffic_observations"
    __table_args__ = (
        UniqueConstraint("city_code", "corridor", "observed_at", name="uq_traffic_obs"),
    )

    id = Column(Integer, primary_key=True, index=True)
    city_code = Column(String(32), index=True, nullable=False)
    corridor = Column(String(64), index=True, nullable=False)
    observed_at = Column(DateTime, index=True, nullable=False)
    speed_kmh = Column(Float, nullable=False)
    congestion_pct = Column(Float, nullable=False)
    source = Column(String(16), nullable=False)          # live_api | calibrated | simulated
    raw_payload = Column(Text, nullable=True)


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(64), nullable=False)
    baseline_name = Column(String(64), nullable=False)
    trained_window_start = Column(DateTime, nullable=False)
    trained_window_end = Column(DateTime, nullable=False)
    evaluated_window_end = Column(DateTime, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    config_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def query_elements_in_radius(db, lat: float, lng: float, radius_m: float, city_code: str = None) -> list:
    """
    Spatial radius query.
    Uses PostGIS ST_DWithin when running on PostgreSQL;
    Falls back to Haversine bounding distance when running on SQLite.
    """
    from database.connection import is_postgres
    import json
    from gis.spatial import haversine_distance

    if is_postgres:
        from sqlalchemy import text
        sql = """
        SELECT id, scenario_id, type, name, lat, lng, radius, capacity, cost, status
        FROM map_elements
        WHERE (:city_code IS NULL OR city_code = :city_code)
          AND lat IS NOT NULL AND lng IS NOT NULL
          AND ST_DWithin(
              ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              :radius_m
          )
        """
        rows = db.execute(text(sql), {"lat": lat, "lng": lng, "radius_m": radius_m, "city_code": city_code}).fetchall()
        return rows

    # SQLite Fallback
    query = db.query(MapElement)
    if city_code:
        query = query.filter(MapElement.city_code == city_code)
    all_elems = query.all()

    matched = []
    for elem in all_elems:
        elem_lat = elem.lat
        elem_lng = elem.lng
        if elem_lat is None and elem.location_geojson:
            try:
                g = json.loads(elem.location_geojson)
                if g.get("type") == "Point" and len(g.get("coordinates", [])) >= 2:
                    elem_lng, elem_lat = g["coordinates"][0], g["coordinates"][1]
            except Exception:
                pass

        if elem_lat is not None and elem_lng is not None:
            dist = haversine_distance(lat, lng, elem_lat, elem_lng)
            if dist <= radius_m:
                matched.append(elem)
    return matched
