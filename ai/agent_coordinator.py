import json
from typing import Dict, Any, List
from agents.specialized_agents import (
    TrafficAgent, HealthcareAgent, PollutionAgent, WeatherAgent,
    DisasterAgent, EconomyAgent, EnergyAgent, TransportationAgent,
    UrbanGrowthAgent, InfrastructureAgent
)
from configs.config import settings

class AgentCoordinator:
    def __init__(self):
        self.agents = [
            TrafficAgent(),
            HealthcareAgent(),
            PollutionAgent(),
            WeatherAgent(),
            DisasterAgent(),
            EconomyAgent(),
            EnergyAgent(),
            TransportationAgent(),
            UrbanGrowthAgent(),
            InfrastructureAgent()
        ]

    def run_collaborative_analysis(
        self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect feedback from all 10 agents and synthesize a unified analysis."""
        agent_reports = []
        total_delta = 0.0
        
        for agent in self.agents:
            report = agent.analyze(scenario_name, elements, baseline_metrics)
            agent_reports.append(report)
            total_delta += report["score_delta"]

        # Synthesize recommendation
        average_delta = total_delta / len(self.agents)
        overall_impact = "positive" if average_delta > 1.5 else ("negative" if average_delta < -1.5 else "neutral")
        confidence_score = 88.0 if len(elements) > 0 else 95.0 # baseline is highly certain

        # Generate a unified, plain-language explanation of why values changed
        explanation = self._synthesize_explanation(scenario_name, agent_reports, elements)

        recommendations = self._generate_recommendations(elements)

        return {
            "scenario_name": scenario_name,
            "overall_impact": overall_impact,
            "average_delta": round(average_delta, 2),
            "confidence_score": confidence_score,
            "explanation": explanation,
            "recommendations": recommendations,
            "agent_reports": agent_reports
        }

    def _synthesize_explanation(self, scenario_name: str, reports: List[Dict[str, Any]], elements: List[Dict[str, Any]]) -> str:
        """Create a logical summary explaining the physical relationships of the planning decisions."""
        if not elements:
            return "The city remains in its baseline state. Active systems indicate stable traffic flows, normal grid loads, and moderate carbon output. No critical actions are pending."

        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospital_count = sum(1 for e in elements if e["type"] == "hospital")
        park_count = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")

        explanation_parts = []
        explanation_parts.append(f"Analyzing proposed scenario '{scenario_name}':")

        if metro_count > 0:
            explanation_parts.append(
                f"The installation of {metro_count} metro hub(s) redirects transit patterns. "
                "By shifting commuters onto subways, traffic density drops on major roads, which in turn reduces carbon emissions and air pollution. "
                "However, this increases electrical load on the local energy substation grid."
            )
        if hospital_count > 0:
            explanation_parts.append(
                f"Building {hospital_count} new medical center(s) improves population health coverage and decreases emergency response times in nearby residential zones. "
                "This creates a localized micro-economy (attracting senior housing and pharmacies) but introduces utility strain during the construction phase."
            )
        if park_count > 0:
            explanation_parts.append(
                f"Adding {park_count} green space(s) acts as a cooling sink that mitigates urban heat islands and aids disaster prevention by absorbing water runoff. "
                "This also boosts surrounding residential land values."
            )
        if closures > 0:
            explanation_parts.append(
                f"Closing key road segments causes severe route redirections. Commute times spike as traffic bottlenecks on neighboring lanes, "
                "generating higher carbon emissions from idling engines and impacting retail foot traffic for local businesses."
            )

        return " ".join(explanation_parts)

    def _generate_recommendations(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Propose smart city optimizations based on the current scenario elements."""
        recommendations = []
        if not elements:
            recommendations.append({
                "title": "Initiate Planning Simulation",
                "description": "Place markers on the map (e.g. Metro Stations, Hospitals, Road Closures) to evaluate city-wide impacts.",
                "priority": "Medium"
            })
            return recommendations

        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospital_count = sum(1 for e in elements if e["type"] == "hospital")
        park_count = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")

        if closures > 0 and metro_count == 0:
            recommendations.append({
                "title": "Introduce Transit Alternatives",
                "description": "To mitigate traffic congestion from closed roads, implement a new metro station or bus lane nearby.",
                "priority": "High"
            })
        if hospital_count > 0:
            recommendations.append({
                "title": "Upgrade Grid Substation",
                "description": "The new hospital will increase power load. Proactively upgrade the energy grid distribution in that sector.",
                "priority": "Medium"
            })
        if park_count > 0:
            recommendations.append({
                "title": "Incorporate Permeable Drainage",
                "description": "Ensure the new green spaces use bioretention soils to maximize storm water absorption and flood mitigation.",
                "priority": "Low"
            })
        if not recommendations:
            recommendations.append({
                "title": "Baseline Verified",
                "description": "Proposed changes represent balanced development. Ready to submit for municipal approval.",
                "priority": "Low"
            })

        return recommendations
