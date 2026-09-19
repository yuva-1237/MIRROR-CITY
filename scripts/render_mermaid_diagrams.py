import os
import sys
import base64
import urllib.request
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mermaid_renderer")

DIAGRAMS = {
    "architecture_system.png": """graph TD
    User([User Client]) -->|HTTPS / WSS| FE[React Vite Frontend]
    FE -->|API Requests| GW[FastAPI API Gateway]
    GW -->|Auth check| Auth[JWT Authenticator]
    GW -->|Telemetry Stream| WS[WebSocket Connection Manager]
    GW -->|City State & Scenarios| DB[(SQLite Database)]
    GW -->|AI Reasoning| AgentCoord[Multi-Agent Coordinator]
    AgentCoord -->|Collaboration| Agents[10 Specialized AI Agents]
    GW -->|Simulation Run| SimEngine[Continuous Simulation Engine]
    SimEngine -->|Congestion Signal| SpectralProp[Spectral Graph Propagator]
    SimEngine -->|Runoff Math| Flood[Flood Runoff Model]
    SimEngine -->|Force Vector| Crowd[Crowd Density Model]
    SimEngine -->|Diurnal Curves| Forecast[Deterministic Forecaster]
    GW -->|Geocoding & Presets| GeoService[Geospatial Service]
    GeoService -->|Nominatim API| OSM[OpenStreetMap / Overpass]
    GeoService -->|Elevation API| OpenMeteo[Open-Meteo API]
    GeoService -->|Weather API| WeatherAPI[OpenWeatherMap API]""",

    "architecture_agent_collaboration.png": """graph LR
    Input[Live Telemetry Batch] --> Coord[Agent Coordinator]
    Coord -->|Distribute Context| A1[Traffic Agent]
    Coord -->|Distribute Context| A2[Pollution Agent]
    Coord -->|Distribute Context| A3[Healthcare Agent]
    Coord -->|Distribute Context| A4[Disaster & Flood Agent]
    Coord -->|Distribute Context| A5[Economy Agent]
    A1 -->|Share Congestion Index| PeerOutputs[Structured Peer Outputs]
    A2 -->|Share AQI Forecast| PeerOutputs
    A3 -->|Share Hospital Access| PeerOutputs
    A4 -->|Share Runoff Risk & Veto| PeerOutputs
    A5 -->|Share Commercial Gain| PeerOutputs
    PeerOutputs --> Resolver[Conflict Resolver Engine]
    Resolver --> TradeOff[Quantified Trade-Off Report]
    TradeOff --> Consensus[Consensus Index & Arbitrated Policy]""",

    "architecture_data_pipeline.png": """graph TD
    Sources[External Data Sources: OSM, Weather, Elevation] --> Fetch[Ingestion Handlers]
    Fetch --> Val["Data Validator"]
    Val -->|Physically Impossible| Reject[Discard / Flag Anomaly]
    Val -->|Normal Range| Normal[Rolling Stats Window]
    Normal --> AnomalyCheck["Outlier Detection > 3 Sigma?"]
    AnomalyCheck -->|Yes| FlagAnomaly[Reduce Quality Score / Log Issue]
    AnomalyCheck -->|No| SafeTelemetry[Telemetry Snapshot]
    SafeTelemetry --> DbSave[(Database Snapshot Save)]
    SafeTelemetry --> Stream[Broadcast via WebSockets]""",

    "architecture_simulation_workflow.png": """sequenceDiagram
    participant Planner as City Planner
    participant API as FastAPI Router
    participant Sim as Simulation Engine
    participant Coord as Agent Coordinator
    participant Resolver as Conflict Resolver
    participant Forecaster as Forecaster Model
    participant DB as SQLite Database

    Planner->>API: Create Scenario (e.g. Westside Transit)
    API->>DB: Persist Scenario & Elements
    Planner->>API: Run Simulation
    API->>Sim: Run Simulation (Elements)
    Sim->>Sim: Spectral Graph & BPR Traffic Propagation
    API->>Coord: Collaborative Multi-Agent Analysis
    Coord->>Resolver: Arbitrate Clashing Stances
    Resolver->>Coord: Generate Trade-Off Report
    API->>Forecaster: Generate 24h Predictions
    API->>DB: Save Results (Metrics & Advisory)
    API->>Planner: Return A/B Visual Payload""",

    "architecture_event_flow.png": """graph TD
    Clock[City Clock 3s Tick] --> Ingest[Fetch Weather & Active Elements]
    Ingest --> Sim[Run Continuous Simulation Models]
    Sim --> Telemetry[Generate Telemetry Snapshot]
    Telemetry --> Quality[Validate & Compute Quality Badge]
    Quality --> AI[Run Multi-Agent Live Cycle]
    AI --> Resolver[Resolve Inter-Agent Conflicts]
    Resolver --> Forecast[Calculate Diurnal Predictions]
    Forecast --> Save[(Save Metric Snapshots to DB)]
    Save --> Broadcast[WebSocket Broadcast to Clients]
    Broadcast --> UI[Update 3D Twin, Collaboration View & Gauges]""",

    "architecture_deployment.png": """graph TD
    Client([Browser Client]) -->|Access Port 80| Nginx[Frontend Nginx Container]
    Nginx -->|SPA Static Files| React[Vite React Bundle]
    Nginx -->|Reverse Proxy /api| Gunicorn[FastAPI Backend Container]
    Nginx -->|Reverse Proxy /ws| Gunicorn
    Gunicorn -->|Read/Write| SQLite[(SQLite Database Volume)]
    Gunicorn -->|AI Reasoning| Gemini[Gemini AI Engine]
    Gunicorn -->|Weather Query| OWM[OpenWeatherMap API]
    Gunicorn -->|GIS Query| Overpass[Overpass API / OSM]"""
}

def render_diagrams():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs", "images"))
    os.makedirs(output_dir, exist_ok=True)

    for filename, code in DIAGRAMS.items():
        filepath = os.path.join(output_dir, filename)
        logger.info(f"Rendering {filename} via mermaid.ink...")
        
        try:
            b64 = base64.b64encode(code.encode("utf-8")).decode("utf-8")
            url = f"https://mermaid.ink/img/{b64}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=15) as res:
                data = res.read()
                with open(filepath, "wb") as f:
                    f.write(data)
                logger.info(f"Successfully saved {filepath} ({len(data)} bytes)")
        except Exception as e:
            logger.error(f"Failed to render {filename} via mermaid.ink: {e}")
            # Fallback to creating a placeholder or matplotlib rendered image if remote is unreachable
            _create_fallback_image(filepath, filename)

def _create_fallback_image(filepath: str, title: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (1000, 600), color=(15, 23, 42))
        d = ImageDraw.Draw(img)
        d.rectangle([(20, 20), (980, 580)], outline=(59, 130, 246), width=3)
        d.text((50, 50), f"Mirror City Architecture: {title}", fill=(255, 255, 255))
        d.text((50, 100), "Rendered architecture snapshot for GitHub viewers", fill=(148, 163, 184))
        img.save(filepath)
        logger.info(f"Saved fallback diagram to {filepath}")
    except Exception as fe:
        logger.error(f"Fallback generation failed: {fe}")

if __name__ == "__main__":
    render_diagrams()
