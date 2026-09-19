import os
import json
import networkx as nx
from typing import Dict, Any, List
from simulation.spectral_propagator import SpectralTrafficPropagator
from simulation.flood_model import FloodModel
from simulation.crowd_model import CrowdModel
from simulation.disaster_model import disaster_model

class ContinuousEngine:
    def __init__(self):
        self.spectral_propagator = SpectralTrafficPropagator()
        self.gnn = self.spectral_propagator
        self.flood = FloodModel()
        self.crowd = CrowdModel()
        self.baseline_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "configs", "city_graph_baseline.json")
        )
        self.active_graph = None
        self.buildings_layer = []
        self.active_city_metadata = {
            "name": "San Francisco (Baseline)",
            "lat": 37.7749,
            "lng": -122.4194,
            "location_type": "city",
            "hierarchy": ["United States", "California", "San Francisco"],
            "area_sq_km": 121.4,
            "population": 873965,
            "population_source": "historical",
            "elevation": 16.0,
            "elevation_source": "historical",
            "timezone": "America/Los_Angeles",
            "datasets": {
                "road_network": {"status": "available", "source": "OpenStreetMap"},
                "buildings": {"status": "available", "source": "OpenStreetMap"},
                "weather": {"status": "available", "source": "OpenWeather Map"},
                "air_quality": {"status": "available", "source": "OpenAQ"},
                "traffic": {"status": "estimated", "source": "Spectral Graph Congestion Flow Model"},
                "flood": {"status": "estimated", "source": "Topographical Runoff Model"},
                "transit": {"status": "estimated", "source": "Estimated Transit Network"}
            }
        }
        
    def load_graph(self) -> nx.Graph:
        if self.active_graph is not None:
            return self.active_graph
            
        with open(self.baseline_path, "r") as f:
            data = json.load(f)
            
        graph = nx.Graph()
        for n in data["nodes"]:
            graph.add_node(
                n["id"],
                lat=n["lat"],
                lng=n["lng"],
                type=n["type"],
                population_density=n.get("population_density", 50.0),
                energy_demand=n.get("energy_demand", 50.0),
                pollution_level=n.get("pollution_level", 50.0)
            )
        for e in data["edges"]:
            graph.add_edge(
                e["from_node"],
                e["to_node"],
                road_name=e["name"],
                length_m=e["length_m"],
                speed_limit_kph=e["speed_limit_kph"],
                lanes=e["lanes"],
                base_congestion=e["base_congestion"]
            )
        self.active_graph = graph
        return graph

    def set_active_city(self, graph: nx.Graph, metadata: Dict[str, Any], buildings: List[Dict[str, Any]]):
        self.active_graph = graph
        self.active_city_metadata = metadata
        self.buildings_layer = buildings

    def run_tick(self, rain_intensity: float) -> Dict[str, Any]:
        """Perform one unified simulation pass of spectral graph traffic propagation, flood, crowd, and active disaster."""
        graph = self.load_graph()
        
        # 1. Update disaster state
        disaster_state = disaster_model.update_disaster()
        disaster_mods = disaster_model.get_impact_modifiers()
        
        # 2. Run spectral graph traffic propagation with disaster modifiers
        # Adjust edge weights by disaster congestion
        if disaster_mods:
            for u, v in graph.edges():
                base_congest = graph.edges[u, v].get("base_congestion", 0.1)
                graph.edges[u, v]["base_congestion"] = min(0.95, base_congest + disaster_mods.get("traffic_congestion_add", 0.0) / 100.0)
                
        graph = self.spectral_propagator.propagate_traffic(graph)
        
        # 3. Simulate flood spread
        flood_results = self.flood.simulate_flood_spread(graph, rain_intensity)
        
        # 4. Simulate crowd distribution
        crowd_results = self.crowd.simulate_crowd_dynamics(graph, rain_intensity)
        
        return {
            "disaster": disaster_state,
            "flood": flood_results,
            "crowd": crowd_results,
            "telemetry_modifications": disaster_mods
        }

# Singleton instance
continuous_engine = ContinuousEngine()
