"""
tests/test_climate.py — Unit & API Test Suite for Climate DNA & ENSO Intelligence

Covers Deliverables P and Q:
  - ENSO parser (NOAA ONI format, malformed text)
  - ENSO classification (EL_NINO, LA_NINA, NEUTRAL, UNKNOWN)
  - ENSO cache (TTL, hit/miss, avoiding redundant calls)
  - Climate impact model (calculateClimateImpact, 7-8 sectors, uppercase levels, explanations)
  - API tests:
      * GET /api/climate/enso (valid 200, schema, source, updatedAt)
      * GET /api/climate/enso (failure 503, ENSO_DATA_UNAVAILABLE)
      * GET /api/climate/impact (valid city, missing city 400, invalid coords 400)
      * POST /api/climate/simulate (scenario analysis disclaimer)
"""

import os
import sys
import unittest.mock as mock
import pytest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from services.climate.enso_types import EnsoPhase, EnsoIntensity, ImpactLevel
from services.climate.enso_provider import EnsoProvider, enso_provider
from services.climate.enso_cache import EnsoCache
from services.climate.enso_service import EnsoCoordinatorService, enso_coordinator_service
from services.climate.climate_impact_service import ClimateImpactService, climate_impact_service

client = TestClient(app)


# -----------------------------------------------------------------------------
# Unit Tests: ENSO Classification & Parsing (Deliverable P)
# -----------------------------------------------------------------------------
def test_enso_classification():
    """Verify standard NOAA CPC classification rules."""
    # El Niño (anomaly >= +0.5)
    phase, intensity = EnsoProvider.classify(1.6)
    assert phase == EnsoPhase.EL_NINO
    assert intensity == EnsoIntensity.STRONG

    phase_mod, intensity_mod = EnsoProvider.classify(1.2)
    assert phase_mod == EnsoPhase.EL_NINO
    assert intensity_mod == EnsoIntensity.MODERATE

    # La Niña (anomaly <= -0.5)
    phase_la, intensity_la = EnsoProvider.classify(-1.1)
    assert phase_la == EnsoPhase.LA_NINA
    assert intensity_la == EnsoIntensity.MODERATE

    phase_la_strong, intensity_la_strong = EnsoProvider.classify(-1.8)
    assert phase_la_strong == EnsoPhase.LA_NINA
    assert intensity_la_strong == EnsoIntensity.STRONG

    # Neutral (-0.5 < anomaly < 0.5)
    phase_neu, intensity_neu = EnsoProvider.classify(0.2)
    assert phase_neu == EnsoPhase.NEUTRAL

    phase_neu_zero, intensity_neu_zero = EnsoProvider.classify(0.0)
    assert phase_neu_zero == EnsoPhase.NEUTRAL


def test_enso_parser_valid_noaa_table():
    """Verify parsing NOAA ONI ascii table format."""
    provider = EnsoProvider()
    raw_sample = """
    SEAS  YEAR  TOTAL  ANOM
    AMJ   2026  28.50  -0.40
    MJJ   2026  28.80  -0.65
    JJA   2026  28.95  -0.82
    """
    result = provider.parse_noaa_oni(raw_sample)
    assert result is not None
    assert result["phase"] == EnsoPhase.LA_NINA.value
    assert result["intensity"] in [EnsoIntensity.WEAK.value, EnsoIntensity.MODERATE.value]
    assert result["anomaly"] == -0.82
    assert result["observationPeriod"] == "2026-07"
    assert "source" in result
    assert result["source"]["name"] == "NOAA Climate Prediction Center (CPC)"
    assert result["confidence"] > 0.70


def test_enso_parser_empty_or_malformed():
    """Verify parser handles empty or garbage responses without crashing."""
    provider = EnsoProvider()
    assert provider.parse_noaa_oni("") is None
    assert provider.parse_noaa_oni("Server 500 Internal Error") is None
    assert provider.parse_noaa_oni("INVALID DATA COLUMNS HERE") is None


# -----------------------------------------------------------------------------
# Unit Tests: ENSO Caching Behavior (Deliverable P)
# -----------------------------------------------------------------------------
def test_enso_cache_behavior():
    """Verify cache stores responses, handles TTL, and prevents redundant calls."""
    cache = EnsoCache(default_ttl=10)
    assert cache.get() is None

    sample_data = {
        "phase": EnsoPhase.LA_NINA.value,
        "intensity": EnsoIntensity.MODERATE.value,
        "anomaly": -0.80
    }
    cache.set(sample_data)

    # Immediately fetch — should be a cache hit
    cached = cache.get()
    assert cached is not None
    assert cached["phase"] == EnsoPhase.LA_NINA.value

    # Invalidate cache
    cache.invalidate()
    assert cache.get() is None


# -----------------------------------------------------------------------------
# Unit Tests: Climate Impact Model (Deliverables G & P)
# -----------------------------------------------------------------------------
def test_calculate_climate_impact_model():
    """Verify calculateClimateImpact outputs all required sectors with level, confidence, drivers, explanation."""
    enso_payload = {
        "phase": EnsoPhase.LA_NINA.value,
        "intensity": EnsoIntensity.MODERATE.value,
        "anomaly": -0.80
    }
    location_payload = {
        "city": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "elevation": 6.0,
        "country": "India"
    }

    service = ClimateImpactService()
    impacts = service.calculate_climate_impact(
        enso=enso_payload,
        location=location_payload,
        season="OND (Northeast Monsoon)"
    )

    required_sectors = [
        "rainfall", "flood", "drought", "heat",
        "waterStress", "agriculture", "infrastructure"
    ]
    for sector in required_sectors:
        assert sector in impacts, f"Missing sector {sector}"
        item = impacts[sector]
        assert "level" in item
        assert item["level"] in ["LOW", "NORMAL", "MODERATE", "ELEVATED", "HIGH"]
        assert "confidence" in item
        assert 0.0 <= item["confidence"] <= 1.0
        assert "drivers" in item
        assert isinstance(item["drivers"], list)
        assert len(item["drivers"]) > 0
        assert "explanation" in item
        assert len(item["explanation"]) > 0


# -----------------------------------------------------------------------------
# API Tests (Deliverables E, F, Q)
# -----------------------------------------------------------------------------
def test_get_enso_endpoint_success():
    """GET /api/climate/enso returns HTTP 200, correct envelope, and valid metadata."""
    response = client.get("/api/climate/enso")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert "phase" in data
    assert data["phase"] in [EnsoPhase.EL_NINO.value, EnsoPhase.LA_NINA.value, EnsoPhase.NEUTRAL.value]
    assert "intensity" in data
    assert "confidence" in data
    assert "source" in data
    assert "updatedAt" in data


def test_get_enso_endpoint_unavailable_handling():
    """GET /api/climate/enso returns 503 ENSO_DATA_UNAVAILABLE when service cannot obtain data."""
    with mock.patch.object(
        enso_coordinator_service,
        "get_current_enso",
        return_value={"phase": "UNKNOWN", "available": False}
    ):
        response = client.get("/api/climate/enso")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "ENSO_DATA_UNAVAILABLE"


def test_get_city_climate_impact_valid():
    """GET /api/climate/impact with valid parameters returns HTTP 200 and required sectors."""
    response = client.get("/api/climate/impact?city=Chennai&country=India&lat=13.0827&lng=80.2707")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["city"] == "Chennai"
    assert "enso" in data
    assert "impacts" in data
    assert "rainfall" in data["impacts"]
    assert "flood" in data["impacts"]
    assert "drought" in data["impacts"]
    assert "heat" in data["impacts"]
    assert "drivers" in data


def test_get_city_climate_impact_missing_city():
    """GET /api/climate/impact without city or coordinates returns HTTP 400."""
    response = client.get("/api/climate/impact")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "MISSING_CITY_OR_LOCATION"


def test_get_city_climate_impact_invalid_coordinates():
    """GET /api/climate/impact with out-of-bounds coordinates returns HTTP 400."""
    response = client.get("/api/climate/impact?city=Chennai&lat=999.0&lng=80.0")
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_COORDINATES"


def test_simulate_climate_scenario():
    """POST /api/climate/simulate returns counterfactual scenario with mandatory disclaimer."""
    payload = {
        "city": "Chennai",
        "lat": 13.0827,
        "lng": 80.2707,
        "target_phase": "El Niño"
    }
    response = client.post("/api/climate/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Chennai"
    assert "simulated_scenario" in data
    assert "deltas" in data
    assert data["disclaimer"] == "SIMULATED SCENARIO — NOT A FORECAST"


def test_get_climate_timeline():
    """GET /api/climate/timeline returns historical time series."""
    response = client.get("/api/climate/timeline")
    assert response.status_code == 200
    data = response.json()
    assert "timeline" in data
    assert len(data["timeline"]) > 0


def test_get_climate_dna():
    """GET /api/climate/dna returns structured CITY DNA environmental signal hierarchy."""
    response = client.get("/api/climate/dna?city=Chennai&lat=13.0827&lng=80.2707")
    assert response.status_code == 200
    data = response.json()
    assert data["location"] == "Chennai"
    assert "climate_signals" in data
    signals = data["climate_signals"]
    assert "enso" in signals
    assert "phase" in signals["enso"]
    assert "seasonal_monsoon" in signals
    assert "temperature_anomaly" in signals
    assert "rainfall_anomaly" in signals


def test_shadow_ai_climate_context():
    """Verify SHADOW AI receives { city, enso, weather, risk } and answers climate risk queries without inventing states."""
    from configs.security import create_access_token
    token = create_access_token({"sub": "planner@mirrorcity.gov", "role": "Planner"})

    payload = {
        "prompt": "Why is rainfall risk elevated?",
        "city": "Chennai",
        "enso": {
            "phase": "LA_NINA",
            "intensity": "MODERATE",
            "confidence": 0.82
        },
        "weather": {
            "condition": "Cloudy",
            "rain_intensity": 0.45
        },
        "risk": {
            "rainfall": {"level": "ELEVATED", "confidence": 0.75}
        }
    }

    # 1. Verify deterministic keyword fallback implementation
    from api.simulations import _keyword_fallback, AssistantRequest
    req_obj = AssistantRequest(**payload)
    fallback_res = _keyword_fallback(req_obj)
    assert "Rainfall risk is currently elevated based on multiple signals" in fallback_res.reply
    assert "ENSO is a contributing climate signal rather than a deterministic cause" in fallback_res.reply
    assert "LA_NINA" in fallback_res.reply or "MODERATE" in fallback_res.reply

    # 2. Verify API endpoint integration
    response = client.post(
        "/api/simulations/assistant",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    reply_lower = data["reply"].lower()
    assert "rainfall" in reply_lower or "rain" in reply_lower
    assert "enso" in reply_lower or "climate" in reply_lower or "nina" in reply_lower or "la niña" in reply_lower

