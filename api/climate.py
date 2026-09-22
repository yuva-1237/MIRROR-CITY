"""
api/climate.py — ENSO & Climate Intelligence Endpoints for MIRROR CITY

Endpoints:
  GET  /api/climate/enso            — Current normalized ENSO state from NOAA CPC
  GET  /api/climate/impact          — City-specific teleconnection & 8-risk profile
  GET  /api/climate/dna             — Structured CITY DNA climate signal hierarchy
  GET  /api/climate/timeline        — Historical ENSO timeline (1950-2026) & forecast outlook
  POST /api/climate/simulate        — Counterfactual "What If?" climate scenario simulator
  GET  /api/climate/teleconnection  — Pacific anomaly coords & propagation lines
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.enso_service import enso_service
from services.city_impact_engine import city_impact_engine
from simulation.continuous_engine import continuous_engine

router = APIRouter(prefix="/climate", tags=["climate"])


class SimulateRequest(BaseModel):
    city: str = "Chennai"
    lat: Optional[float] = None
    lng: Optional[float] = None
    target_phase: str = "El Niño"  # "El Niño" | "La Niña" | "Neutral"
    elevation: Optional[float] = 20.0


def _resolve_coordinates(city: str, lat: Optional[float], lng: Optional[float], elevation: Optional[float]):
    """Helper to resolve coordinates using active city twin if not provided."""
    active_city = continuous_engine.active_city_metadata or {}
    resolved_city = city or active_city.get("name", "Chennai")

    if lat is not None and lng is not None:
        return resolved_city, lat, lng, elevation or 20.0, active_city.get("hierarchy", [])

    # If coordinates match active city, use them
    if active_city.get("lat") and active_city.get("lng") and (not city or city.lower() in active_city.get("name", "").lower()):
        return (
            active_city.get("name", resolved_city),
            active_city["lat"],
            active_city["lng"],
            active_city.get("elevation", 20.0),
            active_city.get("hierarchy", [])
        )

    # Defaults for well-known smart city presets
    presets = {
        "chennai": (13.0827, 80.2707, 6.0, ["India", "Tamil Nadu", "Chennai"]),
        "mumbai": (19.0760, 72.8777, 14.0, ["India", "Maharashtra", "Mumbai"]),
        "delhi": (28.6139, 77.2090, 216.0, ["India", "Delhi", "New Delhi"]),
        "bengaluru": (12.9716, 77.5946, 920.0, ["India", "Karnataka", "Bengaluru"]),
        "san francisco": (37.7749, -122.4194, 16.0, ["United States", "California", "San Francisco"]),
        "sydney": (-33.8688, 151.2093, 19.0, ["Australia", "New South Wales", "Sydney"]),
        "lima": (-12.0464, -77.0428, 154.0, ["Peru", "Lima", "Lima Province"]),
        "tokyo": (35.6762, 139.6503, 40.0, ["Japan", "Kanto", "Tokyo"]),
        "london": (51.5074, -0.1278, 25.0, ["United Kingdom", "England", "London"]),
    }

    match_preset = presets.get(resolved_city.lower().strip())
    if match_preset:
        p_lat, p_lng, p_elev, p_hier = match_preset
        return resolved_city, p_lat, p_lng, elevation or p_elev, p_hier

    # Standard fallback
    return resolved_city, 13.0827, 80.2707, elevation or 20.0, ["India", "Tamil Nadu", "Chennai"]


from fastapi.responses import JSONResponse
from services.climate import enso_coordinator_service, climate_impact_service

@router.get("/enso")
def get_enso_status():
    """
    Returns normalized ENSO status from authoritative NOAA CPC observations.
    Cached with ENSO_CACHE_TTL (6 hours) to prevent excessive external requests.
    Envelope: { success: true, data: { phase, intensity, confidence, observationPeriod, source, updatedAt } }
    """
    enso_data = enso_coordinator_service.get_current_enso()
    if not enso_data or not enso_data.get("available", True) or enso_data.get("phase") == "UNKNOWN":
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "ENSO_DATA_UNAVAILABLE",
                    "message": "ENSO data is temporarily unavailable."
                }
            }
        )

    # Return normalized payload per Deliverable E
    data_payload = {
        "phase": enso_data.get("phase", "NEUTRAL"),
        "intensity": enso_data.get("intensity", "WEAK"),
        "confidence": enso_data.get("confidence", 0.82),
        "anomaly": enso_data.get("anomaly"),
        "observationPeriod": enso_data.get("observationPeriod", "2026-09"),
        "forecastPeriod": enso_data.get("forecastPeriod"),
        "source": enso_data.get("source", {
            "name": "NOAA Climate Prediction Center (CPC)",
            "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
        }),
        "updatedAt": enso_data.get("updatedAt", "")
    }

    # Include auxiliary fields if available (soi, sstObserved, etc.)
    if "soi" in enso_data:
        data_payload["soi"] = enso_data["soi"]
    if "sstObserved" in enso_data:
        data_payload["sstObserved"] = enso_data["sstObserved"]

    return {
        "success": True,
        "data": data_payload
    }


@router.get("/impact")
def get_city_climate_impact(
    city: Optional[str] = Query(None, description="City name"),
    lat: Optional[float] = Query(None, description="Latitude"),
    latitude: Optional[float] = Query(None, description="Latitude alias"),
    lng: Optional[float] = Query(None, description="Longitude"),
    longitude: Optional[float] = Query(None, description="Longitude alias"),
    country: Optional[str] = Query(None, description="Country name"),
    elevation: Optional[float] = Query(None, description="Elevation in meters")
):
    """
    Returns city-level climate impact assessment, regional teleconnection response,
    and multi-sector risk indicators per Deliverable F.
    """
    eff_lat = latitude if latitude is not None else lat
    eff_lng = longitude if longitude is not None else lng

    # Validate coordinates if provided
    if eff_lat is not None and not (-90.0 <= eff_lat <= 90.0):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_COORDINATES",
                    "message": "Latitude must be between -90 and 90."
                }
            }
        )
    if eff_lng is not None and not (-180.0 <= eff_lng <= 180.0):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "INVALID_COORDINATES",
                    "message": "Longitude must be between -180 and 180."
                }
            }
        )

    # If city is missing and coordinates missing, return validation error
    if not city and eff_lat is None and eff_lng is None:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "MISSING_CITY_OR_LOCATION",
                    "message": "Either city or latitude/longitude must be provided."
                }
            }
        )

    res_city, r_lat, r_lng, r_elev, r_hier = _resolve_coordinates(city or "Chennai", eff_lat, eff_lng, elevation)

    # Check ENSO data availability
    enso_data = enso_coordinator_service.get_current_enso()
    if not enso_data or not enso_data.get("available", True):
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "ENSO_DATA_UNAVAILABLE",
                    "message": "ENSO data is temporarily unavailable to calculate impact."
                }
            }
        )

    # Use climate_impact_service for calculation
    location_payload = {
        "city": res_city,
        "lat": r_lat,
        "lng": r_lng,
        "elevation": r_elev,
        "country": country
    }
    sector_impacts = climate_impact_service.calculate_climate_impact(
        enso=enso_data,
        location=location_payload,
        regional_context={"country": country, "hierarchy": r_hier}
    )

    # Also evaluate full city twin payload for frontend visualization
    full_eval = city_impact_engine.evaluate_city_impact(
        city_name=res_city,
        lat=r_lat,
        lng=r_lng,
        elevation=r_elev,
        country=country,
        hierarchy=r_hier,
        custom_enso=enso_data
    )

    response_data = {
        "city": res_city,
        "country": country or (r_hier[0] if r_hier else "India"),
        "coordinates": [r_lat, r_lng],
        "enso": {
            "phase": enso_data.get("phase", "NEUTRAL"),
            "intensity": enso_data.get("intensity", "MODERATE")
        },
        "impacts": sector_impacts,
        "drivers": [
            "ENSO",
            "season",
            "regional climate relationship"
        ],
        "climate_dna": full_eval.get("climate_dna"),
        "teleconnection": full_eval.get("teleconnection"),
        "summary_rationale": full_eval.get("summary_rationale")
    }

    return {
        "success": True,
        "data": response_data
    }



@router.get("/dna")
def get_climate_dna(
    city: str = Query("Chennai", description="City name"),
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    elevation: Optional[float] = Query(None, description="Elevation in meters")
):
    """
    Returns the structured CITY DNA environmental signal hierarchy:
    Location > ENSO > Indian Ocean Dipole > Seasonal Monsoon > Temp & Rain Anomaly.
    """
    res_city, r_lat, r_lng, r_elev, r_hier = _resolve_coordinates(city, lat, lng, elevation)
    impact_data = city_impact_engine.evaluate_city_impact(
        city_name=res_city,
        lat=r_lat,
        lng=r_lng,
        elevation=r_elev,
        hierarchy=r_hier
    )
    return impact_data["climate_dna"]


@router.get("/timeline")
def get_climate_timeline():
    """
    Returns historical ENSO timeline (from NOAA CPC ONI time series 1950-2026)
    and IRI/CPC multi-model probabilistic seasonal outlook.
    """
    return enso_service.get_timeline()


@router.post("/simulate")
def simulate_climate_scenario(req: SimulateRequest):
    """
    Simulates a counterfactual climate scenario (e.g. Current state -> El Niño / La Niña).
    Clearly labeled: SIMULATED SCENARIO — NOT A FORECAST.
    """
    res_city, r_lat, r_lng, r_elev, r_hier = _resolve_coordinates(req.city, req.lat, req.lng, req.elevation)
    return city_impact_engine.simulate_scenario(
        city_name=res_city,
        lat=r_lat,
        lng=r_lng,
        target_phase=req.target_phase,
        elevation=r_elev,
        hierarchy=r_hier
    )


@router.get("/teleconnection")
def get_teleconnection_visuals(
    lat: float = Query(13.0827, description="City Latitude"),
    lng: float = Query(80.2707, description="City Longitude"),
    city: str = Query("Chennai", description="City name")
):
    """
    Returns Pacific Ocean Nino centroids and atmospheric teleconnection wave coordinates
    connecting the Pacific Ocean to the selected city.
    """
    enso = enso_service.get_current_enso()
    region_info = city_impact_engine._resolve_teleconnection_zone(lat, lng, None, None)
    return city_impact_engine._compute_teleconnection_link(lat, lng, region_info, enso)
