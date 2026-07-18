from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from database.connection import get_db
from database.schema import Scenario, MapElement, SimulationResult, User
from api.auth import get_current_user
from simulation.engine import SimulationEngine
from ai.agent_coordinator import AgentCoordinator
from models.forecaster import TemporalForecaster
from configs.config import settings

logger = logging.getLogger(__name__)

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
    confidence_score: Optional[float] = 95.0
    assumptions: Optional[List[str]] = []
    limitations: Optional[List[str]] = []

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


# ── Gemini AI Planning Assistant ─────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are the Mirror City AI Planning Assistant — an expert urban intelligence system "
    "embedded in a real-time AI Digital Twin platform.\n\n"
    "Your role:\n"
    "- Analyse urban planning questions for a smart city digital twin\n"
    "- Provide data-driven recommendations based on city simulation context\n"
    "- Structure responses with bold headers, bullet points, and specific metrics\n"
    "- When suggesting infrastructure placements, mention concrete trade-offs\n"
    "- Always mention confidence level, key assumptions, and limitations\n"
    "- Keep responses concise but insightful (3-5 paragraphs max)\n\n"
    "Domain expertise: traffic engineering, urban planning, flood risk, air quality, "
    "energy grids, public health, green infrastructure, smart mobility, city resilience.\n\n"
    "Respond in Markdown format. Use emojis sparingly to highlight sections."
)


def _call_gemini(prompt: str, context: str) -> Optional[str]:
    """Call Google Gemini 1.5 Flash. Returns text response or None on failure."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        full_prompt = f"{context}\n\n---\n\nUser Question: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except ImportError:
        logger.warning(
            "google-generativeai not installed. "
            "Run: pip install google-generativeai"
        )
        return None
    except Exception as exc:
        logger.warning(f"Gemini API call failed: {exc}")
        return None


def _build_context(scenario_id: Optional[int], db: Session) -> str:
    """Build a rich city-state context string to inject into the AI prompt."""
    lines = [
        "## Mirror City Digital Twin - Current State Context",
        f"- AI Provider: {settings.LLM_PROVIDER}",
        "- Real-time agents: Traffic, Pollution, Healthcare, Energy, Flood, "
          "Crowd, Emergency, Economy, Environment, Master Coordinator",
        "- Data refresh rate: every 3 seconds via WebSocket streams",
    ]
    if scenario_id:
        scen = db.query(Scenario).filter_by(id=scenario_id).first()
        if scen:
            lines.append(f"- Active Scenario: {scen.name} - {scen.description or 'No description'}")
            lines.append(f"- Infrastructure Elements Placed: {len(scen.elements)}")
            type_counts: Dict[str, int] = {}
            for e in scen.elements:
                type_counts[e.type] = type_counts.get(e.type, 0) + 1
            lines.append(f"- Element Breakdown: {json.dumps(type_counts)}")
            if scen.results:
                metrics = json.loads(scen.results[0].metrics_json)
                lines.append(f"- Latest Simulation Metrics:\n{json.dumps(metrics, indent=2)}")
    return "\n".join(lines)


def _keyword_fallback(prompt: str) -> AssistantResponse:
    """
    Deterministic fallback for common urban planning queries.
    Used when Gemini API is unavailable. Clearly labeled as offline fallback.
    """
    p = prompt.lower()

    if any(kw in p for kw in ["rainfall", "rain", "flood", "storm", "drainage"]):
        return AssistantResponse(
            reply=(
                "**Flood & Disaster Agents Analysis** *(Offline Fallback - Gemini API unavailable)*\n\n"
                "A 40% increase in precipitation creates significant surface runoff risk in low-lying sectors.\n\n"
                "**Key Findings:**\n"
                "- Localized drainage basins overflow, raising the Flood Risk Index from ~12 to ~48.\n"
                "- Low-elevation roads face waterlogging, increasing emergency response times by 5-8 minutes.\n\n"
                "**Recommendation:**\n"
                "Place a **Green Space / Storm Retention Basin** in central coordinates. "
                "Green soil retention absorbs up to 45% of peak precipitation runoff."
            ),
            suggested_action={"type": "green_space", "name": "Storm Runoff Retention Park"},
            confidence_score=72.0,
            assumptions=["Precipitation increase is uniform", "No upstream dam failure"],
            limitations=["Offline fallback - connect Gemini API for personalised analysis"]
        )

    if any(kw in p for kw in ["hospital", "medical", "health", "clinic", "emergency room"]):
        return AssistantResponse(
            reply=(
                "**Healthcare Agent Recommendation** *(Offline Fallback - Gemini API unavailable)*\n\n"
                "Western suburban zones currently lack adequate emergency coverage.\n\n"
                "**Optimal Placement:**\n"
                "- A new healthcare center in the western grid increases city-wide coverage from ~85% to 100%.\n"
                "- Average emergency travel times drop by ~50%.\n"
                "- Estimated ROI: +18% within 5 years through anchored commercial development."
            ),
            suggested_action={"type": "hospital", "name": "Westside Emergency Center"},
            confidence_score=78.0,
            assumptions=["Population growth matches census projections"],
            limitations=["Offline fallback - connect Gemini API for personalised analysis"]
        )

    if any(kw in p for kw in ["widen", "road", "flyover", "traffic", "congestion", "highway"]):
        return AssistantResponse(
            reply=(
                "**Traffic & Pollution Agents Evaluation** *(Offline Fallback - Gemini API unavailable)*\n\n"
                "Widening the central arterial corridor reduces bottleneck congestion by ~40%.\n\n"
                "**Trade-off Analysis:**\n"
                "- Commuter travel times drop by ~3.5 minutes on average.\n"
                "- Expanded lanes induce demand: carbon emissions increase by +4.2 metric tons CO2/day.\n"
                "- **Better Alternative:** A Metro Station achieves the same traffic relief but cuts carbon by 15%."
            ),
            suggested_action={"type": "road_widening", "name": "Downtown Boulevard Expansion"},
            confidence_score=68.0,
            assumptions=["Induced demand factor at baseline", "Vehicle class split constant"],
            limitations=["Offline fallback - connect Gemini API for personalised analysis"]
        )

    return AssistantResponse(
        reply=(
            "**Mirror City AI Assistant** *(Offline Fallback - Gemini API unavailable)*\n\n"
            "I can help analyse urban planning decisions. Try asking:\n"
            "- *'What happens if rainfall increases by 40%?'* - Disaster Simulation\n"
            "- *'Where is the best place to build a hospital?'* - Healthcare Optimization\n"
            "- *'Should we widen the downtown roads?'* - Traffic vs Carbon Trade-offs\n\n"
            "**Note:** To enable real AI-powered analysis, ensure `GEMINI_API_KEY` is set "
            "in your `.env` and run `pip install google-generativeai`."
        ),
        suggested_action=None,
        confidence_score=50.0,
        assumptions=[],
        limitations=["Offline fallback mode - Gemini API not available"]
    )


@router.post("/assistant", response_model=AssistantResponse)
def planning_assistant(
    req: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI-powered urban planning assistant backed by Google Gemini 1.5 Flash.

    Injects full city-state context (active scenario, element breakdown, simulation
    metrics, agent architecture) into every prompt so answers are grounded in the
    live digital twin state. Falls back gracefully to labeled keyword responses
    when the Gemini API is offline or unavailable.
    """
    if settings.LLM_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
        context = _build_context(req.scenario_id, db)
        ai_text = _call_gemini(req.prompt, context)
        if ai_text:
            logger.info(f"Planning assistant served by Gemini AI (user={current_user.id})")
            return AssistantResponse(
                reply=ai_text,
                suggested_action=None,
                confidence_score=91.0,
                assumptions=["Response generated by Gemini 1.5 Flash with live city context"],
                limitations=["AI responses are advisory - verify against live simulation metrics"]
            )
        logger.warning("Gemini API call failed - falling back to keyword responses")

    logger.info(f"Planning assistant using keyword fallback (provider={settings.LLM_PROVIDER})")
    return _keyword_fallback(req.prompt)
