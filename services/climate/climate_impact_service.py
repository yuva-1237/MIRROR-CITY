"""
services/climate/climate_impact_service.py — Scientific Climate Impact Assessment Engine

Translates large-scale ENSO ocean-atmosphere signals, seasonal patterns, and regional
teleconnections into structured urban risk indicators across 8 key sectors:
rainfall, flood, heat, drought, waterStress, agriculture, infrastructure.

Adheres strictly to probabilistic teleconnection science:
ENSO is treated as a probabilistic boundary condition rather than a deterministic forecast.
"""

import math
import logging
import datetime
from typing import Dict, Any, List, Optional
from services.climate.enso_types import EnsoPhase, EnsoIntensity, ImpactLevel

logger = logging.getLogger("climate.enso")


def get_current_season_name(month: Optional[int] = None) -> str:
    m = month or datetime.datetime.utcnow().month
    if m in [12, 1, 2]:
        return "DJF (Boreal Winter)"
    elif m in [3, 4, 5]:
        return "MAM (Boreal Spring)"
    elif m in [6, 7, 8]:
        return "JJA (Boreal Summer / SW Monsoon)"
    else:
        return "SON (Boreal Autumn / Post-Monsoon)"


class ClimateImpactService:
    def __init__(self):
        pass

    def calculate_climate_impact(
        self,
        enso: Dict[str, Any],
        location: Dict[str, Any],
        season: Optional[str] = None,
        regional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Public functional interface required by Deliverable G:
        calculateClimateImpact({ enso, location, season, regionalContext })

        Returns:
        {
            "rainfall": { level, confidence, drivers, explanation },
            "flood": { level, confidence, drivers, explanation },
            "drought": { level, confidence, drivers, explanation },
            "heat": { level, confidence, drivers, explanation },
            "waterStress": { level, confidence, drivers, explanation },
            "agriculture": { level, confidence, drivers, explanation },
            "infrastructure": { level, confidence, drivers, explanation }
        }
        """
        city_name = location.get("city", "Chennai")
        lat = float(location.get("latitude", location.get("lat", 13.0827)))
        lng = float(location.get("longitude", location.get("lng", 80.2707)))
        elevation = float(location.get("elevation", 20.0))
        country = location.get("country", regional_context.get("country") if regional_context else None)

        month = datetime.datetime.utcnow().month
        season_str = season or get_current_season_name(month)

        phase_raw = str(enso.get("phase", EnsoPhase.NEUTRAL.value)).upper()
        if "EL" in phase_raw:
            phase = EnsoPhase.EL_NINO
        elif "LA" in phase_raw:
            phase = EnsoPhase.LA_NINA
        elif "NEUTRAL" in phase_raw:
            phase = EnsoPhase.NEUTRAL
        else:
            phase = EnsoPhase.UNKNOWN

        intensity_raw = str(enso.get("intensity", EnsoIntensity.UNKNOWN.value)).upper()
        if "STRONG" in intensity_raw:
            intensity = EnsoIntensity.STRONG
        elif "MODERATE" in intensity_raw:
            intensity = EnsoIntensity.MODERATE
        elif "WEAK" in intensity_raw:
            intensity = EnsoIntensity.WEAK
        else:
            intensity = EnsoIntensity.UNKNOWN

        anomaly = float(enso.get("anomaly") or enso.get("anomaly_c") or 0.0)

        # Teleconnection domain resolution
        zone_info = self._resolve_teleconnection_zone(lat, lng, country)
        coupling = zone_info["coupling_factor"]

        # Multiplier based on ENSO strength
        if intensity == EnsoIntensity.STRONG:
            int_mult = 1.35
        elif intensity == EnsoIntensity.MODERATE:
            int_mult = 1.0
        elif intensity == EnsoIntensity.WEAK:
            int_mult = 0.70
        else:
            int_mult = 0.30 if phase == EnsoPhase.NEUTRAL else 0.50

        # Base scores (0-100)
        rf_score = 35.0
        fl_score = 25.0
        dr_score = 30.0
        ht_score = 40.0
        ws_score = 35.0
        ag_score = 35.0
        inf_score = 30.0

        rf_drivers = ["Seasonal baseline precipitation", "Geographic elevation profile"]
        fl_drivers = ["Catchment basin topography", f"Elevation ({int(elevation)}m AMSL)"]
        dr_drivers = ["Groundwater storage recharge rate", "Seasonal reservoir levels"]
        ht_drivers = ["Diurnal solar cycle", "Urban heat island factor"]
        ws_drivers = ["Municipal consumption baseline", "Piped distribution capacity"]
        ag_drivers = ["Regional soil moisture", "Irrigation reservoir reserves"]
        inf_drivers = ["Drainage culvert capacity", "Roadway thermal durability"]

        rf_expl = f"Precipitation patterns consistent with {season_str} baseline."
        fl_expl = "Runoff volume within municipal drainage design specifications."
        dr_expl = "Groundwater recharge and reservoir levels in expected seasonal band."
        ht_expl = "Ambient temperatures modulated by regional macro-weather patterns."
        ws_expl = "Municipal reservoir capacities balance urban consumption."
        ag_expl = "Cropland soil moisture aligned with seasonal cropping calendars."
        inf_expl = "Urban transit and stormwater networks operating at nominal load."

        # South Asia / India specific teleconnections
        if zone_info.get("is_india"):
            is_peninsular_east = zone_info.get("is_peninsular_east", False)
            if phase == EnsoPhase.LA_NINA:
                is_ne_monsoon = month in [9, 10, 11, 12]
                rf_shift = 32.0 * int_mult if is_ne_monsoon else 18.0 * int_mult
                fl_shift = 28.0 * int_mult if is_ne_monsoon else 15.0 * int_mult

                rf_score += rf_shift
                fl_score += fl_shift
                dr_score -= 18.0 * int_mult
                ws_score -= 15.0 * int_mult
                ht_score -= 10.0 * int_mult
                inf_score += 22.0 * int_mult

                rf_drivers = ["ENSO La Niña cooling anomaly", "Bay of Bengal easterly surges", "Northeast monsoon convection"]
                fl_drivers = ["Saturated coastal catchments", "High-intensity precipitation bursts", "Low-lying urban drainage pressure"]
                dr_drivers = ["Active aquifer recharge", "Healthy surface reservoir inflows"]
                ws_drivers = ["Ample raw water buffer in storage lakes"]
                inf_drivers = ["Hydraulic head on storm sewers", "Surface inundation along arterial transit routes"]

                rf_expl = (
                    f"La Niña ({intensity.value.lower()}) statistically enhances easterly wind flow and moisture flux into coastal "
                    f"peninsular India during the post-monsoon period, elevating rainfall probability."
                )
                fl_expl = "Increased frequency of intense rainfall spells heightens inundation probability in flood-prone micro-basins."
                dr_expl = "Persistent moisture influx diminishes agricultural and meteorological drought pressure."
                inf_expl = "High runoff volumes can strain stormwater pumps, underpasses, and arterial transport networks."

            elif phase == EnsoPhase.EL_NINO:
                dr_score += 28.0 * int_mult
                ws_score += 25.0 * int_mult
                ht_score += 22.0 * int_mult
                ag_score += 28.0 * int_mult
                rf_score -= 18.0 * int_mult
                fl_score -= 12.0 * int_mult

                rf_drivers = ["El Niño Pacific warming anomaly", "Suppressed Walker circulation ascending branch"]
                dr_drivers = ["Deficit monsoonal precipitation", "High soil moisture evaporation"]
                ht_drivers = ["Anomalous anticyclonic subsidence", "Reduced cloud cover and high solar insolation"]
                ws_drivers = ["Accelerated municipal reservoir depletion", "Declining groundwater tables"]

                rf_expl = "El Niño atmospheric teleconnections tend to weaken southwest monsoon wind shear, often shifting rainbands."
                dr_expl = "Historical El Niño episodes correlate with prolonged dry intervals and delayed reservoir replenishment."
                ht_expl = "Subsidence patterns promote elevated daytime surface temperatures and extended heatwave durations."

        elif zone_info["zone_id"] in ["maritime_continent", "australia"]:
            if phase == EnsoPhase.EL_NINO:
                dr_score += 35.0 * int_mult
                ht_score += 30.0 * int_mult
                ag_score += 32.0 * int_mult
                rf_score -= 25.0 * int_mult
                rf_drivers = ["El Niño descending Walker circulation", "Suppressed Indo-Pacific warm pool convection"]
                dr_drivers = ["Extended meteorological dry spells", "Wildfire and agricultural drought susceptibility"]
                rf_expl = "Descending atmospheric branch suppresses convective cloud development across the western Pacific."
            elif phase == EnsoPhase.LA_NINA:
                rf_score += 36.0 * int_mult
                fl_score += 34.0 * int_mult
                inf_score += 25.0 * int_mult
                rf_drivers = ["Warm pool thermal expansion", "Enhanced monsoonal convergence"]
                fl_drivers = ["Riverine overflow risk", "Catchment saturation"]
                rf_expl = "Concentrated western Pacific warm pool enhances deep tropical convective storm systems."

        elif zone_info["zone_id"] == "sa_pacific_coast":
            if phase == EnsoPhase.EL_NINO:
                rf_score += 45.0 * int_mult
                fl_score += 42.0 * int_mult
                inf_score += 35.0 * int_mult
                rf_drivers = ["Eastern equatorial Pacific warming", "Coastal atmospheric boundary layer instability"]
                fl_drivers = ["Torrential coastal runoff", "Mudslide and flash flood vulnerability"]
                rf_expl = "Warm ocean waters off western South America trigger intense convective coastal downpours."

        # Elevation impact on flood
        if elevation > 100.0:
            fl_score = max(10.0, fl_score - 15.0)
            fl_drivers.append(f"Topographical gravity drainage ({int(elevation)}m)")

        def format_sector(name: str, score: float, drivers: List[str], expl: str, base_conf: float) -> Dict[str, Any]:
            clamped = max(5.0, min(95.0, score))
            if clamped >= 70.0:
                lvl = ImpactLevel.ELEVATED if clamped < 85.0 else ImpactLevel.HIGH
            elif clamped >= 45.0:
                lvl = ImpactLevel.MODERATE
            else:
                lvl = ImpactLevel.LOW

            conf = round(min(0.92, max(0.55, base_conf * coupling)), 2)
            return {
                "level": lvl.value,
                "confidence": conf,
                "score": int(round(clamped)),
                "drivers": drivers[:4],
                "explanation": expl
            }

        impacts = {
            "rainfall": format_sector("rainfall", rf_score, rf_drivers, rf_expl, 0.82),
            "flood": format_sector("flood", fl_score, fl_drivers, fl_expl, 0.80),
            "drought": format_sector("drought", dr_score, dr_drivers, dr_expl, 0.75),
            "heat": format_sector("heat", ht_score, ht_drivers, ht_expl, 0.78),
            "waterStress": format_sector("waterStress", ws_score, ws_drivers, ws_expl, 0.74),
            "agriculture": format_sector("agriculture", ag_score, ag_drivers, ag_expl, 0.76),
            "infrastructure": format_sector("infrastructure", inf_score, inf_drivers, inf_expl, 0.72),
        }

        # Observability logging per Deliverable U
        logger.info(f"[CLIMATE] Impact calculated for city={city_name}")

        return impacts

    def _resolve_teleconnection_zone(
        self, lat: float, lng: float, country: Optional[str]
    ) -> Dict[str, Any]:
        text_context = (country or "").lower()
        if "india" in text_context or (6.0 <= lat <= 36.0 and 68.0 <= lng <= 98.0):
            is_peninsular_east = (8.0 <= lat <= 16.0 and 78.0 <= lng <= 82.0) or ("chennai" in text_context)
            return {
                "zone_id": "india_peninsular_east" if is_peninsular_east else "india_mainland",
                "name": "South Asian Monsoon & Indian Ocean Teleconnection Basin",
                "coupling_factor": 0.75,
                "is_india": True,
                "is_peninsular_east": is_peninsular_east
            }
        elif (-12.0 <= lat <= 22.0 and 95.0 <= lng <= 142.0):
            return {
                "zone_id": "maritime_continent",
                "name": "Equatorial Indo-Pacific Maritime Basin",
                "coupling_factor": 0.88,
                "is_india": False
            }
        elif (-55.0 <= lat <= 5.0 and -85.0 <= lng <= -68.0):
            return {
                "zone_id": "sa_pacific_coast",
                "name": "Eastern Pacific Coastal Upwelling & Humboldt Basin",
                "coupling_factor": 0.92,
                "is_india": False
            }
        elif (-45.0 <= lat <= -10.0 and 112.0 <= lng <= 155.0):
            return {
                "zone_id": "australia",
                "name": "Western Pacific Coral Sea & Australian Basin",
                "coupling_factor": 0.84,
                "is_india": False
            }
        return {
            "zone_id": "global_midlatitude",
            "name": "Global Mid-Latitude Atmospheric Wave Train Zone",
            "coupling_factor": 0.60,
            "is_india": False
        }


climate_impact_service = ClimateImpactService()
