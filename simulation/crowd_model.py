import random
import networkx as nx
from typing import Dict, Any, List

class CrowdModel:
    def __init__(self):
        pass

    def simulate_crowd_dynamics(self, graph: nx.Graph, rain_intensity: float) -> Dict[str, Any]:
        """
        Simulates crowd distributions, pedestrian counts, and evacuation density indexes.
        Crowd panic thresholds trigger under disaster conditions.
        """
        crowd_distribution = {}
        total_commuters = 0
        panic_index = 0.0 # 0.0 to 1.0 scale
        
        # High rain reduces outdoor pedestrians, shifts them to transit stations
        for node_id in graph.nodes():
            node = graph.nodes[node_id]
            ntype = node.get("type", "residential")
            pop = node.get("population_density", 50.0)
            
            # Base density factors
            base_count = int(pop * 15.0)
            if rain_intensity > 0.5:
                # Metros and indoor crossroads swell with shelter-seeking crowds
                pedestrians = base_count * (1.8 if ntype in ["station", "commercial"] else 0.4)
            else:
                pedestrians = base_count * (1.2 if ntype in ["park", "commercial"] else 0.8)
                
            pedestrians = int(max(10, pedestrians + random.uniform(-15, 15)))
            total_commuters += pedestrians
            
            # Calculate crowd safety density index (people per square meter)
            # Metros have smaller areas
            area = 500.0 if ntype == "station" else 2500.0
            density = pedestrians / area
            
            crowd_distribution[node_id] = {
                "pedestrian_count": pedestrians,
                "density_people_m2": round(density, 2),
                "status": "danger_stampede" if density > 1.5 else ("critical_crowd" if density > 0.8 else "normal")
            }
            
        # Overall panic index calculation
        critical_nodes = sum(1 for c in crowd_distribution.values() if c["status"] != "normal")
        if critical_nodes > 0:
            panic_index = min(1.0, (critical_nodes / len(graph.nodes())) + (rain_intensity * 0.2))

        return {
            "total_active_pedestrians": total_commuters,
            "crowd_distribution": crowd_distribution,
            "panic_index": round(panic_index, 2),
            "safety_status": "alert_evacuation" if panic_index > 0.4 else "safe"
        }
