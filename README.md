# 🏙️ MIRROR CITY

> **"See the future of your city before it happens."**

MIRROR CITY is an enterprise-grade AI-powered Digital Twin platform designed to predict and simulate how municipal and infrastructure planning decisions affect urban environments *before* they are physically deployed. 

Planners, disaster management agencies, and city officials can configure scenarios, deploy mock assets (subways, parks, hospitals, closures), and run real-time Graph Neural Network (GNN) and Multi-Agent simulations to evaluate city-wide impacts.

---

## 🏛️ System Architecture

```
                                  +---------------------------------------+
                                  |         React (Vite) Frontend         |
                                  |     (Leaflet Map / KPI Dashboard)      |
                                  +-------------------+-------------------+
                                                      |
                                                      | HTTP / API Gateway
                                                      v
                                  +-------------------+-------------------+
                                  |          FastAPI Backend              |
                                  |         (main REST Router)            |
                                  +-------+--------------------+----------+
                                          |                    |
                  +-----------------------+                    +------------------------+
                  |                                                                     |
                  v                                                                     v
    +-------------+-------------+                                         +-------------+-------------+
    |    AI Multi-Agent Core    |                                         |    Graph Simulation Engine  |
    |  (10 Collaborative Agents)|                                         |   (Shortest Commute Paths)  |
    +---------------------------+                                         +-------------+-------------+
                                                                                        |
                                                                                        v
                                                                          +-------------+-------------+
                                                                          |   GNN Congestion Propagator |
                                                                          |    (2-Layer NumPy GCN)    |
                                                                          +---------------------------+
```

### 1. The GNN Traffic Propagator (`/simulation/gnn.py`)
Mirror City represents the urban infrastructure network as a graph $G = (V, E)$, where $V$ represents residential, commercial, industrial, healthcare, and transit zones, and $E$ represents connecting street corridors. When a planning decision shifts flow (e.g. road widening or closure):
- A 2-layer Graph Convolutional Network (GCN) mathematical layer propagates congestion using normalized adjacency representations:
  $$H^{(l+1)} = \sigma\left(\tilde{D}^{-\frac{1}{2}} \tilde{A} \tilde{D}^{-\frac{1}{2}} H^{(l)} W^{(l)}\right)$$
- The resulting node congestion indices propagate to connecting edges, updating commuter routing travel times.

### 2. Multi-Agent AI System (`/ai`, `/agents`)
Ten specialized domain-specific AI agents evaluate each simulation:
1. **Traffic Agent**: Commuter bottlenecks and corridor velocities.
2. **Healthcare Agent**: Clinical reach, catchment indices, and emergency times.
3. **Pollution Agent**: Daily carbon output (metric tons CO2) and particulate AQI dispersion.
4. **Weather Agent**: Urban Heat Island effects and microclimate cooling.
5. **Disaster Agent**: Surface runoff retention and flood resilience scoring.
6. **Economy Agent**: Property premiums, job anchor creations, and project ROI.
7. **Energy Agent**: Peak electricity substation grid loads (MW).
8. **Transportation Agent**: Transit coverage and walkability access indices.
9. **Urban Growth Agent**: TOD (Transit-Oriented Development) and local population density changes.
10. **Infrastructure Agent**: Construction timeline stress and utility pipe disruptions.

The **Agent Coordinator** gathers independent reports, aggregates confidence levels, and synthesizes an explainable, plain-language advisory narrative.

### 3. Time-Series Forecasting Engine (`/models/forecaster.py`)
Generates 24-hour temporal predictions for traffic flow, air pollution (AQI), electricity grid loading, and water flow based on diurnal commute profiles and the modifiers introduced by proposed infrastructure.

---

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Node.js 18+ & npm**

### Simple Windows Setup
We provide a one-click startup script that checks dependencies, seeds the database, and launches the client and server processes concurrently:
```powershell
# Run the PowerShell bootstrapper from the project root
.\scripts\run.ps1
```

### Manual Setup

1. **Backend Server Setup**
   ```bash
   # Install dependencies
   pip install fastapi uvicorn sqlalchemy pyjwt reportlab networkx pydantic pytest

   # Seed the database (creates tables & baseline graph)
   python database/seed.py

   # Start the FastAPI server
   python backend/main.py
   ```
   The backend will start running on `http://localhost:8000`. API docs can be viewed at `http://localhost:8000/docs`.

2. **Frontend Client Setup**
   ```bash
   cd frontend
   
   # Install dependencies
   npm install
   
   # Run the Vite server
   npm run dev
   ```
   The client will open on `http://localhost:5173`.

---

## 🔑 Seeding & User Roles

The database is pre-seeded with 5 user accounts representing different platform access tiers:

| Email | Password | Role | Access Level |
| :--- | :--- | :--- | :--- |
| `admin@mirrorcity.gov` | `adminpassword` | **Administrator** | Access to Cockpit, Comparisons, and Admin logs/reseeding |
| `planner@mirrorcity.gov` | `plannerpassword` | **Planner** | Create scenarios, deploy assets, run simulations |
| `officer@mirrorcity.gov` | `officerpassword` | **Government Official** | Create scenarios, download reports |
| `researcher@mirrorcity.gov` | `researcherpassword` | **Researcher** | Run forecasts, read-only analytics comparison |
| `citizen@mirrorcity.gov` | `citizenpassword` | **Citizen** | Read-only dashboards and scenario maps |

---

## 📈 Demo Walkthrough

1. **Sign In**: Log in using `planner@mirrorcity.gov` / `plannerpassword`.
2. **Review Baseline**: Examine the starting city stats. The Western suburban blocks currently lack nearby hospitals, and downtown traffic spikes during commute peaks.
3. **Plan Scenario**: Click the `+` icon in the active scenario block. Name it *"Westside Healthcare Expansion"* and click **Create Project**.
4. **Deploy Assets**: Select the **Hospital** tool in the deployment drawer, then click in the Western sector of the map (lower-left quadrant) to place it.
5. **Run Simulation**: Click **Recalculate City State**. You will see:
   - **Healthcare outreach** spikes to **100%**.
   - **Emergency response speed** drops by **4+ minutes**.
   - **Explainable AI** updates detailing energy grid load increases.
6. **AI Planning Assistant**: Type *"What if rainfall increases by 40%?"* in the floating chat. The Disaster Agent warns of flash floods in the downtown grid and suggests deploying a **Green Space** (Park) to absorb runoff. Click **Deploy Suggestion** to place it.
7. **Compare**: Switch to the **Multi-Scenario** tab. Select the baseline and your healthcare proposal to review performance indicators side-by-side.
8. **Export**: Go back to the cockpit and click **Download Executive Report (PDF)** to download a complete spatial evaluation document ready for council presentation.