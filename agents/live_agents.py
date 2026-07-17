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

    def log_thought(self, message: str, data: Dict[str, Any] = None):
        """Save reasoning to persistent City Memory."""
        city_memory.remember(self.domain, "observation", f"{self.name}: {message}", data)


class TrafficAI(LiveAgent):
    def __init__(self):
        super().__init__("Traffic AI", "traffic")
        
    def reason(self) -> List[str]:
        traffic_data = self.last_observation.get("traffic", {})
        if not traffic_data:
            return ["No active traffic feeds detected."]
            
        congestions = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congestion = sum(congestions) / len(congestions) if congestions else 0.0
        
        reasons = [
            f"Average city-wide traffic congestion is currently at {avg_congestion:.1f}%.",
            f"Active camera feeds count: {len(traffic_data)} segments."
        ]
        
        high_congestion_nodes = [k for k, v in traffic_data.items() if v["congestion_percentage"] > 75.0]
        if high_congestion_nodes:
            self.alert_level = "danger" if len(high_congestion_nodes) > 3 else "warning"
            reasons.append(f"Severe congestion bottlenecks detected at: {', '.join(high_congestion_nodes[:3])}.")
        else:
            self.alert_level = "normal"
            reasons.append("All primary road corridors are flowing within nominal tolerances.")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"avg_congestion": avg_congestion})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        traffic_data = self.last_observation.get("traffic", {})
        congestions = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congestion = sum(congestions) / len(congestions) if congestions else 0.0
        
        # Predict trend
        multiplier = 1.0
        if horizon_mins <= 15:
            multiplier = 1.05 # minor growth
        elif horizon_mins <= 60:
            multiplier = 1.15 # peak hour simulation
        else:
            multiplier = 0.9 # evening disperse
            
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
                "cost": 1500.0
            })
        return recs


class PollutionAI(LiveAgent):
    def __init__(self):
        super().__init__("Pollution AI", "pollution")
        
    def reason(self) -> List[str]:
        air_data = self.last_observation.get("air_quality", {})
        if not air_data:
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
        else:
            self.alert_level = "normal"
            reasons.append("Air quality levels are inside safe regulatory parameters.")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"avg_aqi": avg_aqi})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        # If TrafficAI predicts high congestion, PollutionAI boosts predicted AQI
        traffic_pred = peer_outputs.get("traffic", {}).get("predicted_congestion_percentage", 30)
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


class HealthcareAI(LiveAgent):
    def __init__(self):
        super().__init__("Healthcare AI", "healthcare")
        
    def reason(self) -> List[str]:
        # Hospital status / emergency response estimation
        traffic_data = self.last_observation.get("traffic", {})
        congests = [t["congestion_percentage"] for t in traffic_data.values()]
        avg_congest = sum(congests) / len(congests) if congests else 0.0
        
        # Estimate ambulance response times based on traffic
        response_time = 6.0 + (avg_congest / 15.0)
        
        reasons = [
            f"Mean emergency vehicle dispatch-to-arrival latency: {response_time:.1f} minutes.",
        ]
        
        if response_time > 12.0:
            self.alert_level = "danger"
            reasons.append("Critical ambulance delays warning. Core arterial congestion is blocking priority lanes.")
        elif response_time > 9.0:
            self.alert_level = "warning"
            reasons.append("Moderate medical transport delay due to peak traffic conditions.")
        else:
            self.alert_level = "normal"
            reasons.append("Emergency response response-times are within 8-minute target window.")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"estimated_response_time": response_time})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        # If PollutionAI reports AQI danger, HealthcareAI flags potential asthma alert
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
            return ["Energy grid monitors offline."]
            
        loads = [p["load_percentage"] for p in power_data.values()]
        avg_load = sum(loads) / len(loads) if loads else 0.0
        
        reasons = [
            f"Grid power load is averaging {avg_load:.1f}%.",
        ]
        
        critical_transformers = [k for k, v in power_data.items() if v["load_percentage"] > 90.0]
        if critical_transformers:
            self.alert_level = "danger" if len(critical_transformers) > 2 else "warning"
            reasons.append(f"Transformer overload detected at grid nodes: {', '.join(critical_transformers[:2])}.")
        else:
            self.alert_level = "normal"
            reasons.append("Grid operating margins are stable with 20%+ reserve capacity.")
            
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
                "cost": 500.0
            })
        return recs


class FloodAI(LiveAgent):
    def __init__(self):
        super().__init__("Flood AI", "flood")
        
    def reason(self) -> List[str]:
        flood_data = self.last_observation.get("flood", {})
        if not flood_data:
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
        elif warning_sensors:
            self.alert_level = "warning"
            reasons.append(f"Minor water accumulation reported at sensors: {', '.join(warning_sensors)}.")
        else:
            self.alert_level = "normal"
            reasons.append("Run-off levels are clear. Catchment basins have full drain capacities.")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"max_water_level": max_level})
        return reasons

    def collaborate(self, peer_outputs: Dict[str, Any]):
        weather_rain = peer_outputs.get("weather", {}).get("rain_intensity", 0.0)
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


class WeatherAI(LiveAgent):
    def __init__(self):
        super().__init__("Weather AI", "weather")
        
    def reason(self) -> List[str]:
        # Pull weather from sensors
        weather_data = self.last_observation.get("weather", {})
        temp = weather_data.get("temp", 18.0)
        cond = weather_data.get("condition", "Clear")
        rain = weather_data.get("rain_intensity", 0.0)
        
        reasons = [
            f"Active weather cell check: Temperature {temp}°C, condition: {cond}.",
            f"Rain intensity factor: {rain:.2f} (convective precipitation rate)."
        ]
        
        if cond in ["Heavy Rain", "Storm"]:
            self.alert_level = "danger"
            reasons.append("Severe rain cell warning in effect. High risk of local water logging.")
        elif cond in ["Light Rain", "Mist/Fog"]:
            self.alert_level = "warning"
            reasons.append("Slight visibility and slick road hazards. Rerouting advisories.")
        else:
            self.alert_level = "normal"
            reasons.append("Weather conditions are clear. High visibility.")
            
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
        # Crime logs or crowd safety indicators
        crowd_data = self.last_observation.get("crowd", {})
        congested_count = sum(1 for c in crowd_data.values() if c["density_people_m2"] > 1.2)
        
        reasons = [
            "Patrol grid activity: 100% police unit coverage.",
        ]
        
        if congested_count > 4:
            self.alert_level = "warning"
            reasons.append("Heightened alert in massive crowd gathering zones. Increased risk of public safety incidents.")
        else:
            self.alert_level = "normal"
            reasons.append("No unusual safety metrics or civil incidents reported.")
            
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
        # Monitors active emergency incidents
        reasons = [
            "Emergency dispatch channels monitoring 112/911 call logs.",
        ]
        
        # Check if we have active accidents in traffic simulator or flood alerts
        traffic = self.last_observation.get("traffic", {})
        accidents = [k for k, v in traffic.items() if v.get("incident_reported")]
        flood_data = self.last_observation.get("flood", {})
        critical_floods = [k for k, v in flood_data.items() if v["alert_status"] == "danger"]
        
        if accidents or critical_floods:
            self.alert_level = "danger"
            if accidents:
                reasons.append(f"ACTIVE TRAFFIC INCIDENT: Collision reported on corridor: {', '.join(accidents[:2])}. Dispatching responders.")
            if critical_floods:
                reasons.append(f"FLOOD EMERGENCY: Critical water levels at: {', '.join(critical_floods[:2])}. Initiating drainage pump systems.")
        else:
            self.alert_level = "normal"
            reasons.append("Zero active major dispatch emergencies reported.")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"active_emergencies": len(accidents) + len(critical_floods)})
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
        
        # High traffic reduces economic throughput (lost productivity)
        lost_productivity_millions = (avg_congest / 45.0) * 0.15
        
        reasons = [
            f"Estimated daily congestion productivity loss: ${lost_productivity_millions:.3f}M.",
        ]
        
        if avg_congest > 65.0:
            self.alert_level = "warning"
            reasons.append("Economic drag warning: gridlock in downtown retail zones limits shopping commute rates.")
        else:
            self.alert_level = "normal"
            reasons.append("Commercial nodes are trading at nominal efficiency levels.")
            
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
        # Track simulated transit vehicle ETA status
        transit_vehicles = self.last_observation.get("transit", [])
        
        reasons = [
            f"Public transit monitoring online: {len(transit_vehicles)} active vehicles.",
        ]
        
        late_vehicles = sum(1 for v in transit_vehicles if v.get("speed_kph", 40.0) < 20.0)
        if late_vehicles > 2:
            self.alert_level = "warning"
            reasons.append(f"Transit schedules running behind: {late_vehicles} vehicles reporting delays.")
        else:
            self.alert_level = "normal"
            reasons.append("All bus and metro routes running on schedule (98.2% on-time performance).")
            
        self.reasoning_chain = reasons
        self.log_thought(reasons[-1], {"transit_vehicles_count": len(transit_vehicles)})
        return reasons

    def predict(self, horizon_mins: int) -> Dict[str, Any]:
        return {
            "on_time_performance_percentage": 95.0,
            "confidence": 0.93,
            "description": "Transit reliability score projected above 94%."
        }
