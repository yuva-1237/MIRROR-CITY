# MIRROR CITY — ENSO / Climate DNA Architecture & Implementation Audit

## 1. Codebase Architecture Audit

### Frontend Architecture
- **Framework**: React 18.3.1 with TypeScript 5.2.2.
- **Build Tool / Bundler**: Vite 5.2.11.
- **Styling**: TailwindCSS 3.4.4 with custom cyberpunk/twin palette (`brand-dark`, `brand-panel`, `brand-neonCyan`, `brand-neonPurple`, `brand-neonOrange`).
- **State Management**: Zustand 5.0.14 (`useLocationStore`, `useCityStream`).
- **Animations & Interactivity**: Framer Motion 11.2.10.
- **GIS / Spatial Visualization**: 
  - 3D WebGL: `@deck.gl/core` + `@deck.gl/layers` + `@deck.gl/react` (9.3.7) + `maplibre-gl` (5.24.0).
  - 2D GIS: `leaflet` (1.9.4) + `react-leaflet` (4.2.1).
- **Charts & Telemetry**: `chart.js` (4.4.3) + `react-chartjs-2` (5.2.0).
- **Icons**: `lucide-react` (0.395.0).
- **API Communication**: Centralized wrapper in `src/lib/api.ts` with error mapping, token injection, and 401 interceptors.

### Backend Architecture
- **Framework**: Python 3.12+ FastAPI (0.100+) on Uvicorn ASGI server.
- **Architecture**: Modular API router architecture mounted on `/api` (`settings.API_V1_STR`).
- **Data Persistence**: SQLAlchemy with dual-mode storage:
  - Default: Zero-setup SQLite with Write-Ahead Logging (`mirror_city.db`).
  - Production: PostgreSQL + PostGIS (`POSTGIS_URL`).
- **Security & Authentication**:
  - Cryptographic JWT bearer tokens with HS256, minimum 32-char enforced secret (`JWT_SECRET`).
  - Bcrypt password hashing (12 rounds) and role-based access control (Administrator, City Planner, Emergency Responder, Analyst, Auditor).
  - Sliding-window IP rate limiting (`RateLimitMiddleware`).
- **Continuous Simulation Engine**:
  - `services/city_clock.py`: 3-second continuous loop simulating urban physics and broadcasting state via WebSockets (`services/ws_manager.py`).
  - `simulation/continuous_engine.py`: Spectral Graph Laplacian diffusion propagator ($L = I - D^{-1/2} A D^{-1/2}$), Hydrostatic flood depth model, crowd dynamics, disaster propagation.
- **Multi-Agent Cognitive Layer & SHADOW AI**:
  - 10 autonomous agents in `agents/live_agents.py` (`TrafficAI`, `PollutionAI`, `HealthcareAI`, `PowerAI`, `FloodAI`, `WeatherAI`, `CrimeAI`, `EmergencyAI`, `EconomyAI`, `TransportationAI`).
  - Automated Master Conflict Resolver (`agents/conflict_resolver.py`).
  - Master recommendation & explainability synthesis (`ai/agent_coordinator.py`).
- **Spatial Intelligence**:
  - `services/geospatial_service.py`: Global reverse geocoding via OpenStreetMap Overpass & Nominatim with LRU caching, Open-Meteo elevation extraction.

---

## 2. Components Reused vs Added

### Reused Components & Services
- `backend.main:app`: Mounted router under `/api/climate`.
- `configs/config.py`: Extended with `ENSO_CACHE_TTL`.
- `services/city_clock.py`: Injected `climate_dna` telemetry into WebSocket ticks.
- `agents/live_agents.py`: Extended `WeatherAI` and `FloodAI` to consume climate drivers.
- `ai/agent_coordinator.py`: Master explainability chain enhanced with ENSO attribution.
- `frontend/src/store/locationStore.ts`: Coordinates, hierarchy, and city metadata.
- `frontend/src/hooks/useCityStream.ts`: WebSocket stream receiving `climate_dna`.
- `frontend/src/components/CommandCenter.tsx`: Telemetry cockpit embedding widget and modal.
- `frontend/src/components/Dashboard.tsx`: Integrated Climate DNA card and modal.
- `frontend/src/App.tsx`: Global navigation header pill for Climate DNA.

### Newly Added Components & Services
- **Backend Services (`services/climate/`)**:
  - `enso_types.py`: Typed enums (`EnsoPhase`, `EnsoIntensity`) and Pydantic response models.
  - `enso_cache.py`: High-performance in-memory cache with hit/miss logging and TTL expiration.
  - `enso_provider.py`: Authoritative NOAA CPC parser with network timeouts and validation.
  - `enso_service.py`: State orchestrator, diagnostics, confidence calculation.
  - `climate_impact_service.py`: Teleconnection matrix and 8-sector probabilistic risk engine.
- **API Routing (`api/climate.py`)**:
  - `GET /api/climate/enso`: Normalized NOAA ENSO state (`{ success: true, data: { ... } }`).
  - `GET /api/climate/impact`: City-level teleconnection and 8-sector risk indicators.
  - `GET /api/climate/dna`: CITY DNA environmental signal tree.
  - `GET /api/climate/timeline`: Historical ONI data and IRI outlook probabilities.
  - `POST /api/climate/simulate`: Counterfactual "What-If" scenario sandbox.
  - `GET /api/climate/teleconnection`: Pacific-to-city atmospheric wave vectors.
- **Frontend Client (`frontend/src/api/climateApi.ts`)**:
  - Typed client for all climate endpoints.
- **Frontend UI (`frontend/src/components/ClimateDNA/`)**:
  - `ClimateDNACard.tsx`: Dashboard widget adhering to ASCII specification.
  - `ClimateDNAModal.tsx`: Full-screen NASA-style command modal.
  - `ClimateTimeline.tsx`: Chronological timeline visualizer.
  - `ClimateScenarioPanel.tsx`: Counterfactual "What-If" scenario sandbox.

---

## 3. Data Flow Architecture

```text
 NOAA Climate Prediction Center (CPC)
   ├── ONI 3-Month Running Mean Anomalies
   └── Monthly Diagnostic Synopsis
                  │
                  ▼
         enso_provider.py (HTTP Ingestion & Validation)
                  │
                  ▼
         enso_cache.py (In-Memory Cache, TTL = 21,600s)
                  │
                  ▼
         enso_service.py (State & Intensity Classification)
                  │
                  ▼
    climate_impact_service.py (City Teleconnection Model)
                  │
                  ▼
       FastAPI Router: /api/climate/*
                  │
                  ├──► WebSocket CityClock Loop (Live Telemetry Stream)
                  │          └──► WeatherAI & FloodAI & SHADOW AI
                  │
                  ▼
        frontend/src/api/climateApi.ts
                  │
                  ▼
    ClimateDNACard + ClimateDNAModal + ClimateTimeline + ClimateScenarioPanel
```

---

## 4. Key Design Decisions & Scientific Assumptions

1. **Authoritative Grounding (No Fabricated Conditions)**:
   - Data is sourced strictly from NOAA CPC ONI datasets.
   - If external connections fail, the service utilizes a verified baseline fixture (`fixtures/climate/enso_historical_baseline.json`) marked as cached baseline, or responds with `ENSO_DATA_UNAVAILABLE`.
2. **Probabilistic Non-Deterministic Language**:
   - In accordance with meteorological science, ENSO shifts background probability distributions rather than dictating day-to-day weather deterministically.
   - All summaries and SHADOW AI responses employ phrases such as *"Historical patterns associated with La Niña can increase rainfall variability in this region"*.
3. **Structured Enums**:
   - EnsoPhase: `EL_NINO`, `LA_NINA`, `NEUTRAL`, `UNKNOWN`.
   - EnsoIntensity: `WEAK`, `MODERATE`, `STRONG`, `UNKNOWN`.
4. **Performance & Caching**:
   - 6-hour TTL (`ENSO_CACHE_TTL=21600`) avoids redundant external requests.
   - Zero additional database overhead; state is cached in memory.
