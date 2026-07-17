from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from database.connection import get_db
from database.schema import Scenario, MapElement, User
from api.auth import get_current_user, require_role

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# Pydantic Schemas
class ElementCreate(BaseModel):
    type: str # hospital, metro, green_space, road_widening, flyover, closure
    name: str
    location_geojson: str # GeoJSON coordinates
    radius: float = 0.0
    capacity: float = 0.0
    cost: float = 0.0

class ElementResponse(BaseModel):
    id: int
    scenario_id: int
    type: str
    name: str
    location_geojson: str
    radius: float
    capacity: float
    cost: float
    status: str

    class Config:
        from_attributes = True

class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    baseline_id: Optional[int] = None

class ScenarioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    baseline_id: Optional[int]
    created_by: int
    status: str
    elements: List[ElementResponse] = []

    class Config:
        from_attributes = True

@router.get("", response_model=List[ScenarioResponse])
def get_scenarios(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Citizens can read scenarios, Planner/Officials can manage
    return db.query(Scenario).all()

@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    scen = db.query(Scenario).filter_by(id=scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen

@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scen_in: ScenarioCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["Planner", "Government Official", "Administrator"]))
):
    # Create scenario
    scen = Scenario(
        name=scen_in.name,
        description=scen_in.description,
        baseline_id=scen_in.baseline_id,
        created_by=current_user.id,
        status="proposed"
    )
    db.add(scen)
    db.commit()
    
    # If baseline_id is specified, clone the baseline elements into the new scenario
    if scen_in.baseline_id:
        baseline_elements = db.query(MapElement).filter_by(scenario_id=scen_in.baseline_id).all()
        for elem in baseline_elements:
            cloned = MapElement(
                scenario_id=scen.id,
                type=elem.type,
                name=elem.name,
                location_geojson=elem.location_geojson,
                radius=elem.radius,
                capacity=elem.capacity,
                cost=elem.cost,
                status="active" if elem.scenario.status == "baseline" else "proposed"
            )
            db.add(cloned)
        db.commit()

    db.refresh(scen)
    return scen

@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_role(["Planner", "Government Official", "Administrator"]))
):
    scen = db.query(Scenario).filter_by(id=scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.status == "baseline":
        raise HTTPException(status_code=400, detail="Cannot delete baseline city scenario")
    db.delete(scen)
    db.commit()
    return

@router.post("/{scenario_id}/elements", response_model=ElementResponse, status_code=status.HTTP_201_CREATED)
def add_element(
    scenario_id: int,
    elem_in: ElementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Planner", "Government Official", "Administrator"]))
):
    scen = db.query(Scenario).filter_by(id=scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.status == "baseline":
        raise HTTPException(status_code=400, detail="Cannot modify baseline scenario")
        
    elem = MapElement(
        scenario_id=scenario_id,
        type=elem_in.type,
        name=elem_in.name,
        location_geojson=elem_in.location_geojson,
        radius=elem_in.radius,
        capacity=elem_in.capacity,
        cost=elem_in.cost,
        status="proposed"
    )
    db.add(elem)
    db.commit()
    db.refresh(elem)
    return elem

@router.delete("/{scenario_id}/elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_element(
    scenario_id: int,
    element_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Planner", "Government Official", "Administrator"]))
):
    scen = db.query(Scenario).filter_by(id=scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.status == "baseline":
        raise HTTPException(status_code=400, detail="Cannot modify baseline scenario")
        
    elem = db.query(MapElement).filter_by(id=element_id, scenario_id=scenario_id).first()
    if not elem:
        raise HTTPException(status_code=404, detail="Element not found in this scenario")
        
    db.delete(elem)
    db.commit()
    return
