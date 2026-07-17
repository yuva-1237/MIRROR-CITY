import json
from typing import Dict, Any, List

class CityAgent:
    def __init__(self, name: str, domain: str):
        self.name = name
        self.domain = domain

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Each agent must implement the analyze method.")

class TrafficAgent(CityAgent):
    def __init__(self):
        super().__init__("Traffic Agent", "Traffic Congestion & Travel Times")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        # Analyze elements
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        closure_count = sum(1 for e in elements if e["type"] == "closure")
        widening_count = sum(1 for e in elements if e["type"] == "road_widening")
        flyover_count = sum(1 for e in elements if e["type"] == "flyover")

        if metro_count > 0:
            score_delta += 15.0 * metro_count
            reasoning_bullets.append(f"Adding {metro_count} metro station(s) shifts commuters from roads to public transit, reducing general congestion.")
        if widening_count > 0:
            score_delta += 8.0 * widening_count
            reasoning_bullets.append(f"Widening lanes increases capacity for private vehicles, improving traffic throughput.")
        if flyover_count > 0:
            score_delta += 12.0 * flyover_count
            reasoning_bullets.append(f"Constructing flyovers bypasses congested intersections, easing flow at bottleneck points.")
        if closure_count > 0:
            score_delta -= 25.0 * closure_count
            reasoning_bullets.append(f"Closing roads forces traffic to detour onto adjacent lanes, causing localized bottlenecks.")
            
        if not elements:
            reasoning_bullets.append("No active traffic modifications proposed in this scenario.")

        impact = "positive" if score_delta > 0 else ("negative" if score_delta < 0 else "neutral")
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No traffic impacts identified."
        }

class HealthcareAgent(CityAgent):
    def __init__(self):
        super().__init__("Healthcare Agent", "Medical Coverage & Emergency Access")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        hospitals = sum(1 for e in elements if e["type"] == "hospital")
        metro_count = sum(1 for e in elements if e["type"] == "metro")

        if hospitals > 0:
            score_delta += 35.0 * hospitals
            reasoning_bullets.append(f"Building {hospitals} hospital(s) dramatically expands ICU bed capacity and medical coverage radius.")
        if metro_count > 0:
            score_delta += 5.0 * metro_count
            reasoning_bullets.append("New metro lines facilitate transit access for elderly and low-income patients.")
            
        if not elements:
            reasoning_bullets.append("No health facility updates provided.")

        impact = "positive" if score_delta > 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No healthcare impacts identified."
        }

class PollutionAgent(CityAgent):
    def __init__(self):
        super().__init__("Pollution Agent", "Air Quality & CO2 Output")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        green_spaces = sum(1 for e in elements if e["type"] == "green_space")
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        closures = sum(1 for e in elements if e["type"] == "closure")

        if green_spaces > 0:
            score_delta += 20.0 * green_spaces
            reasoning_bullets.append(f"Creating {green_spaces} green park(s) adds carbon sinks and helps filter PM2.5 particles from local air.")
        if metro_count > 0:
            score_delta += 10.0 * metro_count
            reasoning_bullets.append("Metro stations lower carbon emissions by reducing vehicle miles traveled.")
        if closures > 0:
            score_delta -= 8.0 * closures
            reasoning_bullets.append("Road closures create idling traffic, increasing emissions in bottleneck areas.")

        impact = "positive" if score_delta > 0 else ("negative" if score_delta < 0 else "neutral")
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No carbon/AQI impacts identified."
        }

class WeatherAgent(CityAgent):
    def __init__(self):
        super().__init__("Weather Agent", "Microclimate & Temperature Regulation")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        green_spaces = sum(1 for e in elements if e["type"] == "green_space")
        
        if green_spaces > 0:
            score_delta += 15.0 * green_spaces
            reasoning_bullets.append(f"Parks reduce the Urban Heat Island effect, lowering local temperatures by 1.5C.")
        else:
            reasoning_bullets.append("Lack of new canopy spaces leaves the neighborhood vulnerable to heat domes.")

        impact = "positive" if score_delta > 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets)
        }

class DisasterAgent(CityAgent):
    def __init__(self):
        super().__init__("Disaster Agent", "Flood Risk & Evacuation Capacity")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        green_spaces = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")
        hospitals = sum(1 for e in elements if e["type"] == "hospital")

        if green_spaces > 0:
            score_delta += 18.0 * green_spaces
            reasoning_bullets.append("Permeable green surfaces act as retention areas, absorbing storm runoff and preventing flash floods.")
        if hospitals > 0:
            score_delta += 10.0 * hospitals
            reasoning_bullets.append("New medical hubs enhance disaster casualty response readiness.")
        if closures > 0:
            score_delta -= 15.0 * closures
            reasoning_bullets.append("Closing crucial road segments impairs evacuation routes during severe emergencies.")

        impact = "positive" if score_delta > 0 else ("negative" if score_delta < 0 else "neutral")
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No resilience changes identified."
        }

class EconomyAgent(CityAgent):
    def __init__(self):
        super().__init__("Economy Agent", "Financial ROI & Commercial Value")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospitals = sum(1 for e in elements if e["type"] == "hospital")
        parks = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")

        if metro_count > 0:
            score_delta += 25.0 * metro_count
            reasoning_bullets.append("Subways drive retail foot traffic and commercial real estate valuation around station portals.")
        if hospitals > 0:
            score_delta += 15.0 * hospitals
            reasoning_bullets.append("Hospitals act as economic anchors, creating high-skill jobs and medical supplier networks.")
        if parks > 0:
            score_delta += 10.0 * parks
            reasoning_bullets.append("Parks improve surrounding residential property values (premium green pricing).")
        if closures > 0:
            score_delta -= 12.0 * closures
            reasoning_bullets.append("Closing roads blocks storefront access, leading to lower sales for adjacent local shops.")

        impact = "positive" if score_delta > 0 else ("negative" if score_delta < 0 else "neutral")
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No macroeconomic impact."
        }

class EnergyAgent(CityAgent):
    def __init__(self):
        super().__init__("Energy Agent", "Power Grid Capacity")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        hospitals = sum(1 for e in elements if e["type"] == "hospital")
        metro_count = sum(1 for e in elements if e["type"] == "metro")

        if hospitals > 0:
            score_delta -= 15.0 * hospitals
            reasoning_bullets.append("Hospitals are energy-intensive 24/7 facilities; building one increases local substation load.")
        if metro_count > 0:
            score_delta -= 10.0 * metro_count
            reasoning_bullets.append("Metro lines require substantial electricity, raising peak demands on the municipal grid.")

        if not elements:
            reasoning_bullets.append("Energy grid levels remain steady at baseline.")

        impact = "negative" if score_delta < 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No electrical grid adjustments."
        }

class TransportationAgent(CityAgent):
    def __init__(self):
        super().__init__("Transportation Agent", "Public Transit Networks")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        flyover_count = sum(1 for e in elements if e["type"] == "flyover")

        if metro_count > 0:
            score_delta += 30.0 * metro_count
            reasoning_bullets.append("Expanded transit network increases city connectivity and transit coverage indexes.")
        if flyover_count > 0:
            score_delta += 5.0 * flyover_count
            reasoning_bullets.append("Flyovers aid bus express routes in bypassing gridlocked arterial streets.")

        impact = "positive" if score_delta > 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No public transit updates."
        }

class UrbanGrowthAgent(CityAgent):
    def __init__(self):
        super().__init__("Urban Growth Agent", "Zoning & Population Density")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        hospitals = sum(1 for e in elements if e["type"] == "hospital")
        parks = sum(1 for e in elements if e["type"] == "green_space")
        metro_count = sum(1 for e in elements if e["type"] == "metro")

        if metro_count > 0:
            score_delta += 15.0 * metro_count
            reasoning_bullets.append("New transit infrastructure encourages Transit-Oriented Development (TOD) and higher residential density.")
        if parks > 0:
            score_delta += 12.0 * parks
            reasoning_bullets.append("Adding greenspaces keeps population centers livable and balances urban concrete footprint.")
        if hospitals > 0:
            score_delta += 5.0 * hospitals
            reasoning_bullets.append("Healthcare hubs attract residential growth and senior communities nearby.")

        impact = "positive" if score_delta > 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets) or "No urban density adjustments."
        }

class InfrastructureAgent(CityAgent):
    def __init__(self):
        super().__init__("Infrastructure Agent", "Structural Health & Utilities")

    def analyze(self, scenario_name: str, elements: List[Dict[str, Any]], baseline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        score_delta = 0.0
        reasoning_bullets = []
        
        flyover_count = sum(1 for e in elements if e["type"] == "flyover")
        widening_count = sum(1 for e in elements if e["type"] == "road_widening")
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospitals = sum(1 for e in elements if e["type"] == "hospital")

        if flyover_count > 0 or widening_count > 0 or metro_count > 0 or hospitals > 0:
            # Construction has a negative short-term utility disruption impact
            disruptions = flyover_count + widening_count + metro_count + hospitals
            score_delta -= 10.0 * disruptions
            reasoning_bullets.append(f"Heavy construction of {disruptions} asset(s) places temporary strain on structural utilities and local pipelines.")
        else:
            reasoning_bullets.append("Utility pipelines and structural elements remain in stable, non-disrupted status.")

        impact = "negative" if score_delta < 0 else "neutral"
        return {
            "agent": self.name,
            "domain": self.domain,
            "impact_rating": impact,
            "score_delta": score_delta,
            "reasoning": " ".join(reasoning_bullets)
        }
