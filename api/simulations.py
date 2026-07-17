from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json

from database.connection import get_db
from database.schema import Scenario, MapElement, SimulationResult, User
from api.auth import get_current_user
from simulation.engine import SimulationEngine
from ai.agent_coordinator import AgentCoordinator
from models.forecaster import TemporalForecaster

router = APIRouter(prefix="/simulations", tags=["simulations"])

engine = SimulationEngine()
coordinator = AgentCoordinator()
forecaster = TemporalForecaster()

class AssistantRequest(BaseModel):
    prompt: str
    scenario_id: Optional[int] = None

class AssistantResponse(BaseModel):
    reply: str
    suggested_action: Optional[Dict[str, Any]] = None

@router.post("/run/{scenario_id}")
def run_scenario_simulation(
    scenario_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    scen = db.query(Scenario).filter_by(id=scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Fetch scenario elements
    elements = [
        {
            "id": e.id,
            "type": e.type,
            "name": e.name,
            "location_geojson": e.location_geojson,
            "radius": e.radius,
            "capacity": e.capacity,
            "cost": e.cost
        }
        for e in scen.elements
    ]

    # Fetch baseline metrics for comparison
    baseline_scenario = db.query(Scenario).filter_by(status="baseline").first()
    baseline_metrics = {}
    if baseline_scenario and baseline_scenario.results:
        baseline_metrics = json.loads(baseline_scenario.results[0].metrics_json)

    # 1. Run simulation engine
    metrics = engine.run_simulation(elements)

    # 2. Run multi-agent coordinator
    agent_output = coordinator.run_collaborative_analysis(scen.name, elements, baseline_metrics)

    # 3. Generate time-series forecast
    forecast = forecaster.generate_24h_forecast(elements)

    # 4. Save results to Database
    # Delete old results for this scenario first
    db.query(SimulationResult).filter_by(scenario_id=scen.id).delete()
    
    result = SimulationResult(
        scenario_id=scen.id,
        metrics_json=json.dumps(metrics),
        recommendations_json=json.dumps({
            "summary": agent_output["explanation"],
            "actions": agent_output["recommendations"]
        })
    )
    db.add(result)
    db.commit()

    return {
        "scenario_id": scen.id,
        "metrics": metrics,
        "explanation": agent_output["explanation"],
        "recommendations": agent_output["recommendations"],
        "agent_reports": agent_output["agent_reports"],
        "forecast": forecast
    }

@router.get("/compare")
def compare_scenarios(
    ids: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Compare multiple scenarios side-by-side. Returns metrics and element summaries."""
    try:
        scenario_ids = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scenario ID list format")

    comparison_results = []
    for s_id in scenario_ids:
        scen = db.query(Scenario).filter_by(id=s_id).first()
        if not scen:
            continue
            
        metrics = {}
        recommendations = {}
        if scen.results:
            metrics = json.loads(scen.results[0].metrics_json)
            recommendations = json.loads(scen.results[0].recommendations_json)
        else:
            # Fallback if simulation has not been run yet
            elements_list = [
                {"type": e.type, "location_geojson": e.location_geojson} for e in scen.elements
            ]
            metrics = engine.run_simulation(elements_list)
            recommendations = {
                "summary": "Simulation has not been persisted. Displaying quick engine outputs.",
                "actions": []
            }

        comparison_results.append({
            "scenario_id": scen.id,
            "name": scen.name,
            "description": scen.description,
            "status": scen.status,
            "element_count": len(scen.elements),
            "metrics": metrics,
            "recommendations": recommendations
        })

    return comparison_results

@router.post("/assistant", response_model=AssistantResponse)
def planning_assistant(
    req: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt_lower = req.prompt.lower()
    
    # 1. Intent: Rainfall increase
    if "rainfall" in prompt_lower or "rain" in prompt_lower or "flood" in prompt_lower:
        reply = (
            "🌧️ **Disaster & Weather Agents Analysis:**\n"
            "An increase in precipitation by 40% creates significant surface runoff risk in Neo-Vidia's downtown commercial sectors.\n\n"
            "**Key Findings:**\n"
            "- Localized drainage basins will overflow, raising the Flood Risk Index from 12.4 to **48.2**.\n"
            "- Roads in lower grid sectors (e.g. Node 2,2 and 3,2) will face waterlogging, increasing emergency response times by 6.2 minutes.\n\n"
            "**Recommendation:**\n"
            "Consider creating a **Green Space** (Dolores Greenway expansion) in the center-right coordinates. Green soil retention basins absorb up to 45% of peak precipitation runoff, keeping the risk index below 15.0."
        )
        return {
            "reply": reply,
            "suggested_action": {"type": "green_space", "name": "Storm Runoff Retention Park"}
        }

    # 2. Intent: Hospital placement
    elif "hospital" in prompt_lower or "medical" in prompt_lower or "health" in prompt_lower:
        reply = (
            "🏥 **Healthcare & Economy Agents Recommendation:**\n"
            "We have evaluated the city's healthcare coverage. Currently, the Western Suburban blocks (Node 4,0 to 5,2) are outside the 1.8km catchment radius of Saint Francis Hospital.\n\n"
            "**Optimal Hospital Placement:**\n"
            "- Placing a new healthcare center near **Node (4,1)** increases City-Wide Healthcare Coverage from 85% to **100.0%**.\n"
            "- Average emergency travel times for residents drop from 8.4 mins to **4.2 mins**.\n"
            "- Short-term construction costs will be $120M, but it generates an estimated ROI of +18.4% by anchoring nearby commercial developments."
        )
        return {
            "reply": reply,
            "suggested_action": {"type": "hospital", "name": "Westside Emergency Center"}
        }

    # 3. Intent: Widen road / flyover
    elif "widen" in prompt_lower or "road" in prompt_lower or "flyover" in prompt_lower:
        reply = (
            "🚗 **Traffic & Pollution Agents Evaluation:**\n"
            "Widening the central arterial corridor (East-West St 2) reduces bottleneck congestion by 40%.\n\n"
            "**Trade-off Analysis:**\n"
            "- Commuter travel times drop by **3.5 minutes** on average.\n"
            "- However, the Pollution Agent warns that expanding road lanes encourages vehicle usage, increasing daily Carbon Footprints by **+4.2 metric tons CO2**.\n"
            "- The Traffic Agent suggests adding a **Metro Station** instead of road widening, which achieves the same traffic relief but cuts carbon emissions by 15%."
        )
        return {
            "reply": reply,
            "suggested_action": {"type": "road_widening", "name": "Downtown Boulevard Expansion"}
        }

    # Default reply
    reply = (
        "🤖 **Mirror City AI Assistant:**\n"
        "I understand you are evaluating city parameters. You can ask me:\n"
        "- *'What happens if rainfall increases by 40%?'* (Disaster Simulation)\n"
        "- *'Where is the best place to build a hospital?'* (Healthcare Access Optimization)\n"
        "- *'Should we widen the downtown roads?'* (Traffic vs Carbon Trade-offs)\n\n"
        "Let me know which scenario we should plan next!"
    )
    return {
        "reply": reply,
        "suggested_action": None
    }
