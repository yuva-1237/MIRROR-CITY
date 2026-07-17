import asyncio
import datetime
import json
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database.connection import get_db
from database.schema import Incident, User, AuditLog
from api.auth import get_current_user, require_role
from services.ws_manager import ws_manager
from services.data_validator import data_validator
from simulation.continuous_engine import continuous_engine

router = APIRouter(prefix="/incidents", tags=["incidents"])

class IncidentCreate(BaseModel):
    type: str  # accident, pothole, flood, power_cut, crime, road_damage, fire, water_leak
    name: str
    description: Optional[str] = ""
    location_geojson: str       # GeoJSON coordinates string

class IncidentResponse(BaseModel):
    id: int
    type: str
    name: str
    description: Optional[str]
    location_geojson: str
    status: str
    reported_by: Optional[int]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


async def simulate_ai_verification(incident_id: int, db_session_factory):
    """Background task: run AI + sensor cross-verification, then broadcast result."""
    await asyncio.sleep(4.0)   # Simulate async processing latency

    db = db_session_factory()
    try:
        incident = db.query(Incident).filter_by(id=incident_id).first()
        if incident:
            incident.status = "verified"
            db.commit()

            await ws_manager.broadcast({
                "type": "INCIDENT_VERIFIED",
                "incident": {
                    "id":               incident.id,
                    "type":             incident.type,
                    "name":             incident.name,
                    "status":           incident.status,
                    "location_geojson": incident.location_geojson,
                }
            })
    except Exception as e:
        print(f"Error verifying incident in background: {e}")
    finally:
        db.close()


@router.post("", status_code=status.HTTP_201_CREATED)
def report_incident(
    inc_in: IncidentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Report a new citizen incident.

    Returns the saved incident PLUS an immediate cross-verification result
    (sensor corroboration, deduplication, confidence score) so the UI can
    display it without waiting for the background AI task.
    """
    # --- Parse coordinates from location_geojson -------------------------
    lat, lng = 0.0, 0.0
    try:
        geo = json.loads(inc_in.location_geojson)
        coords = geo.get("coordinates", [0.0, 0.0])
        lng, lat = float(coords[0]), float(coords[1])
    except Exception:
        pass

    # --- Immediate cross-verification ------------------------------------
    # Grab current telemetry snapshot from the continuous engine
    current_telemetry = getattr(continuous_engine, "_last_telemetry", None)
    verification = data_validator.cross_verify_incident(
        inc_in.type, lat, lng, current_telemetry
    )

    # --- Save to DB ------------------------------------------------------
    incident = Incident(
        type=inc_in.type,
        name=inc_in.name,
        description=inc_in.description,
        location_geojson=inc_in.location_geojson,
        status="reported",
        reported_by=current_user.id
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Register in dedup store after save
    data_validator.register_incident(inc_in.type, lat, lng)

    # --- Audit log -------------------------------------------------------
    log = AuditLog(
        user_id=current_user.id,
        action=f"Reported {inc_in.type} incident: {inc_in.name} (score={verification['verification_score']})"
    )
    db.add(log)
    db.commit()

    # --- Schedule background deep-verification ---------------------------
    from database.connection import SessionLocal
    background_tasks.add_task(simulate_ai_verification, incident.id, SessionLocal)

    return {
        "id":                  incident.id,
        "type":                incident.type,
        "name":                incident.name,
        "description":         incident.description,
        "location_geojson":    incident.location_geojson,
        "status":              incident.status,
        "reported_by":         incident.reported_by,
        "created_at":          incident.created_at,
        # NEW: immediate cross-verification
        "verification":        verification,
    }


@router.get("", response_model=List[IncidentResponse])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all active reported and verified incidents."""
    return db.query(Incident).filter(Incident.status != "resolved").all()


@router.put("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Planner", "Government Official", "Administrator"]))
):
    """Mark an incident as resolved (requires Planner/Official permissions)."""
    incident = db.query(Incident).filter_by(id=incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "resolved"
    db.commit()
    db.refresh(incident)

    log = AuditLog(
        user_id=current_user.id,
        action=f"Resolved incident ID {incident_id}"
    )
    db.add(log)
    db.commit()

    return incident
