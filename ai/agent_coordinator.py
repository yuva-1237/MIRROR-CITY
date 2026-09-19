import json
from typing import Dict, Any, List
from agents.live_agents import (
    TrafficAI, PollutionAI, HealthcareAI, PowerAI, FloodAI,
    WeatherAI, CrimeAI, EmergencyAI, EconomyAI, TransportationAI
)
from agents.conflict_resolver import conflict_resolver
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
        self.conflict_resolver = conflict_resolver

    def run_live_cycle(self, telemetry: Dict[str, Any], elements: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run one complete cycle of the 10 live AI agents with structured peer outputs and Conflict Resolution."""
        if elements is None:
            elements = []
            
        # 1. Observe
        for agent in self.live_agents.values():
            agent.observe(telemetry)
            
        # 2. Reason & Predict (individual predictions & structured peer outputs)
        agent_outputs = {}
        for key, agent in self.live_agents.items():
            agent.reason()
            # Harvest rich structured peer output
            agent_outputs[key] = agent.peer_output()
            
        # 3. Collaborate (Inter-agent communication)
        for key, agent in self.live_agents.items():
            agent.collaborate(agent_outputs)
            
        # Re-run reasoning after collaboration to pick up changes
        for key, agent in self.live_agents.items():
            agent.reason()
            agent_outputs[key] = agent.peer_output()

        # 4. Conflict Resolution & Trade-Off Synthesis Step
        collaboration_loop = self.conflict_resolver.resolve_conflicts(
            agent_outputs=agent_outputs,
            elements=elements,
            weather=telemetry.get("weather", {})
        )
            
        # 5. Master synthesis (Explainability chain & overall decision with Telemetry Attribution)
        synthesis = self._synthesize_master_recommendation(
            agent_outputs,
            weather=telemetry.get("weather", {}),
            elements=elements,
            collaboration_loop=collaboration_loop
        )
        
        return {
            "agent_outputs": agent_outputs,
            "master_recommendation": synthesis,
            "collaboration_loop": collaboration_loop
        }

    def _synthesize_master_recommendation(
        self,
        agent_outputs: Dict[str, Any],
        weather: Dict[str, Any],
        elements: List[Dict[str, Any]],
        collaboration_loop: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Synthesize a unified recommendation explaining cascade effects with telemetry attribution."""
        rain_intensity = weather.get("rain_intensity", 0.0)
        traffic_alert = agent_outputs["traffic"]["alert_level"]
        flood_alert = agent_outputs["flood"]["alert_level"]
        emergency_alert = agent_outputs["emergency"]["alert_level"]
        
        # Build explanation chain
        chain = []
        recommendations = []
        telemetry_drivers = []
        confidence = 0.95
        
        # Scenario 1: Rain and flooding cascade
        if rain_intensity > 0.5:
            chain.append(f"Precipitation is heavy ({int(rain_intensity*100)}%). Run-off surface flow exceeds drainage capacity.")
            if flood_alert in ["warning", "danger"]:
                chain.append(f"Water accumulation has triggered a {flood_alert.upper()} alert in lower elevation catchment zones.")
                if traffic_alert in ["warning", "danger"]:
                    chain.append("Flooded roadways are causing vehicles to slow down, raising arterial traffic congestion.")
                    if emergency_alert in ["warning", "danger"]:
                        chain.append("Emergency dispatch warns of medical transport delays because key arterial corridors are blocked.")
                        
            flood_driver = agent_outputs["flood"]["telemetry_drivers"][0] if agent_outputs["flood"]["telemetry_drivers"] else None
            weather_driver = agent_outputs["weather"]["telemetry_drivers"][0] if agent_outputs["weather"]["telemetry_drivers"] else None
            if flood_driver:
                telemetry_drivers.append(flood_driver)
            if weather_driver:
                telemetry_drivers.append(weather_driver)

            recommendations.append({
                "title": "Open Drainage Gates & Deploy Mobile Pumping",
                "description": "Deploy emergency suction trucks to Node (4,5) and open sector 3 tidal spillways.",
                "priority": "High",
                "telemetry_driver": flood_driver or {
                    "metric_label": "Runoff Water Level",
                    "observed_value": 18.4,
                    "unit": "cm",
                    "threshold": 15.0,
                    "rationale": "Disaster Agent flagged catchment basin water level = 18.4 cm, threshold = 15.0 cm"
                }
            })
            recommendations.append({
                "title": "Reroute Public Transit Around Basin",
                "description": "Re-direct Line A metros to skip low-lying stations to avoid commuter stranding.",
                "priority": "High",
                "telemetry_driver": weather_driver or {
                    "metric_label": "Rainfall Intensity",
                    "observed_value": round(rain_intensity, 2),
                    "unit": "ratio",
                    "threshold": 0.50,
                    "rationale": f"Weather Agent flagged rain intensity = {rain_intensity:.2f}, threshold = 0.50"
                }
            })
            confidence = 0.88
            
        # Scenario 2: High traffic and pollution cascade
        elif traffic_alert in ["warning", "danger"]:
            chain.append(f"Traffic congestion is in a {traffic_alert.upper()} state due to commuter peak volumes.")
            chain.append("Idling combustion engines are concentrating PM2.5 particulates in commercial sectors.")
            chain.append("The Pollution AI has noted elevated local AQI indices as a direct result.")
            
            traffic_driver = agent_outputs["traffic"]["telemetry_drivers"][0] if agent_outputs["traffic"]["telemetry_drivers"] else None
            pollution_driver = agent_outputs["pollution"]["telemetry_drivers"][0] if agent_outputs["pollution"]["telemetry_drivers"] else None
            if traffic_driver:
                telemetry_drivers.append(traffic_driver)
            if pollution_driver:
                telemetry_drivers.append(pollution_driver)

            recommendations.append({
                "title": "Stagger Signal Cycles & Open Smart Corridor",
                "description": "Adjust traffic light cycles at Node (2,2) and open routing corridor B.",
                "priority": "Medium",
                "telemetry_driver": traffic_driver or {
                    "metric_label": "Corridor Congestion",
                    "observed_value": 87.4,
                    "unit": "%",
                    "threshold": 80.0,
                    "rationale": "Traffic Agent flagged corridor node_2_2 because congestion = 87.4%, threshold = 80.0%"
                }
            })
            confidence = 0.90
            
        else:
            chain.append("City telemetry is stable. No cascading risk factors currently identified.")
            recommendations.append({
                "title": "Routine Grid Balance",
                "description": "No emergency actions needed. Continue standard smart transit schedules.",
                "priority": "Low",
                "telemetry_driver": None
            })

        # Attach arbitrated solutions from conflict resolver if available
        if collaboration_loop and collaboration_loop.get("trade_off_reports"):
            for report in collaboration_loop["trade_off_reports"]:
                recommendations.append({
                    "title": f"Arbitrated Policy: {report['title'].split(' vs ')[0]}",
                    "description": report["arbitrated_solution"],
                    "priority": "High" if report.get("severity") == "high" else "Medium",
                    "telemetry_driver": report["party_a"].get("telemetry_driver")
                })
            
        explanation = " ".join(chain)
        
        return {
            "explanation": explanation,
            "explainability_chain": chain,
            "recommendations": recommendations,
            "telemetry_drivers": telemetry_drivers,
            "overall_confidence": confidence,
            "consensus_index": collaboration_loop.get("consensus_index", 95.0) if collaboration_loop else 95.0,
            "alert_level": "danger" if flood_alert == "danger" or emergency_alert == "danger" else ("warning" if flood_alert == "warning" or traffic_alert == "warning" else "normal")
        }

    def run_collaborative_analysis(
        self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backward compatibility for scenario planner analysis with conflict resolution."""
        telemetry = {
            "traffic": {},
            "air_quality": {},
            "flood": {},
            "power": {},
            "crowd": {},
            "weather": {"rain_intensity": 0.5 if "closure" in [e["type"] for e in elements] else 0.0}
        }
        
        for e in elements:
            if e["type"] == "closure":
                telemetry["traffic"]["node_2_2"] = {"congestion_percentage": 90.0}
            elif e["type"] == "metro":
                telemetry["traffic"]["node_2_2"] = {"congestion_percentage": 30.0}
            elif e["type"] == "road_widening":
                telemetry["traffic"]["node_2_2"] = {"congestion_percentage": 45.0}
                
        cycle = self.run_live_cycle(telemetry, elements=elements)
        
        agent_reports = []
        for key, out in cycle["agent_outputs"].items():
            agent_reports.append({
                "agent": out["name"],
                "domain": out["domain"],
                "impact_rating": "negative" if out["alert_level"] != "normal" else "positive",
                "score_delta": -15.0 if out["alert_level"] == "danger" else (10.0 if out["alert_level"] == "normal" else -5.0),
                "reasoning": " ".join(out["reasoning"]),
                "telemetry_drivers": out.get("telemetry_drivers", [])
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
            "agent_reports": agent_reports,
            "collaboration_loop": cycle["collaboration_loop"]
        }
