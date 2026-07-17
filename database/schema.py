import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="Citizen")  # Citizen, Planner, Government Official, Administrator, Researcher
    api_key = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scenarios = relationship("Scenario", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")
    incidents = relationship("Incident", back_populates="reporter")

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
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
    type = Column(String, nullable=False)  # hospital, metro, green_space, road_widening, flyover, closure
    name = Column(String, nullable=False)
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
    type = Column(String, nullable=False)  # accident, pothole, flood, power_cut, crime, road_damage, fire, water_leak
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
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
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    metrics_json = Column(Text, nullable=False) # overall average congestion, air quality index, power load, flood level, crowd density
