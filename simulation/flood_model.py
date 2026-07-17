import random
import networkx as nx
from typing import Dict, Any, List

class FloodModel:
    def __init__(self):
        pass

    def simulate_flood_spread(self, graph: nx.Graph, rain_intensity: float) -> Dict[str, Any]:
        """
        Simulate water propagation across the grid graph.
        Water flows from higher or low-draining nodes to adjacent nodes, causing road closures.
        """
        flooded_roads = []
        affected_nodes = []
        node_water_levels = {}
        
        # 1. Calculate water level at nodes based on zoning and rain intensity
        for node_id in graph.nodes():
            node = graph.nodes[node_id]
            ntype = node.get("type", "residential")
            
            # Base accumulation factors: parks absorb water, industrial/concrete zone collects it
            absorb_rate = 0.8 if ntype == "park" else (0.2 if ntype in ["industrial", "commercial"] else 0.4)
            accumulation = max(0.0, (rain_intensity * 100.0) * (1.0 - absorb_rate) + random.uniform(-2, 2))
            
            node_water_levels[node_id] = round(accumulation, 1)
            if accumulation > 25.0: # 25cm is a warning
                affected_nodes.append({
                    "node_id": node_id,
                    "water_level_cm": round(accumulation, 1),
                    "status": "submerged" if accumulation > 60.0 else "waterlogged"
                })

        # 2. Spread water along edges (roads)
        for u, v in graph.edges():
            level_u = node_water_levels.get(u, 0.0)
            level_v = node_water_levels.get(v, 0.0)
            avg_road_water = (level_u + level_v) / 2.0
            
            if avg_road_water > 30.0: # roads close if water > 30cm
                flooded_roads.append({
                    "from_node": u,
                    "to_node": v,
                    "road_name": graph.edges[u, v].get("road_name", "Local Street"),
                    "water_level_cm": round(avg_road_water, 1),
                    "status": "closed" if avg_road_water > 50.0 else "impassable_for_cars"
                })
                
        return {
            "node_water_levels": node_water_levels,
            "flooded_roads": flooded_roads,
            "affected_nodes": affected_nodes,
            "max_water_level_cm": round(max(node_water_levels.values()) if node_water_levels else 0.0, 1)
        }
