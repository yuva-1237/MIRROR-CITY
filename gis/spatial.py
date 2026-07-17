import math
import networkx as nx
from typing import Tuple, Dict, Any

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface 
    using the Haversine formula. Returns distance in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

def find_nearest_node(graph: nx.Graph, lat: float, lng: float) -> str:
    """Find the nearest graph node ID for a given coordinate."""
    min_dist = float("inf")
    nearest_node_id = None
    
    for node_id, data in graph.nodes(data=True):
        n_lat = data.get("lat")
        n_lng = data.get("lng")
        if n_lat is not None and n_lng is not None:
            dist = haversine_distance(lat, lng, n_lat, n_lng)
            if dist < min_dist:
                min_dist = dist
                nearest_node_id = node_id
                
    return nearest_node_id

def find_nearest_edge(graph: nx.Graph, lat: float, lng: float) -> Tuple[str, str]:
    """Find the nearest graph edge for a given coordinate by checking edge midpoints."""
    min_dist = float("inf")
    nearest_edge = None
    
    for u, v, data in graph.edges(data=True):
        u_lat, u_lng = graph.nodes[u].get("lat"), graph.nodes[u].get("lng")
        v_lat, v_lng = graph.nodes[v].get("lat"), graph.nodes[v].get("lng")
        
        if None not in [u_lat, u_lng, v_lat, v_lng]:
            # Midpoint coordinates of the edge
            mid_lat = (u_lat + v_lat) / 2.0
            mid_lng = (u_lng + v_lng) / 2.0
            
            dist = haversine_distance(lat, lng, mid_lat, mid_lng)
            if dist < min_dist:
                min_dist = dist
                nearest_edge = (u, v)
                
    return nearest_edge
