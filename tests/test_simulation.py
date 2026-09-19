import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import networkx as nx
from simulation.engine import SimulationEngine
from simulation.spectral_propagator import SpectralTrafficPropagator, TrafficGNN
from gis.spatial import haversine_distance

def test_haversine():
    # Distance between SF center and a point spaced by COORD_SPACING (0.005 deg)
    # Roughly 500-600 meters depending on exact latitude
    dist = haversine_distance(37.7749, -122.4194, 37.7799, -122.4194)
    assert 500.0 < dist < 600.0

def test_spectral_graph_propagation():
    # Construct a simple test graph
    graph = nx.Graph()
    graph.add_node("node_A", population_density=80, type="residential")
    graph.add_node("node_B", population_density=40, type="commercial")
    graph.add_edge("node_A", "node_B", length_m=500, speed_limit_kph=50, base_congestion=0.2, lanes=2)
    
    propagator = SpectralTrafficPropagator()
    updated_graph = propagator.propagate_traffic(graph)
    
    assert "congestion_index" in updated_graph.nodes["node_A"]
    assert "congestion_index" in updated_graph.nodes["node_B"]
    assert "current_congestion" in updated_graph.edges["node_A", "node_B"]
    assert "travel_time_mins" in updated_graph.edges["node_A", "node_B"]
    
    # Congestion should be bound between 0 and 1
    assert 0.0 <= updated_graph.edges["node_A", "node_B"]["current_congestion"] <= 1.0

def test_gnn_compatibility_alias():
    # Verify backward-compatibility alias TrafficGNN works identically
    graph = nx.Graph()
    graph.add_node("node_A", population_density=80, type="residential")
    graph.add_node("node_B", population_density=40, type="commercial")
    graph.add_edge("node_A", "node_B", length_m=500, speed_limit_kph=50, base_congestion=0.2, lanes=2)
    
    gnn = TrafficGNN()
    updated = gnn.propagate_traffic(graph)
    assert "congestion_index" in updated.nodes["node_A"]
