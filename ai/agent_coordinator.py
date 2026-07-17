import json
from typing import Dict, Any, List
from agents.live_agents import (
    TrafficAI, PollutionAI, HealthcareAI, PowerAI, FloodAI,
    WeatherAI, CrimeAI, EmergencyAI, EconomyAI, TransportationAI
)
from configs.config import settings

class AgentCoordinator:
    def __init__(self):
        self.live_agents = {
            "traffic": TrafficAI(),
            "pollution": PollutionAI(),
            "healthcare": HealthcareAI(),
            "power": PowerAI(),
            "flood": FloodAI(),
            "weather": WeatherAI(),
            "crime": CrimeAI(),
            "emergency": EmergencyAI(),
            "economy": EconomyAI(),
            "transportation": TransportationAI()
        }

    def run_live_cycle(self, telemetry: Dict[str, Any], elements: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one complete cycle of the 10 live AI agents (Observe -> Reason -> Collaborate -> Recommend)."""
        if elements is None:
            elements = []
            
        # 1. Observe
        for agent in self.live_agents.values():
            agent.observe(telemetry)
            
        # 2. Reason & Predict (individual predictions)
        agent_outputs = {}
        for key, agent in self.live_agents.items():
            reasons = agent.reason()
            pred_5m = agent.predict(5)
            pred_1h = agent.predict(60)
            
            agent_outputs[key] = {
                "name": agent.name,
                "domain": agent.domain,
                "alert_level": agent.alert_level,
                "reasoning": reasons,
                "predictions": {
                    "5m": pred_5m,
                    "1h": pred_1h
                },
                "recommendations": agent.recommend()
            }
            
        # 3. Collaborate (Inter-agent communication)
        # Agents adapt their states based on peer outputs
        for key, agent in self.live_agents.items():
            agent.collaborate(agent_outputs)
            
        # Re-run reasoning after collaboration to pick up changes
        for key, agent in self.live_agents.items():
            agent_outputs[key]["reasoning"] = agent.reason()
            
        # 4. Master synthesis (Explainability chain & overall decision)
        synthesis = self._synthesize_master_recommendation(agent_outputs, weather=telemetry.get("weather", {}), elements=elements)
        
        return {
            "agent_outputs": agent_outputs,
            "master_recommendation": synthesis
        }

    def _synthesize_master_recommendation(self, agent_outputs: Dict[str, Any], weather: Dict[str, Any], elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize a unified recommendation explaining the cascade effects of city variables."""
        rain_intensity = weather.get("rain_intensity", 0.0)
        traffic_alert = agent_outputs["traffic"]["alert_level"]
        flood_alert = agent_outputs["flood"]["alert_level"]
        emergency_alert = agent_outputs["emergency"]["alert_level"]
        
        # Build explanation chain
        chain = []
        recommendations = []
        confidence = 0.95
        
        # Scenario 1: Rain and flooding cascade
        if rain_intensity > 0.5:
            chain.append(f"Precipitation is heavy ({int(rain_intensity*100)}%). This increases rain run-off flow rates.")
            if flood_alert in ["warning", "danger"]:
                chain.append(f"Water accumulation has triggered a {flood_alert.upper()} alert in lower elevation zones.")
                if traffic_alert in ["warning", "danger"]:
                    chain.append(f"Flooded roadways are causing vehicles to slow down, raising traffic congestion.")
                    if emergency_alert in ["warning", "danger"]:
                        chain.append("Emergency services warn of medical dispatch delays because key road corridors are blocked.")
                        
            # Recommendations
            recommendations.append({
                "title": "Open Drainage Gates",
                "description": "Deploy emergency drainage pump trucks to Node (4,5) and open sector 3 spillways.",
                "priority": "High"
            })
            recommendations.append({
                "title": "Reroute Public Transit",
                "description": "Re-direct Line A metros to skip low-lying stations to avoid commuter stranding.",
                "priority": "High"
            })
            confidence = 0.88
            
        # Scenario 2: High traffic and pollution cascade
        elif traffic_alert in ["warning", "danger"]:
            chain.append(f"Traffic congestion is in a {traffic_alert.upper()} state due to commuter peak curves.")
            chain.append("Idling combustion engines are concentrating PM2.5 particulates in commercial sectors.")
            chain.append("The Pollution AI has noted elevated local AQI indices as a direct result.")
            
            recommendations.append({
                "title": "Stagger Signal Cycles",
                "description": "Adjust traffic light cycles at Node (2,2) to clear northbound corridors.",
                "priority": "Medium"
            })
            confidence = 0.90
            
        else:
            chain.append("City telemetry is stable. No cascading risk factors currently identified.")
            recommendations.append({
                "title": "Routine Grid Balance",
                "description": "No emergency actions needed. Continue standard smart transit schedules.",
                "priority": "Low"
            })
            
        explanation = " ".join(chain)
        
        return {
            "explanation": explanation,
            "explainability_chain": chain,
            "recommendations": recommendations,
            "overall_confidence": confidence,
            "alert_level": "danger" if flood_alert == "danger" or emergency_alert == "danger" else ("warning" if flood_alert == "warning" or traffic_alert == "warning" else "normal")
        }

    def run_collaborative_analysis(
        self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backward compatibility for scenario planner analysis."""
        # Map element inputs into dummy telemetry to reuse live logic
        telemetry = {
            "traffic": {},
            "air_quality": {},
            "flood": {},
            "power": {},
            "crowd": {},
            "weather": {"rain_intensity": 0.5 if "closure" in [e["type"] for e in elements] else 0.0}
        }
        
        # Populate dummy measurements
        for e in elements:
            if e["type"] == "closure":
                telemetry["traffic"]["node_2_2"] = {"congestion_percentage": 90.0}
            elif e["type"] == "metro":
                telemetry["traffic"]["node_2_2"] = {"congestion_percentage": 30.0}
                
        cycle = self.run_live_cycle(telemetry, elements=elements)
        
        # Formulate original schema
        agent_reports = []
        for key, out in cycle["agent_outputs"].items():
            agent_reports.append({
                "agent": out["name"],
                "domain": out["domain"],
                "impact_rating": "negative" if out["alert_level"] != "normal" else "positive",
                "score_delta": -15.0 if out["alert_level"] == "danger" else (10.0 if out["alert_level"] == "normal" else -5.0),
                "reasoning": " ".join(out["reasoning"])
            })
            
        total_delta = sum(r["score_delta"] for r in agent_reports)
        average_delta = total_delta / len(agent_reports)
        
        return {
            "scenario_name": scenario_name,
            "overall_impact": "positive" if average_delta > 0 else "negative",
            "average_delta": round(average_delta, 2),
            "confidence_score": int(cycle["master_recommendation"]["overall_confidence"] * 100),
            "explanation": cycle["master_recommendation"]["explanation"],
            "recommendations": cycle["master_recommendation"]["recommendations"],
            "agent_reports": agent_reports
        }
