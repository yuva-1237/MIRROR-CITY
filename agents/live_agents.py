import json
import random
from typing import Dict, Any, List
from agents.city_memory import city_memory

class LiveAgent:
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain
        self.last_observation = {}
        self.reasoning_chain = []
        self.alert_level = "normal"  # normal, warning, danger
        self.confidence_score = 0.95
        self.telemetry_drivers: List[Dict[str, Any]] = []
        self.proposals: List[Dict[str, Any]] = []
        self.concerns: List[Dict[str, Any]] = []
        self.compromise_flexibility: float = 0.8
        self.stance: str = "neutral"  # advocate, oppose, neutral, mitigate
        
    def observe(self, telemetry: Dict[str, Any]):
        self.last_observation = telemetry

    def reason(self) -> List[str]:
        raise NotImplementedError()

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        raise NotImplementedError()

    def collaborate(self, peer_outputs: Dict[str, Any]):
        pass

    def recommend(self) -> List[Dict[str, Any]]:
        return []

    def peer_output(self) -> Dict[str, Any]:
        """Returns structured peer output schema for collaborative multi-agent arbitration."""
        return {
            "agent_id": self.domain,
            "name": self.name,
            "domain": self.domain,
            "alert_level": self.alert_level,
            "confidence_score": int(self.confidence_score * 100),
            "stance": self.stance,
            "compromise_flexibility": self.compromise_flexibility,
            "reasoning": self.reasoning_chain,
            "telemetry_drivers": self.telemetry_drivers,
            "proposals": self.proposals,
            "concerns": self.concerns,
            "predictions": {
                "5m": self.predict(5),
                "1h": self.predict(60)
            },
            "recommendations": self.recommend()
        }

    def log_thought(self, message: str, data: Dict[str, Any] = None):
        """Save reasoning to persistent City Memory."""
        city_memory.remember(self.domain, "observation", f"{self.name}: {message}", data)


class TrafficAI(LiveAgent):
    def __init__(self):
        super().__init__("Traffic AI", "traffic")
        
    def reason(self) -> List[str]:
        traffic_data = self.last_observation.get("traffic", {})
        if not traffic_data:
            self.telemetry_drivers = []
            return ["No active traffic feeds detected."]
            
        congestions = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congestion = sum(congestions) / len(congestions) if congestions else 0.0
        
        reasons = [
            f"Average city-wide traffic congestion is currently at {avg_congestion:.1f}%.",
            f"Active camera feeds count: {len(traffic_data)} segments."
        ]
        
        high_congestion_nodes = [k for k, v in traffic_data.items() if v["congestion_percentage"] > 75.0]
        critical_nodes = [k for k, v in traffic_data.items() if v["congestion_percentage"] > 80.0]
        
        if high_congestion_nodes:
            self.alert_level = "danger" if len(high_congestion_nodes) > 3 else "warning"
            reasons.append(f"Severe congestion bottlenecks detected at: {', '.join(high_congestion_nodes[:3])}.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("All primary road corridors are flowing within nominal tolerances.")
            self.stance = "neutral"

        # Structured Telemetry Driver for Explainability
        focus_node = critical_nodes[0] if critical_nodes else (high_congestion_nodes[0] if high_congestion_nodes else "Corridor Alpha (node_2_2)")
        focus_val = traffic_data.get(focus_node, {}).get("congestion_percentage", avg_congestion)
        
        self.telemetry_drivers = [
            {
                "metric_key": "congestion_percentage",
                "metric_label": "Corridor Congestion",
                "entity": focus_node,
                "observed_value": round(focus_val, 1),
                "unit": "%",
                "threshold": 80.0,
                "comparison": ">" if focus_val > 80.0 else "<=",
                "delta_from_threshold": f"{round(focus_val - 80.0, 1):+}%",
                "alert_severity": "critical" if focus_val > 80.0 else ("warning" if focus_val > 70.0 else "nominal"),
                "rationale": f"Traffic Agent flagged corridor {focus_node} because congestion = {focus_val:.1f}%, threshold = 80.0%",
                "sensor_source": f"CCTV/Inductive Sensor #{focus_node}",
                "confidence": 95
            }
        ]

        # Collaboration proposals and concerns
        if self.alert_level != "normal":
            self.proposals = [
                {
                    "id": "PROP-TRF-01",
                    "action": "Activate Emergency Transit Corridor B",
                    "target": focus_node,
                    "intent": "Divert light vehicle flow to reduce arterial congestion below 65%",
                    "cost": 1500.0,
                    "estimated_benefit": "Reduces bottleneck congestion by 22%"
                }
            ]
            self.concerns = [
                {
                    "target": focus_node,
                    "issue": "Gridlock cascade reaching adjacent residential connectors",
                    "severity": "high",
                    "conflicts_with_domain": "pollution"
                }
            ]
        else:
            self.proposals = []
            self.concerns = []
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"avg_congestion": avg_congestion})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        traffic_data = self.last_observation.get("traffic", {})
        congestions = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congestion = sum(congestions) / len(congestions) if congestions else 0.0
        
        multiplier = 1.0
        if horizon_mins <= 15:
            multiplier = 1.05
        elif horizon_mins <= 60:
            multiplier = 1.15
        else:
            multiplier = 0.9
            
        predicted_congestion = min(100.0, avg_congestion * multiplier)
        return {
            "predicted_congestion_percentage": round(predicted_congestion, 1),
            "confidence": round(self.confidence_score - (horizon_mins / 2000.0), 2),
            "description": f"Congestion is projected to reach {predicted_congestion:.1f}% in the next {horizon_mins} minutes."
        }

    def recommend(self) -> List[Dict[str, Any]]:
        traffic_data = self.last_observation.get("traffic", {})
        heavy = [k for k, v in traffic_data.items() if v["congestion_percentage"] > 80.0]
        
        recs = []
        if heavy:
            recs.append({
                "action": "Activate Emergency Corridor",
                "target": heavy[0],
                "description": f"Reroute non-essential traffic around {heavy[0]} by opening smart routing corridor B.",
                "estimated_benefit": "Reduces congestion by 22% in 10 minutes",
                "cost": 1500.0,
                "telemetry_driver": self.telemetry_drivers[0] if self.telemetry_drivers else None
            })
        return recs


class PollutionAI(LiveAgent):
    def __init__(self):
        super().__init__("Pollution AI", "pollution")
        
    def reason(self) -> List[str]:
        air_data = self.last_observation.get("air_quality", {})
        if not air_data:
            self.telemetry_drivers = []
            return ["No active air quality sensors online."]
            
        aqis = [n["aqi"] for n in air_data.values()]
        avg_aqi = sum(aqis) / len(aqis) if aqis else 0
        
        reasons = [
            f"Mean particulate matter telemetry yields average AQI of {avg_aqi}.",
        ]
        
        poor_air_zones = [k for k, v in air_data.items() if v["aqi"] > 150]
        if poor_air_zones:
            self.alert_level = "danger" if len(poor_air_zones) > 2 else "warning"
            reasons.append(f"Unhealthy air conditions verified in industrial/commercial nodes: {', '.join(poor_air_zones[:2])}.")
            self.stance = "oppose"
        else:
            self.alert_level = "normal"
            reasons.append("Air quality levels are inside safe regulatory parameters.")
            self.stance = "neutral"

        focus_zone = poor_air_zones[0] if poor_air_zones else list(air_data.keys())[0]
        focus_aqi = air_data.get(focus_zone, {}).get("aqi", avg_aqi)

        self.telemetry_drivers = [
            {
                "metric_key": "aqi",
                "metric_label": "Air Quality Index (PM2.5)",
                "entity": focus_zone,
                "observed_value": int(focus_aqi),
                "unit": "AQI",
                "threshold": 150,
                "comparison": ">" if focus_aqi > 150 else "<=",
                "delta_from_threshold": f"{int(focus_aqi - 150):+}",
                "alert_severity": "critical" if focus_aqi > 150 else "nominal",
                "rationale": f"Pollution Agent flagged {focus_zone} because AQI = {int(focus_aqi)}, safe threshold = 150",
                "sensor_source": f"OpenAQ Laser PM2.5 Sensor #{focus_zone}",
                "confidence": 94
            }
        ]

        if self.alert_level != "normal":
            self.proposals = [
                {
                    "id": "PROP-POL-01",
                    "action": "Deploy Low-Emission Zone & Street Mist Cannons",
                    "target": focus_zone,
                    "intent": "Scrub PM2.5 and restrict diesel idling in sensitive sectors",
                    "cost": 3200.0,
                    "estimated_benefit": "Lowers local AQI by 28 points in 30 minutes"
                }
            ]
            self.concerns = [
                {
                    "target": focus_zone,
                    "issue": "Diverting traffic through residential streets concentrates toxic diesel particulates",
                    "severity": "high",
                    "conflicts_with_domain": "traffic"
                }
            ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"avg_aqi": avg_aqi})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        traffic_pred = peer_outputs.get("traffic", {}).get("predictions", {}).get("5m", {}).get("predicted_congestion_percentage", 30)
        if traffic_pred > 70:
            self.confidence_score = 0.92
            self.log_thought("Correlating high traffic forecasts with increased PM2.5 deposition rates.")

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        air_data = self.last_observation.get("air_quality", {})
        aqis = [n["aqi"] for n in air_data.values()]
        avg_aqi = sum(aqis) / len(aqis) if aqis else 50
        
        predicted_aqi = avg_aqi * (1.0 + (horizon_mins / 500.0))
        return {
            "predicted_aqi": int(min(500, predicted_aqi)),
            "confidence": round(self.confidence_score - (horizon_mins / 1500.0), 2),
            "description": f"AQI will likely rise to {int(predicted_aqi)} in industrial centers due to stagnant winds."
        }

    def recommend(self) -> List[Dict[str, Any]]:
        if self.alert_level != "normal":
            return [{
                "action": "Trigger Clean Air Mist Dispersion",
                "target": "Industrial & Central Corridors",
                "description": "Deploy automated water mist atomizers to capture airborne PM2.5 particulates.",
                "estimated_benefit": "Reduces PM2.5 concentration by 18%",
                "cost": 2400.0,
                "telemetry_driver": self.telemetry_drivers[0] if self.telemetry_drivers else None
            }]
        return []


class HealthcareAI(LiveAgent):
    def __init__(self):
        super().__init__("Healthcare AI", "healthcare")
        
    def reason(self) -> List[str]:
        traffic_data = self.last_observation.get("traffic", {})
        congests = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congest = sum(congests) / len(congests) if congests else 0.0
        
        response_time = 6.0 + (avg_congest / 15.0)
        
        reasons = [
            f"Mean emergency vehicle dispatch-to-arrival latency: {response_time:.1f} minutes.",
        ]
        
        if response_time > 12.0:
            self.alert_level = "danger"
            reasons.append("Critical ambulance delays warning. Core arterial congestion is blocking priority lanes.")
            self.stance = "advocate"
        elif response_time > 9.0:
            self.alert_level = "warning"
            reasons.append("Moderate medical transport delay due to peak traffic conditions.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("Emergency response response-times are within 8-minute target window.")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "emergency_response_latency_mins",
                "metric_label": "Ambulance Response Time",
                "entity": "Metro Trauma Center Corridors",
                "observed_value": round(response_time, 1),
                "unit": "mins",
                "threshold": 8.0,
                "comparison": ">" if response_time > 8.0 else "<=",
                "delta_from_threshold": f"{round(response_time - 8.0, 1):+} mins",
                "alert_severity": "critical" if response_time > 10.0 else "nominal",
                "rationale": f"Healthcare Agent flagged ambulance dispatch delay = {response_time:.1f} mins, SLA threshold = 8.0 mins",
                "sensor_source": "CAD (Computer Aided Dispatch) Telematics",
                "confidence": 96
            }
        ]

        if self.alert_level != "normal":
            self.proposals = [
                {
                    "id": "PROP-HLT-01",
                    "action": "Pre-Empt Traffic Signals for Paramedic Transit",
                    "target": "Hospital Zone Arterials",
                    "intent": "Clear dedicated green waves to keep response times below 8 minutes",
                    "cost": 800.0,
                    "estimated_benefit": "Shaves 3.5 minutes off emergency arrivals"
                }
            ]
            self.concerns = [
                {
                    "target": "Hospital Access Roads",
                    "issue": "Road closures or diverted freight block critical ICU trauma arrivals",
                    "severity": "critical",
                    "conflicts_with_domain": "traffic"
                }
            ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"estimated_response_time": response_time})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        pollution_alert = peer_outputs.get("pollution", {}).get("alert_level", "normal")
        if pollution_alert == "danger":
            self.log_thought("Alerting local emergency rooms for spike in respiratory/asthma admissions.")

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "predicted_response_time_mins": round(8.0 + (horizon_mins / 100.0), 1),
            "confidence": 0.90,
            "description": f"Response times predicted to rise to {8.0 + (horizon_mins/100.0):.1f} mins during peak hour."
        }


class PowerAI(LiveAgent):
    def __init__(self):
        super().__init__("Power AI", "power")
        
    def reason(self) -> List[str]:
        power_data = self.last_observation.get("power", {})
        if not power_data:
            self.telemetry_drivers = []
            return ["Energy grid monitors offline."]
            
        loads = [p["load_percentage"] for p in power_data.values()]
        avg_load = sum(loads) / len(loads) if loads else 0.0
        
        reasons = [
            f"Grid power load is averaging {avg_load:.1f}%.",
        ]
        
        critical_transformers = [k for k, v in power_data.items() if v["load_percentage"] > 90.0]
        warning_transformers = [k for k, v in power_data.items() if v["load_percentage"] > 80.0]

        if critical_transformers:
            self.alert_level = "danger" if len(critical_transformers) > 2 else "warning"
            reasons.append(f"Transformer overload detected at grid nodes: {', '.join(critical_transformers[:2])}.")
            self.stance = "oppose"
        else:
            self.alert_level = "normal"
            reasons.append("Grid operating margins are stable with 20%+ reserve capacity.")
            self.stance = "neutral"

        focus_node = critical_transformers[0] if critical_transformers else (warning_transformers[0] if warning_transformers else list(power_data.keys())[0])
        focus_load = power_data.get(focus_node, {}).get("load_percentage", avg_load)

        self.telemetry_drivers = [
            {
                "metric_key": "substation_load_percentage",
                "metric_label": "Substation Load Factor",
                "entity": focus_node,
                "observed_value": round(focus_load, 1),
                "unit": "%",
                "threshold": 85.0,
                "comparison": ">" if focus_load > 85.0 else "<=",
                "delta_from_threshold": f"{round(focus_load - 85.0, 1):+}%",
                "alert_severity": "critical" if focus_load > 90.0 else ("warning" if focus_load > 80.0 else "nominal"),
                "rationale": f"Power Agent flagged substation {focus_node} load = {focus_load:.1f}%, safety threshold = 85.0%",
                "sensor_source": f"SCADA Substation Meter #{focus_node}",
                "confidence": 98
            }
        ]

        if self.alert_level != "normal":
            self.proposals = [
                {
                    "id": "PROP-PWR-01",
                    "action": "Divert Peak Load to Utility Batteries (BESS)",
                    "target": focus_node,
                    "intent": "Relieve transformer thermal stress and preserve 20% reserve margin",
                    "cost": 500.0,
                    "estimated_benefit": "Reduces peak substation load by 14%"
                }
            ]
            self.concerns = [
                {
                    "target": focus_node,
                    "issue": "Concurrent high-draw pumping and transit charging risks cascading blackout",
                    "severity": "critical",
                    "conflicts_with_domain": "healthcare"
                }
            ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"avg_load": avg_load})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "grid_risk": "low" if self.alert_level == "normal" else "moderate",
            "confidence": 0.94,
            "description": "Grid expected to handle power demand without load shedding."
        }

    def recommend(self) -> List[Dict[str, Any]]:
        power_data = self.last_observation.get("power", {})
        overloaded = [v["node_id"] for k, v in power_data.items() if v["load_percentage"] > 85.0]
        recs = []
        if overloaded:
            recs.append({
                "action": "Divert Load Grid Section C",
                "target": overloaded[0],
                "description": f"Divert 15MW load from overloaded substation {overloaded[0]} to reserve batteries.",
                "estimated_benefit": "Reduces peak load by 12%",
                "cost": 500.0,
                "telemetry_driver": self.telemetry_drivers[0] if self.telemetry_drivers else None
            })
        return recs


class FloodAI(LiveAgent):
    def __init__(self):
        super().__init__("Flood AI", "flood")
        
    def reason(self) -> List[str]:
        flood_data = self.last_observation.get("flood", {})
        if not flood_data:
            self.telemetry_drivers = []
            return ["No active water level telemetry detected."]
            
        levels = [f["water_level_cm"] for f in flood_data.values()]
        max_level = max(levels) if levels else 0.0
        
        reasons = [
            f"Maximum surface run-off water accumulation: {max_level:.1f} cm.",
        ]
        
        danger_sensors = [k for k, v in flood_data.items() if v["alert_status"] == "danger"]
        warning_sensors = [k for k, v in flood_data.items() if v["alert_status"] == "warning"]
        
        if danger_sensors:
            self.alert_level = "danger"
            reasons.append(f"CRITICAL FLOODING DETECTED! Sensors ({', '.join(danger_sensors)}) exceed safe thresholds.")
            self.stance = "oppose"
        elif warning_sensors:
            self.alert_level = "warning"
            reasons.append(f"Minor water accumulation reported at sensors: {', '.join(warning_sensors)}.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("Run-off levels are clear. Catchment basins have full drain capacities.")
            self.stance = "neutral"

        focus_sensor = danger_sensors[0] if danger_sensors else (warning_sensors[0] if warning_sensors else list(flood_data.keys())[0])
        focus_level = flood_data.get(focus_sensor, {}).get("water_level_cm", max_level)

        self.telemetry_drivers = [
            {
                "metric_key": "water_level_cm",
                "metric_label": "Runoff Surface Water Level",
                "entity": focus_sensor,
                "observed_value": round(focus_level, 1),
                "unit": "cm",
                "threshold": 15.0,
                "comparison": ">" if focus_level > 15.0 else "<=",
                "delta_from_threshold": f"{round(focus_level - 15.0, 1):+} cm",
                "alert_severity": "critical" if focus_level > 15.0 else ("warning" if focus_level > 8.0 else "nominal"),
                "rationale": f"Disaster & Flood Agent flagged catchment basin {focus_sensor} water level = {focus_level:.1f} cm, overflow threshold = 15.0 cm",
                "sensor_source": f"Ultrasonic Hydrostatic Water Gauge #{focus_sensor}",
                "confidence": 97
            }
        ]

        # Climate DNA (ENSO) Teleconnection Driver
        climate_dna = self.last_observation.get("climate_dna") or {}
        enso_info = climate_dna.get("enso", {})
        flood_impact = climate_dna.get("impacts", {}).get("flood", {})
        if flood_impact and flood_impact.get("level") in ["elevated", "high"]:
            reasons.append(
                f"Climate Intelligence Link: {enso_info.get('phase', 'ENSO')} teleconnection indicates "
                f"statistically elevated rainfall variability, increasing catchment vulnerability."
            )
            self.telemetry_drivers.append({
                "metric_key": "climate_flood_risk",
                "metric_label": "Regional ENSO Flood Vulnerability",
                "entity": "MIRROR CITY Climate Impact Engine",
                "observed_value": flood_impact.get("score", 60),
                "unit": "risk index",
                "threshold": 50.0,
                "comparison": ">",
                "delta_from_threshold": f"{flood_impact.get('score', 60) - 50:+}",
                "alert_severity": "warning",
                "rationale": f"Coupled {enso_info.get('phase')} signal combined with local basin topography yields elevated flood risk score = {flood_impact.get('score', 60)}",
                "sensor_source": "NOAA Climate Signal + Hydrostatic Catchment Model",
                "confidence": int(flood_impact.get("confidence", 0.75) * 100)
            })

        if self.alert_level != "normal":
            self.proposals = [
                {
                    "id": "PROP-FLD-01",
                    "action": "Open Sector 3 Drainage Spillways & Deploy Suction Pumps",
                    "target": focus_sensor,
                    "intent": "Divert stormwater into secondary underground retention cisterns",
                    "cost": 4200.0,
                    "estimated_benefit": "Drops basin water level by 8.5 cm within 20 minutes"
                }
            ]
            self.concerns = [
                {
                    "target": focus_sensor,
                    "issue": "Road widening and concrete paving reduces retention soil percolation by 35%",
                    "severity": "critical",
                    "conflicts_with_domain": "economy"
                }
            ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"max_water_level": max_level})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        weather_rain = peer_outputs.get("weather", {}).get("predictions", {}).get("5m", {}).get("rain_intensity", 0.0)
        if weather_rain > 0.6:
            self.confidence_score = 0.98
            self.log_thought("Increasing confidence in run-off models due to heavy convective rain conditions.")

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        flood_data = self.last_observation.get("flood", {})
        levels = [f["water_level_cm"] for f in flood_data.values()]
        max_level = max(levels) if levels else 5.0
        
        predicted_max = max_level + (horizon_mins * 0.4 if self.alert_level == "danger" else 0.05)
        return {
            "predicted_water_level_cm": round(predicted_max, 1),
            "confidence": 0.88,
            "description": f"Accumulation level will peak around {predicted_max:.1f} cm near drainage grids."
        }

    def recommend(self) -> List[Dict[str, Any]]:
        if self.alert_level != "normal":
            return [{
                "action": "Engage Auxiliary Basin Drainage Gates",
                "target": "Basin Catchment Sector 3",
                "description": "Open floodgates to allow gravity discharge into tidal retention canal.",
                "estimated_benefit": "Prevents overtopping of arterial roadway",
                "cost": 1800.0,
                "telemetry_driver": self.telemetry_drivers[0] if self.telemetry_drivers else None
            }]
        return []


class WeatherAI(LiveAgent):
    def __init__(self):
        super().__init__("Weather AI", "weather")
        
    def reason(self) -> List[str]:
        weather_data = self.last_observation.get("weather", {})
        temp = weather_data.get("temp", 18.0)
        cond = weather_data.get("condition", "Clear")
        rain = weather_data.get("rain_intensity", 0.0)
        
        reasons = [
            f"Active weather cell check: Temperature {temp}°C, condition: {cond}.",
            f"Rain intensity factor: {rain:.2f} (convective precipitation rate)."
        ]
        
        if cond in ["Heavy Rain", "Storm"] or rain > 0.6:
            self.alert_level = "danger"
            reasons.append("Severe rain cell warning in effect. High risk of local water logging.")
            self.stance = "mitigate"
        elif cond in ["Light Rain", "Mist/Fog"] or rain > 0.2:
            self.alert_level = "warning"
            reasons.append("Slight visibility and slick road hazards. Rerouting advisories.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("Weather conditions are clear. High visibility.")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "rain_intensity",
                "metric_label": "Precipitation Convective Intensity",
                "entity": "Atmospheric Doppler Radar Grid",
                "observed_value": round(rain, 2),
                "unit": "ratio (0-1)",
                "threshold": 0.50,
                "comparison": ">" if rain > 0.50 else "<=",
                "delta_from_threshold": f"{round(rain - 0.50, 2):+}",
                "alert_severity": "critical" if rain > 0.50 else "nominal",
                "rationale": f"Weather Agent flagged convective precipitation rate = {rain:.2f}, flash risk threshold = 0.50",
                "sensor_source": "Meteorological Doppler Radar & Rain Barometer",
                "confidence": 98
            }
        ]

        # Climate DNA (ENSO) Teleconnection Driver
        climate_dna = self.last_observation.get("climate_dna") or {}
        enso_info = climate_dna.get("enso", {})
        if enso_info and enso_info.get("phase") in ["El Niño", "La Niña"]:
            c_phase = enso_info["phase"]
            c_int = enso_info.get("intensity", "Moderate")
            c_anom = enso_info.get("anomaly_c", 0.0)
            reasons.append(
                f"Global Climate Signal: {c_int} {c_phase} active (NOAA CPC, {c_anom:+.1f}°C). "
                f"Atmospheric teleconnection shifts regional convective precipitation probabilities."
            )
            self.telemetry_drivers.append({
                "metric_key": "enso_climate_signal",
                "metric_label": f"Global ENSO Teleconnection ({c_phase})",
                "entity": "NOAA Climate Prediction Center",
                "observed_value": round(c_anom, 2),
                "unit": "°C anomaly",
                "threshold": 0.50 if c_phase == "El Niño" else -0.50,
                "comparison": ">=" if c_phase == "El Niño" else "<=",
                "delta_from_threshold": f"{c_anom:+0.2f}",
                "alert_severity": "warning" if c_int in ["Strong", "Very Strong"] else "nominal",
                "rationale": f"Coupled ocean-atmosphere signal indicates {c_int} {c_phase} conditions affecting seasonal precipitation.",
                "sensor_source": enso_info.get("source", "NOAA CPC"),
                "confidence": int(enso_info.get("confidence", 0.85) * 100)
            })
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"condition": cond, "rain_intensity": rain})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        weather_data = self.last_observation.get("weather", {})
        rain = weather_data.get("rain_intensity", 0.0)
        return {
            "rain_intensity": rain,
            "condition": weather_data.get("condition", "Clear"),
            "confidence": 0.96,
            "description": f"Weather cell expected to pass in approximately {horizon_mins + 30} minutes."
        }


class CrimeAI(LiveAgent):
    def __init__(self):
        super().__init__("Crime AI", "crime")
        
    def reason(self) -> List[str]:
        crowd_data = self.last_observation.get("crowd", {})
        congested_count = sum(1 for c in crowd_data.values() if c["density_people_m2"] > 1.2)
        densities = [c["density_people_m2"] for c in crowd_data.values()]
        max_density = max(densities) if densities else 0.4
        
        reasons = [
            "Patrol grid activity: 100% police unit coverage.",
        ]
        
        if congested_count > 4 or max_density > 1.8:
            self.alert_level = "warning"
            reasons.append("Heightened alert in massive crowd gathering zones. Increased risk of public safety incidents.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("No unusual safety metrics or civil incidents reported.")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "crowd_density_people_m2",
                "metric_label": "Pedestrian Density Factor",
                "entity": "Downtown Plaza & Transit Hub",
                "observed_value": round(max_density, 2),
                "unit": "people/m²",
                "threshold": 1.20,
                "comparison": ">" if max_density > 1.2 else "<=",
                "delta_from_threshold": f"{round(max_density - 1.20, 2):+}",
                "alert_severity": "warning" if max_density > 1.2 else "nominal",
                "rationale": f"Public Safety Agent flagged pedestrian density = {max_density:.2f} people/m², threshold = 1.20",
                "sensor_source": "Thermal Optical Footfall Sensor Grid",
                "confidence": 93
            }
        ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"heavy_crowds_count": congested_count})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "safety_index": "safe",
            "confidence": 0.97,
            "description": "Standard city safety metrics predicted to remain stable."
        }


class EmergencyAI(LiveAgent):
    def __init__(self):
        super().__init__("Emergency AI", "emergency")
        
    def reason(self) -> List[str]:
        reasons = [
            "Emergency dispatch channels monitoring 112/911 call logs.",
        ]
        
        traffic = self.last_observation.get("traffic", {})
        accidents = [k for k, v in traffic.items() if v.get("incident_reported")]
        flood_data = self.last_observation.get("flood", {})
        critical_floods = [k for k, v in flood_data.items() if v["alert_status"] == "danger"]
        total_incidents = len(accidents) + len(critical_floods)
        
        if accidents or critical_floods:
            self.alert_level = "danger"
            if accidents:
                reasons.append(f"ACTIVE TRAFFIC INCIDENT: Collision reported on corridor: {', '.join(accidents[:2])}. Dispatching responders.")
            if critical_floods:
                reasons.append(f"FLOOD EMERGENCY: Critical water levels at: {', '.join(critical_floods[:2])}. Initiating drainage pump systems.")
            self.stance = "advocate"
        else:
            self.alert_level = "normal"
            reasons.append("Zero active major dispatch emergencies reported.")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "active_emergencies",
                "metric_label": "Active Emergency Dispatches",
                "entity": "City-Wide Dispatch Grid",
                "observed_value": total_incidents,
                "unit": "events",
                "threshold": 1,
                "comparison": ">=" if total_incidents >= 1 else "<",
                "delta_from_threshold": f"{total_incidents - 1:+}",
                "alert_severity": "critical" if total_incidents > 0 else "nominal",
                "rationale": f"Emergency Dispatch flagged {total_incidents} active incident(s), target threshold = 0",
                "sensor_source": "CAD Integrated Dispatch Stream",
                "confidence": 99
            }
        ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"active_emergencies": total_incidents})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        flood_alert = peer_outputs.get("flood", {}).get("alert_level", "normal")
        if flood_alert == "danger":
            self.log_thought("Evacuation response plans prepared for lower basin residential nodes.")

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "estimated_incident_clearance_time_mins": 35,
            "confidence": 0.91,
            "description": "Average response and resolution times expected at 22 minutes city-wide."
        }


class EconomyAI(LiveAgent):
    def __init__(self):
        super().__init__("Economy AI", "economy")
        
    def reason(self) -> List[str]:
        traffic_data = self.last_observation.get("traffic", {})
        congests = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congest = sum(congests) / len(congests) if congests else 0.0
        
        lost_productivity_millions = (avg_congest / 45.0) * 0.15
        
        reasons = [
            f"Estimated daily congestion productivity loss: ${lost_productivity_millions:.3f}M.",
        ]
        
        if avg_congest > 65.0:
            self.alert_level = "warning"
            reasons.append("Economic drag warning: gridlock in downtown retail zones limits shopping commute rates.")
            self.stance = "advocate"
        else:
            self.alert_level = "normal"
            reasons.append("Commercial nodes are trading at nominal efficiency levels.")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "congestion_drag",
                "metric_label": "Congestion Productivity Drag",
                "entity": "Downtown Commercial District",
                "observed_value": round(lost_productivity_millions, 3),
                "unit": "$M/day",
                "threshold": 0.100,
                "comparison": ">" if lost_productivity_millions > 0.100 else "<=",
                "delta_from_threshold": f"{round(lost_productivity_millions - 0.100, 3):+} $M",
                "alert_severity": "warning" if lost_productivity_millions > 0.100 else "nominal",
                "rationale": f"Economy Agent flagged daily congestion economic drag = ${lost_productivity_millions:.3f}M, tolerance threshold = $0.100M",
                "sensor_source": "Chamber of Commerce Urban Economic Telemetry",
                "confidence": 91
            }
        ]

        if avg_congest > 65.0:
            self.proposals = [
                {
                    "id": "PROP-ECN-01",
                    "action": "Expand Arterial Capacity & Widen Commercial Corridors",
                    "target": "Downtown Corridor",
                    "intent": "Enhance vehicle throughput to stimulate retail footfall and business revenue",
                    "cost": 15000.0,
                    "estimated_benefit": "+$1.4M annual commercial trade velocity"
                }
            ]
            self.concerns = [
                {
                    "target": "Downtown Corridor",
                    "issue": "Prolonged road closures curtail storefront revenues for local small businesses",
                    "severity": "medium",
                    "conflicts_with_domain": "traffic"
                }
            ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"lost_productivity_millions": lost_productivity_millions})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "economic_activity_delta": -0.02 if self.alert_level == "warning" else 0.0,
            "confidence": 0.85,
            "description": "Retail and service industries forecast positive weekend output trends."
        }


class TransportationAI(LiveAgent):
    def __init__(self):
        super().__init__("Transportation AI", "transportation")
        
    def reason(self) -> List[str]:
        transit_vehicles = self.last_observation.get("transit", [])
        
        reasons = [
            f"Public transit monitoring online: {len(transit_vehicles)} active vehicles.",
        ]
        
        late_vehicles = sum(1 for v in transit_vehicles if v.get("speed_kph", 40.0) < 20.0)
        if late_vehicles > 2:
            self.alert_level = "warning"
            reasons.append(f"Transit schedules running behind: {late_vehicles} vehicles reporting delays.")
            self.stance = "mitigate"
        else:
            self.alert_level = "normal"
            reasons.append("All bus and metro routes running on schedule (98.2% on-time performance).")
            self.stance = "neutral"

        self.telemetry_drivers = [
            {
                "metric_key": "transit_delays",
                "metric_label": "Delayed Transit Units",
                "entity": "Municipal Metro & Bus Lines",
                "observed_value": late_vehicles,
                "unit": "vehicles",
                "threshold": 2,
                "comparison": ">" if late_vehicles > 2 else "<=",
                "delta_from_threshold": f"{late_vehicles - 2:+}",
                "alert_severity": "warning" if late_vehicles > 2 else "nominal",
                "rationale": f"Transportation Agent flagged {late_vehicles} transit delays, SLA threshold = 2",
                "sensor_source": "GTFS-RT Vehicle Automatic Location System",
                "confidence": 97
            }
        ]
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"transit_vehicles_count": len(transit_vehicles)})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "on_time_performance_percentage": 95.0,
            "confidence": 0.93,
            "description": "Transit reliability score projected above 94%."
        }
