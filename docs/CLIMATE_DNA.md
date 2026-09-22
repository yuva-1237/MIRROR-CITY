# CLIMATE DNA — ENSO & Global-to-Local Climate Intelligence

## 1. Executive Summary

**CLIMATE DNA** is MIRROR CITY's climate intelligence capability. It bridges macro-scale equatorial ocean-atmosphere dynamics with local urban infrastructure resilience, translating global El Niño–Southern Oscillation (ENSO) signals into localized, probabilistic risk assessments across eight municipal sectors:

1. **Rainfall**
2. **Flood Risk**
3. **Drought Risk**
4. **Heat Wave Risk**
5. **Water Stress**
6. **Agriculture / Soil Moisture**
7. **Infrastructure Strain**
8. **Energy Demand**

> **Scientific Guiding Principle:**
> ENSO is treated strictly as a **probabilistic boundary condition**, never as a deterministic forecast. Historical atmospheric couplings alter background probabilities of extreme weather; local topography, drainage culverts, elevation, and synoptic weather ultimately dictate on-the-ground outcomes.

---

## 2. Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                   AUTHORITATIVE EXTERNAL SOURCES                       │
│  NOAA Climate Prediction Center (CPC) · IRI Multi-Model Probability    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ ONI Time Series (ASCII)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       services/climate/ Module                         │
│                                                                        │
│  ┌──────────────────────┐              ┌────────────────────────────┐  │
│  │   enso_provider.py   │ ──(parse)──> │       enso_cache.py        │  │
│  │ NOAA ONI Ingestion   │              │ 6-Hour In-Memory TTL Cache │  │
│  │ Circuit Breaker      │              │ [CLIMATE] Observability    │  │
│  └──────────────────────┘              └─────────────┬──────────────┘  │
│                                                      │                 │
│                                                      ▼                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         enso_service.py                          │  │
│  │ Coordinates Cache, Live Ingestion, Baseline Fallback, Confidence │  │
│  └───────────────────────────────────┬──────────────────────────────┘  │
│                                      │                                 │
│                                      ▼                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    climate_impact_service.py                     │  │
│  │  calculateClimateImpact({ enso, location, season, context })     │  │
│  │  8-Sector Risk Engine · Teleconnection Wave Vector Generator     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        api/climate.py (FastAPI)                        │
│  GET /api/climate/enso        GET /api/climate/impact                  │
│  GET /api/climate/dna         GET /api/climate/timeline                │
│  POST /api/climate/simulate   GET /api/climate/teleconnection          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│       SHADOW AI AGENT ENGINE         │  │   FRONTEND USER INTERFACE    │
│ WeatherAI / FloodAI Context Source   │  │ ClimateDNACard (Widget)      │
│ Probabilistic Reasoning Prompts      │  │ ClimateDNAModal (Full Intel) │
│ Continuous city_clock.py Stream      │  │ ClimateTimeline (1950-2026)  │
│                                      │  │ ClimateScenarioPanel (Sim)   │
└──────────────────────────────────────┘  └──────────────────────────────┘
```

---

## 3. Data Schema & Models

### ENSO State Representation (`services/climate/enso_types.py`)

```typescript
type EnsoPhase = "EL_NINO" | "LA_NINA" | "NEUTRAL" | "UNKNOWN";
type EnsoIntensity = "WEAK" | "MODERATE" | "STRONG" | "UNKNOWN";
type ImpactLevel = "LOW" | "NORMAL" | "MODERATE" | "ELEVATED" | "HIGH" | "UNKNOWN";

interface EnsoDataModel {
  phase: EnsoPhase;
  intensity: EnsoIntensity;
  confidence: number;                  // 0.0 to 1.0
  anomaly: number | null;              // Niño-3.4 Sea Surface Temp Anomaly in °C
  observationPeriod: string | null;    // e.g. "2026-09"
  forecastPeriod: string | null;
  source: {
    name: string;
    url: string;
  };
  updatedAt: string;                   // ISO 8601 UTC
}
```

### Impact Response Envelope (`GET /api/climate/impact`)

```json
{
  "success": true,
  "data": {
    "city": "Chennai",
    "country": "India",
    "coordinates": [13.0827, 80.2707],
    "enso": {
      "phase": "LA_NINA",
      "intensity": "MODERATE"
    },
    "impacts": {
      "rainfall": {
        "level": "ELEVATED",
        "confidence": 0.71,
        "score": 68,
        "drivers": [
          "ENSO La Niña cooling anomaly",
          "Bay of Bengal easterly surges",
          "Northeast monsoon convection"
        ],
        "explanation": "La Niña statistically enhances easterly moisture flux into coastal peninsular India during post-monsoon..."
      },
      "flood": {
        "level": "MODERATE",
        "confidence": 0.66,
        "score": 55,
        "drivers": ["Saturated coastal catchments", "Elevation (6m AMSL)"],
        "explanation": "Increased frequency of convective cloudbursts heightens localized inundation risk."
      },
      "drought": {
        "level": "LOW",
        "confidence": 0.58,
        "score": 28,
        "drivers": ["Active aquifer recharge", "Healthy surface reservoir inflows"],
        "explanation": "Persistent moisture influx diminishes drought risk."
      },
      "heat": {
        "level": "MODERATE",
        "confidence": 0.61,
        "score": 50,
        "drivers": ["Diurnal solar cycle", "Urban heat island factor"],
        "explanation": "Ambient temperatures modulated by regional macro-weather patterns."
      },
      "waterStress": {
        "level": "LOW",
        "confidence": 0.64,
        "score": 35,
        "drivers": ["Ample raw water buffer in storage lakes"],
        "explanation": "Surface reservoirs balanced against municipal extraction."
      },
      "agriculture": {
        "level": "NORMAL",
        "confidence": 0.66,
        "score": 42,
        "drivers": ["Cropland soil moisture aligned with seasonal cropping calendars"],
        "explanation": "Soil moisture supports rainfed agricultural zones."
      },
      "infrastructure": {
        "level": "MODERATE",
        "confidence": 0.62,
        "score": 52,
        "drivers": ["Surface runoff load on stormwater networks"],
        "explanation": "High runoff volumes can strain low-lying drainage underpasses."
      }
    },
    "drivers": [
      "ENSO",
      "season",
      "regional climate relationship"
    ]
  }
}
```

---

## 4. API Reference

### 1. `GET /api/climate/enso`
- **Description:** Returns the normalized current ENSO status from authoritative NOAA CPC observations.
- **Cache:** 6 hours (`ENSO_CACHE_TTL=21600`).
- **Success (HTTP 200):**
  ```json
  {
    "success": true,
    "data": {
      "phase": "LA_NINA",
      "intensity": "MODERATE",
      "confidence": 0.82,
      "anomaly": -0.80,
      "observationPeriod": "2026-09",
      "source": {
        "name": "NOAA Climate Prediction Center (CPC)",
        "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
      },
      "updatedAt": "2026-09-22T00:00:00Z"
    }
  }
  ```
- **Error (HTTP 503):**
  ```json
  {
    "success": false,
    "error": {
      "code": "ENSO_DATA_UNAVAILABLE",
      "message": "ENSO data is temporarily unavailable."
    }
  }
  ```

### 2. `GET /api/climate/impact`
- **Parameters:**
  - `city` (string, optional, e.g. `Chennai`)
  - `lat` / `latitude` (float, -90 to 90)
  - `lng` / `longitude` (float, -180 to 180)
  - `country` (string, optional)
  - `elevation` (float, optional in meters)
- **Validation:** Returns HTTP 400 with `MISSING_CITY_OR_LOCATION` or `INVALID_COORDINATES` on invalid inputs.

### 3. `GET /api/climate/timeline`
- **Description:** Historical ENSO episodes (1950–2026) based on NOAA CPC ONI time series, plus IRI probabilistic multi-model outlooks.

### 4. `POST /api/climate/simulate`
- **Description:** Counterfactual "What-If" sensitivity analysis testing urban sectors against alternative ENSO phases (`EL_NINO`, `LA_NINA`, `NEUTRAL`).
- **Mandatory Disclaimer:** Returns `disclaimer: "SIMULATED SCENARIO — NOT A FORECAST"`.

---

## 5. Teleconnection Methodology

ENSO teleconnections propagate through atmospheric Rossby wave trains and Walker circulation displacements:

- **South Asia & Southeastern Peninsular India (e.g. Chennai):**
  - **La Niña:** Associated with normal to above-normal post-monsoon (October–December) rainfall, enhanced Bay of Bengal easterly moisture surges, and heightened short-duration cloudburst risks.
  - **El Niño:** Historical statistical correlations show higher propensity for monsoon rainfall deficits, elevated summertime maximum temperatures, and accelerated municipal reservoir drawdown.
- **Maritime Continent & Australia:**
  - **El Niño:** Strong atmospheric subsidence, suppressed convection, severe drought, and wildfire vulnerability.
  - **La Niña:** Warm pool thermal expansion, frequent monsoonal downpours, riverine flood hazards.
- **Pacific Coast of South America (Peru / Ecuador):**
  - **El Niño:** High positive SST anomalies off the coast cause extreme convective rainfall, mudslides, and flash flooding.
  - **La Niña:** Enhanced coastal upwelling, cold water stability, arid coastal conditions.

---

## 6. Observability & Logging

Structured logging format (Deliverable U):
```
[CLIMATE] ENSO provider request to NOAA CPC
[CLIMATE] ENSO cache hit
[CLIMATE] ENSO cache miss
[CLIMATE] ENSO provider failure: <error>
[CLIMATE] Impact calculated for city=Chennai
```
API keys, JWT tokens, and credentials are never logged.

---

## 7. Extension Points

1. **Indian Ocean Dipole (IOD):** Integration with real-time Dipole Mode Index (DMI) observations to model ENSO-IOD interference.
2. **Madden-Julian Oscillation (MJO):** Ingestion of Wheeler-Hendon index to resolve sub-seasonal 30–60 day tropical convective pulses.
3. **Hyperlocal Soil Hydrology:** Micro-catchment runoff modeling directly feeding into stormwater pump SCADA automation.
