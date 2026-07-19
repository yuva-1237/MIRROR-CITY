from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

from database.connection import get_db
from database.schema import Scenario, MapElement, User
from api.auth import get_current_user
from services.geospatial_service import geospatial_service
from simulation.continuous_engine import continuous_engine
from services.city_clock import city_clock

router = APIRouter(prefix="/geospatial", tags=["geospatial"])

class LoadLocationRequest(BaseModel):
    name: str
    lat: float
    lng: float
    location_type: str
    hierarchy: List[str]
    population: int
    area_sq_km: float
    elevation: float
    timezone: str
    datasets: Optional[Dict[str, Any]] = None

@router.get("/search")
def search_location(query: str, current_user: User = Depends(get_current_user)):
    """Search for any village, town, city, or district globally."""
    clean_query = query.strip()
    if not clean_query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    if len(clean_query) > 200:
        raise HTTPException(status_code=400, detail="Search query is too long (max 200 characters)")
    
    results = geospatial_service.search_location(clean_query)
    
    # If the only result returned is the synthetic not found fallback, or empty
    if not results or (len(results) == 1 and results[0].get("source") == "Not Found"):
        raise HTTPException(
            status_code=404,
            detail={
                "results": [],
                "message": f"No locations found for '{clean_query}'. Try checking the spelling or adding a country name."
            }
        )
    return results

@router.post("/load")
def load_digital_twin(req: LoadLocationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Loads the dynamic Digital Twin into the active engine memory, building a live graph."""
    try:
        # 1. Generate graph and buildings layer
        graph, buildings, datasets = geospatial_service.generate_city_graph(
            req.location_type, req.lat, req.lng
        )
        
        # Override datasets status based on loaded responses
        metadata = req.dict()
        metadata["datasets"] = datasets

        # 2. Update continuous engine active state
        continuous_engine.set_active_city(graph, metadata, buildings)

        # 3. Serialize nodes and edges for SensorSimulator
        nodes_list = []
        for n, attrs in graph.nodes(data=True):
            nodes_list.append({
                "id": n,
                "lat": attrs["lat"],
                "lng": attrs["lng"],
                "type": attrs.get("type", "residential"),
                "population_density": attrs.get("population_density", 50.0),
                "energy_demand": attrs.get("energy_demand", 50.0),
                "pollution_level": attrs.get("pollution_level", 50.0)
            })
            
        edges_list = []
        for u, v, attrs in graph.edges(data=True):
            edges_list.append({
                "from_node": u,
                "to_node": v,
                "name": attrs.get("road_name", "Local Street"),
                "length_m": attrs.get("length_m", 400.0),
                "speed_limit_kph": attrs.get("speed_limit_kph", 50.0),
                "lanes": attrs.get("lanes", 2),
                "base_congestion": attrs.get("base_congestion", 0.1)
            })

        # Update active nodes and edges in SensorSimulator
        disable_transit = (req.location_type == "village")
        city_clock.simulator.set_active_nodes_edges(
            nodes_list, edges_list, disable_transit=disable_transit
        )

        # 4. Clear old elements from database to avoid coordinate mismatches
        db.query(MapElement).delete()
        
        # Ensure we have an active baseline scenario for this city
        baseline_scen = db.query(Scenario).filter_by(status="baseline").first()
        if not baseline_scen:
            baseline_scen = Scenario(
                name=f"{req.name} Baseline",
                description=f"Initial default twin for {req.name}",
                status="baseline",
                created_by=current_user.id
            )
            db.add(baseline_scen)
        else:
            baseline_scen.name = f"{req.name} Baseline"
            baseline_scen.description = f"Initial default twin for {req.name}"
        
        db.commit()

        return {
            "status": "success",
            "message": f"Digital Twin for {req.name} successfully generated and initialized.",
            "active_city": metadata
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Digital Twin: {str(e)}"
        )

@router.get("/active")
def get_active_twin(current_user: User = Depends(get_current_user)):
    """Returns metadata of currently active twin."""
    return {
        "active_city": continuous_engine.active_city_metadata,
        "buildings_count": len(continuous_engine.buildings_layer)
    }
