"""
services/city_impact_engine.py — City-Level Climate Impact & Risk Engine

Translates global ENSO ocean-atmosphere signals (El Niño, La Niña, Neutral)
into localized, probabilistic urban risk indicators, CITY DNA environmental profiles,
and counterfactual "What If?" simulations.

Key Rule: Strictly probabilistic language (e.g. "Historical patterns associated with
La Niña can increase rainfall risk in some regions"). Never claims deterministic causality.
"""

import math
import datetime
from typing import Dict, Any, List, Optional
from services.enso_service import enso_service

class CityImpactEngine:
    def __init__(self):
        pass

    # -------------------------------------------------------------------------
    # Main Public Assessment
    # -------------------------------------------------------------------------
    def evaluate_city_impact(
        self,
        city_name: str,
        lat: float,
        lng: float,
        elevation: float = 20.0,
        country: Optional[str] = None,
        hierarchy: Optional[List[str]] = None,
        custom_enso: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the local climate response of a city to the active ENSO state.
        """
        enso = custom_enso or enso_service.get_current_enso()
        phase = enso.get("phase", "Neutral")
        intensity = enso.get("intensity", "Neutral")
        anomaly = enso.get("anomaly_c", 0.0)
        
        # Determine region & teleconnection regime
        region_info = self._resolve_teleconnection_zone(lat, lng, country, hierarchy)
        current_month = datetime.datetime.utcnow().month

        # Calculate the 8 urban risk vectors
        risks = self._compute_risk_vectors(phase, intensity, anomaly, region_info, current_month, elevation)

        # Build CITY DNA climate signal hierarchy
        climate_dna = self._build_climate_dna(city_name, region_info, enso, risks, current_month)

        # Teleconnection propagation paths from Pacific
        teleconnection = self._compute_teleconnection_link(lat, lng, region_info, enso)

        return {
            "city": city_name,
            "coordinates": [lat, lng],
            "elevation": elevation,
            "region": region_info["name"],
            "enso": {
                "phase": phase,
                "intensity": intensity,
                "anomaly_c": anomaly,
                "confidence": enso.get("confidence", 0.82),
                "source": enso.get("source", "NOAA CPC"),
                "updatedAt": enso.get("updatedAt", "")
            },
            "impacts": risks,
            "climate_dna": climate_dna,
            "teleconnection": teleconnection,
            "summary_rationale": self._generate_probabilistic_summary(city_name, phase, intensity, region_info, risks)
        }

    # -------------------------------------------------------------------------
    # "What If?" Counterfactual Simulation Engine
    # -------------------------------------------------------------------------
    def simulate_scenario(
        self,
        city_name: str,
        lat: float,
        lng: float,
        target_phase: str,
        elevation: float = 20.0,
        country: Optional[str] = None,
        hierarchy: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Simulates an alternative climate scenario (e.g. Current Neutral -> El Niño).
        Returns delta shifts across key municipal sectors with mandatory disclaimer.
        """
        current_enso = enso_service.get_current_enso()
        current_eval = self.evaluate_city_impact(city_name, lat, lng, elevation, country, hierarchy, custom_enso=current_enso)

        # Synthesize target ENSO parameters
        target_phase_clean = "El Niño" if "el" in target_phase.lower() else ("La Niña" if "la" in target_phase.lower() else "Neutral")
        mock_anomaly = 1.8 if target_phase_clean == "El Niño" else (-1.4 if target_phase_clean == "La Niña" else 0.0)
        mock_intensity = "Moderate" if abs(mock_anomaly) >= 1.0 else "Neutral"
        
        simulated_enso = {
            "phase": target_phase_clean,
            "intensity": mock_intensity,
            "anomaly_c": mock_anomaly,
            "confidence": 0.85,
            "soi": -1.1 if target_phase_clean == "El Niño" else (1.1 if target_phase_clean == "La Niña" else 0.0),
            "source": "MIRROR CITY Counterfactual Simulation Model",
            "updatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d")
        }

        sim_eval = self.evaluate_city_impact(city_name, lat, lng, elevation, country, hierarchy, custom_enso=simulated_enso)

        # Sectoral delta calculations
        curr_impacts = current_eval["impacts"]
        sim_impacts = sim_eval["impacts"]

        deltas = {}
        for key in ["rainfall", "flood", "heat", "drought", "water_stress", "energy_demand", "infrastructure", "agriculture"]:
            curr_score = curr_impacts[key]["score"]
            sim_score = sim_impacts[key]["score"]
            diff = sim_score - curr_score
            deltas[key] = {
                "current_level": curr_impacts[key]["level"],
                "simulated_level": sim_impacts[key]["level"],
                "current_score": curr_score,
                "simulated_score": sim_score,
                "delta": diff,
                "trend": "↑" if diff > 5 else ("↓" if diff < -5 else "→"),
                "direction": "up" if diff > 5 else ("down" if diff < -5 else "neutral")
            }

        return {
            "city": city_name,
            "baseline_enso": current_eval["enso"],
            "simulated_scenario": simulated_enso,
            "deltas": deltas,
            "disclaimer": "SIMULATED SCENARIO — NOT A FORECAST",
            "narrative": (
                f"Under a simulated {target_phase_clean} scenario, historical statistical couplings suggest "
                f"rainfall variability would trend {deltas['rainfall']['trend']} ({deltas['rainfall']['delta']:+d} pts), "
                f"drought pressure would trend {deltas['drought']['trend']}, and municipal water stress would trend "
                f"{deltas['water_stress']['trend']} for {city_name}. This sensitivity analysis tests infrastructure resiliency."
            )
        }

    # -------------------------------------------------------------------------
    # Teleconnection Resolution
    # -------------------------------------------------------------------------
    def _resolve_teleconnection_zone(
        self, lat: float, lng: float, country: Optional[str], hierarchy: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Resolves the regional climatological zone and teleconnection coupling characteristics."""
        text_context = f"{country or ''} {' '.join(hierarchy or [])}".lower()

        # India / South Asia
        if "india" in text_context or (6.0 <= lat <= 36.0 and 68.0 <= lng <= 98.0):
            # Differentiate coastal southeastern India (e.g. Chennai / Tamil Nadu) from Northwest
            is_peninsular_east = (8.0 <= lat <= 16.0 and 78.0 <= lng <= 82.0) or ("chennai" in text_context or "tamil" in text_context)
            return {
                "zone_id": "india_peninsular_east" if is_peninsular_east else "india_mainland",
                "name": "South Asian Monsoon & Indian Ocean Teleconnection Basin",
                "coupling_factor": 0.72,
                "is_india": True,
                "is_peninsular_east": is_peninsular_east
            }

        # Southeast Asia & Maritime Continent (Indonesia, Philippines, Singapore, Malaysia, Vietnam)
        if (-12.0 <= lat <= 22.0 and 95.0 <= lng <= 142.0):
            return {
                "zone_id": "maritime_continent",
                "name": "Equatorial Indo-Pacific Maritime Basin",
                "coupling_factor": 0.88,
                "is_india": False
            }

        # North America - West Coast & Southwest (California, Oregon, Washington, Arizona)
        if (25.0 <= lat <= 50.0 and -128.0 <= lng <= -110.0):
            return {
                "zone_id": "na_pacific_coast",
                "name": "North Pacific Jet Stream & West Coast Basin",
                "coupling_factor": 0.78,
                "is_india": False
            }

        # North America - Southern Tier & Gulf (Texas, Florida, Gulf of Mexico)
        if (24.0 <= lat <= 35.0 and -110.0 <= lng <= -75.0):
            return {
                "zone_id": "na_southern_tier",
                "name": "Subtropical Jet Stream & Gulf Teleconnection Basin",
                "coupling_factor": 0.75,
                "is_india": False
            }

        # South America - Pacific Coast (Peru, Ecuador, Chile)
        if (-55.0 <= lat <= 5.0 and -85.0 <= lng <= -68.0):
            return {
                "zone_id": "sa_pacific_coast",
                "name": "Eastern Pacific Coastal Upwelling & Humboldt Basin",
                "coupling_factor": 0.92,
                "is_india": False
            }

        # Australia & South Pacific
        if (-45.0 <= lat <= -10.0 and 112.0 <= lng <= 155.0):
            return {
                "zone_id": "australia",
                "name": "Western Pacific Coral Sea & Australian Basin",
                "coupling_factor": 0.84,
                "is_india": False
            }

        # East Africa
        if (-12.0 <= lat <= 15.0 and 28.0 <= lng <= 52.0):
            return {
                "zone_id": "east_africa",
                "name": "Equatorial East Africa Teleconnection Basin",
                "coupling_factor": 0.76,
                "is_india": False
            }

        # Default Global Mid-Latitudes
        return {
            "zone_id": "global_midlatitude",
            "name": "Global Mid-Latitude Atmospheric Wave Train Zone",
            "coupling_factor": 0.50,
            "is_india": False
        }

    # -------------------------------------------------------------------------
    # 8-Sector Risk Engine
    # -------------------------------------------------------------------------
    def _compute_risk_vectors(
        self,
        phase: str,
        intensity: str,
        anomaly: float,
        region: Dict[str, Any],
        month: int,
        elevation: float
    ) -> Dict[str, Dict[str, Any]]:
        """
        Computes the 8 core urban risk indicators:
        Rainfall, Flood, Heat, Drought, Water Stress, Energy Demand, Infrastructure, Agriculture.
        """
        intensity_mult = 1.3 if intensity in ["Strong", "Very Strong"] else (1.0 if intensity == "Moderate" else 0.7)
        if phase == "Neutral":
            intensity_mult = 0.3

        zone_id = region["zone_id"]
        c_factor = region["coupling_factor"]

        # Base scores (0 - 100)
        # Default baseline under neutral conditions
        rf_score = 35.0
        fl_score = 25.0
        ht_score = 40.0
        dr_score = 30.0
        ws_score = 35.0
        en_score = 42.0
        inf_score = 30.0
        ag_score = 35.0

        rf_drivers = ["Seasonal baseline precipitation", "Geographic elevation profile"]
        fl_drivers = ["Catchment basin topography", f"Elevation ({int(elevation)}m AMSL)"]
        ht_drivers = ["Diurnal solar cycle", "Urban heat island factor"]
        dr_drivers = ["Groundwater storage recharge rate", "Seasonal reservoir levels"]
        ws_drivers = ["Municipal consumption baseline", "Piped distribution capacity"]
        en_drivers = ["HVAC cooling baseline", "Industrial grid demand"]
        inf_drivers = ["Drainage culvert capacity", "Roadway thermal durability"]
        ag_drivers = ["Regional soil moisture", "Irrigation reservoir reserves"]

        # Regional Teleconnection Matrix
        if region.get("is_india"):
            if phase == "La Niña":
                # In India, La Niña is statistically associated with normal-to-above-normal rainfall
                # For southeastern peninsular India (Chennai), Oct-Dec northeast monsoon is often intense
                is_ne_monsoon = (month in [10, 11, 12, 9])
                rf_shift = 32.0 * intensity_mult if is_ne_monsoon else 18.0 * intensity_mult
                fl_shift = 30.0 * intensity_mult if is_ne_monsoon else 15.0 * intensity_mult
                
                rf_score += rf_shift
                fl_score += fl_shift
                dr_score -= 18.0 * intensity_mult
                ws_score -= 15.0 * intensity_mult
                ht_score -= 10.0 * intensity_mult
                inf_score += 22.0 * intensity_mult

                rf_drivers.insert(0, f"La Niña Pacific cooling signal ({anomaly:.2f}°C)")
                rf_drivers.insert(1, "Enhanced Bay of Bengal easterly wind surges")
                fl_drivers.insert(0, "Elevated probability of intense convective cloudbursts")
                fl_drivers.insert(1, "Saturated coastal catchment retention soils")
                inf_drivers.insert(0, "Surface runoff load on municipal drainage network")
            elif phase == "El Niño":
                # In India, El Niño correlates with higher probability of summer monsoon rainfall deficits, though IOD can mitigate
                dr_score += 28.0 * intensity_mult
                ws_score += 25.0 * intensity_mult
                ht_score += 22.0 * intensity_mult
                ag_score += 30.0 * intensity_mult
                rf_score -= 18.0 * intensity_mult
                fl_score -= 12.0 * intensity_mult
                en_score += 24.0 * intensity_mult

                dr_drivers.insert(0, f"El Niño Pacific heating signal (+{anomaly:.2f}°C)")
                dr_drivers.insert(1, "Suppressed summer monsoon convection across peninsular India")
                ht_drivers.insert(0, "Elevated regional surface temperature anomalies")
                ws_drivers.insert(0, "Higher reservoir evaporation and depletion velocity")
                ag_drivers.insert(0, "Rainfed crop moisture stress vulnerability")
            else:
                rf_drivers.insert(0, "ENSO Neutral equatorial Pacific conditions")

        elif zone_id in ["maritime_continent", "australia"]:
            if phase == "El Niño":
                dr_score += 38.0 * intensity_mult
                ht_score += 30.0 * intensity_mult
                ag_score += 35.0 * intensity_mult
                ws_score += 32.0 * intensity_mult
                rf_score -= 25.0 * intensity_mult
                fl_score -= 18.0 * intensity_mult
                dr_drivers.insert(0, f"El Niño descending Walker circulation branch (+{anomaly:.2f}°C)")
                ht_drivers.insert(0, "Atmospheric subsidence and elevated clear-sky solar insolation")
            elif phase == "La Niña":
                rf_score += 38.0 * intensity_mult
                fl_score += 36.0 * intensity_mult
                inf_score += 26.0 * intensity_mult
                dr_score -= 22.0 * intensity_mult
                rf_drivers.insert(0, f"La Niña enhanced western Pacific warm pool convection ({anomaly:.2f}°C)")
                fl_drivers.insert(0, "Persistent multi-day monsoonal downpours")

        elif zone_id in ["sa_pacific_coast"]:
            if phase == "El Niño":
                rf_score += 48.0 * intensity_mult
                fl_score += 46.0 * intensity_mult
                inf_score += 38.0 * intensity_mult
                rf_drivers.insert(0, f"Intense Eastern Pacific equatorial warming (+{anomaly:.2f}°C)")
                fl_drivers.insert(0, "Coastal storm surge and torrential coastal precipitation")
            elif phase == "La Niña":
                dr_score += 32.0 * intensity_mult
                ht_score -= 12.0 * intensity_mult

        elif zone_id in ["na_pacific_coast", "na_southern_tier"]:
            if phase == "El Niño":
                rf_score += 22.0 * intensity_mult
                fl_score += 20.0 * intensity_mult
                en_score += 15.0 * intensity_mult
                rf_drivers.insert(0, f"Subtropical Pacific jet stream displacement (+{anomaly:.2f}°C)")
            elif phase == "La Niña":
                dr_score += 26.0 * intensity_mult
                ht_score += 20.0 * intensity_mult
                ws_score += 20.0 * intensity_mult
                dr_drivers.insert(0, f"La Niña northward-shifted storm track ({anomaly:.2f}°C)")

        else: # Global mid-latitude
            if phase != "Neutral":
                rf_score += 10.0 * intensity_mult
                ht_score += 10.0 * intensity_mult
                rf_drivers.insert(0, f"Rossby wave atmospheric teleconnection ({phase})")

        # Elevation mitigation on flood risk
        if elevation > 100.0:
            fl_score = max(10.0, fl_score - 14.0)
            fl_drivers.append(f"Topographical drainage gradient ({int(elevation)}m)")

        # Clamp and assemble risk dictionaries
        def package_risk(risk_name: str, score_val: float, drivers_list: List[str], conf_base: float) -> Dict[str, Any]:
            clamped = max(5.0, min(95.0, score_val))
            if clamped >= 70.0:
                lvl = "elevated" if clamped < 85.0 else "high"
            elif clamped >= 45.0:
                lvl = "moderate"
            else:
                lvl = "low"

            conf = round(min(0.92, max(0.55, conf_base * c_factor)), 2)
            return {
                "risk": risk_name,
                "level": lvl,
                "score": int(round(clamped)),
                "confidence": conf,
                "drivers": drivers_list[:4]
            }

        return {
            "rainfall": package_risk("rainfall", rf_score, rf_drivers, 0.82),
            "flood": package_risk("flood", fl_score, fl_drivers, 0.80),
            "heat": package_risk("heat", ht_score, ht_drivers, 0.78),
            "drought": package_risk("drought", dr_score, dr_drivers, 0.75),
            "water_stress": package_risk("water_stress", ws_score, ws_drivers, 0.74),
            "energy_demand": package_risk("energy_demand", en_score, en_drivers, 0.70),
            "infrastructure": package_risk("infrastructure", inf_score, inf_drivers, 0.72),
            "agriculture": package_risk("agriculture", ag_score, ag_drivers, 0.76),
        }

    # -------------------------------------------------------------------------
    # CITY DNA Hierarchy Generator
    # -------------------------------------------------------------------------
    def _build_climate_dna(
        self,
        city_name: str,
        region: Dict[str, Any],
        enso: Dict[str, Any],
        risks: Dict[str, Any],
        month: int
    ) -> Dict[str, Any]:
        """Constructs the structured environmental signal tree for CITY DNA."""
        phase = enso.get("phase", "Neutral")
        anomaly = enso.get("anomaly_c", 0.0)

        # Indian Ocean Dipole (IOD) status
        # Typically neutral or weakly coupled
        iod_status = "Neutral (+0.12°C)"
        if phase == "El Niño":
            iod_status = "Positive Phase Tendency (East Indian Ocean cooling, West warming)"
        elif phase == "La Niña":
            iod_status = "Negative Phase Tendency (Enhanced eastern Indian Ocean convection)"

        # Seasonal Monsoon / Climatology
        if region.get("is_india"):
            if month in [6, 7, 8, 9]:
                monsoon_regime = "Southwest Monsoon (Kharif Season)"
            elif month in [10, 11, 12]:
                monsoon_regime = "Northeast Retreating Monsoon (Coastal Peninsular Peak)"
            else:
                monsoon_regime = "Dry Pre-Monsoon / Inter-monsoonal Transition"
        else:
            monsoon_regime = f"Seasonal Meteorological Cycle (Quarter Q{(month - 1)//3 + 1})"

        return {
            "location": city_name,
            "region": region["name"],
            "climate_signals": {
                "enso": {
                    "phase": phase,
                    "intensity": enso.get("intensity", "Neutral"),
                    "anomaly_c": anomaly,
                    "confidence": enso.get("confidence", 0.82),
                    "source": enso.get("source", "NOAA CPC")
                },
                "indian_ocean_dipole": {
                    "state": iod_status,
                    "coupling": "Secondary modulator of regional rainfall"
                },
                "seasonal_monsoon": {
                    "regime": monsoon_regime,
                    "active_month": datetime.date(2000, month, 1).strftime("%B")
                },
                "temperature_anomaly": f"{'+' if anomaly > 0 else ''}{anomaly * 0.4:.1f}°C regional teleconnection variance",
                "rainfall_anomaly": f"{'+' if risks['rainfall']['score'] > 50 else ''}{int((risks['rainfall']['score'] - 40) * 0.8)}% probability shift"
            },
            "attribution_note": (
                "ENSO is one environmental signal among several. Local rainfall, terrain elevation, and "
                "urban drainage determine actual on-the-ground outcomes."
            )
        }

    # -------------------------------------------------------------------------
    # Teleconnection Wave Vector Generator (Pacific to City)
    # -------------------------------------------------------------------------
    def _compute_teleconnection_link(
        self, lat: float, lng: float, region: Dict[str, Any], enso: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculates geographic coordinates and propagation lines from Pacific Nino 3.4 to City."""
        # Niño 3.4 centroid
        nino_lat = 0.0
        nino_lng = -145.0

        # Intermediate atmospheric wave train nodes
        mid_lat = (nino_lat + lat) / 2.0
        # If city is in Eastern Hemisphere (e.g. India, Asia, Australia), route westward through Indo-Pacific
        if lng > 0:
            mid_lng = -180.0 if lng > 100 else 100.0
        else:
            mid_lng = (nino_lng + lng) / 2.0

        return {
            "origin": {"name": "Niño-3.4 Equatorial Pacific Center", "lat": nino_lat, "lng": nino_lng},
            "target": {"name": region["name"], "lat": lat, "lng": lng},
            "wave_nodes": [
                {"lat": nino_lat, "lng": nino_lng, "label": "Pacific SST Anomaly Source"},
                {"lat": mid_lat, "lng": mid_lng, "label": "Atmospheric Walker / Rossby Wave Cell"},
                {"lat": lat, "lng": lng, "label": "Local Urban Reception Zone"}
            ],
            "atmospheric_influence": (
                "Displaced tropical convective heating alters upper-tropospheric velocity potential, "
                "modulating downstream regional jet stream and monsoon troughs."
            )
        }

    def _generate_probabilistic_summary(
        self, city: str, phase: str, intensity: str, region: Dict[str, Any], risks: Dict[str, Any]
    ) -> str:
        """Strictly probabilistic narrative summary."""
        rf_lvl = risks["rainfall"]["level"]
        fl_lvl = risks["flood"]["level"]
        dr_lvl = risks["drought"]["level"]

        if phase == "Neutral":
            return (
                f"Global climate conditions reflect an ENSO Neutral state. Historical climatology indicates "
                f"{city} will experience near-average seasonal variability, governed primarily by local synoptic "
                f"weather patterns and topographical factors."
            )

        if region.get("is_india"):
            if phase == "La Niña":
                return (
                    f"The current {intensity} La Niña signal indicates conditions historically associated with "
                    f"increased rainfall variability and elevated storm surge likelihood in this region. "
                    f"While ENSO does not deterministically control local weather, historical patterns suggest "
                    f"elevated flood watch readiness ({fl_lvl.upper()}) is advisable for low-lying municipal sectors."
                )
            else: # El Niño
                return (
                    f"The current {intensity} El Niño signal indicates conditions historically correlated with "
                    f"monsoon rainfall fluctuations and elevated thermal anomalies across peninsular India. "
                    f"Drought risk is evaluated at {dr_lvl.upper()}, with secondary modulation from the Indian Ocean Dipole."
                )

        return (
            f"The active {intensity} {phase} climate signal alters global atmospheric circulation patterns. "
            f"Statistical teleconnections suggest {city} faces {rf_lvl} rainfall risk and {dr_lvl} drought stress. "
            f"Local drainage topography and real-time precipitation determine operational municipal vulnerability."
        )


city_impact_engine = CityImpactEngine()
