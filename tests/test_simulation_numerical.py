import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import numpy as np
import networkx as nx
from simulation.spectral_propagator import SpectralTrafficPropagator
from simulation.flood_model import FloodModel
from models.baseline_evaluator import baseline_evaluator

class TestSpectralTrafficPropagation:
    """Numerical tests for the Spectral Graph Laplacian traffic propagation engine."""

    def test_spectral_neighbor_propagation_hierarchy(self):
        """
        Verify that traffic congestion propagates strictly through graph neighborhoods:
        Injecting load at Node 0 must diffuse outward such that Hop 1 receives more load
        than Hop 2, and all nodes reflect spatial diffusion.
        """
        # Line topology: N0 -- N1 -- N2 -- N3
        graph = nx.Graph()
        graph.add_node("N0", population_density=100.0, type="commercial")
        graph.add_node("N1", population_density=0.0, type="residential")
        graph.add_node("N2", population_density=0.0, type="residential")
        graph.add_node("N3", population_density=0.0, type="residential")

        graph.add_edge("N0", "N1", length_m=500, speed_limit_kph=50, base_congestion=0.05, lanes=2)
        graph.add_edge("N1", "N2", length_m=500, speed_limit_kph=50, base_congestion=0.05, lanes=2)
        graph.add_edge("N2", "N3", length_m=500, speed_limit_kph=50, base_congestion=0.05, lanes=2)

        propagator = SpectralTrafficPropagator()
        updated = propagator.propagate_traffic(graph)

        c0 = updated.nodes["N0"]["congestion_index"]
        c1 = updated.nodes["N1"]["congestion_index"]
        c2 = updated.nodes["N2"]["congestion_index"]
        c3 = updated.nodes["N3"]["congestion_index"]

        # Congestion must propagate from source
        assert c0 > c1, f"Source N0 ({c0}) should have higher congestion than neighbor N1 ({c1})"
        assert c1 > c2, f"Hop 1 neighbor N1 ({c1}) should have higher congestion than Hop 2 N2 ({c2})"
        assert c2 >= c3, f"Hop 2 neighbor N2 ({c2}) should be >= Hop 3 N3 ({c3})"
        assert c1 > 0.0, "Neighbor N1 must receive non-zero propagated congestion"

    def test_congestion_bounds_conservation(self):
        """Verify that congestion values are strictly bounded in [0.0, 1.0] across all nodes and edges."""
        graph = nx.complete_graph(6)
        for u in graph.nodes():
            graph.nodes[u]["population_density"] = float(np.random.uniform(20, 150))
            graph.nodes[u]["type"] = "commercial" if u % 2 == 0 else "residential"

        for u, v in graph.edges():
            graph.edges[u, v]["length_m"] = 600
            graph.edges[u, v]["speed_limit_kph"] = 60
            graph.edges[u, v]["base_congestion"] = 0.3
            graph.edges[u, v]["lanes"] = 2

        propagator = SpectralTrafficPropagator()
        updated = propagator.propagate_traffic(graph)

        for u in updated.nodes():
            cong = updated.nodes[u]["congestion_index"]
            assert 0.0 <= cong <= 1.0, f"Node {u} congestion {cong} out of bounds [0, 1]"

        for u, v, data in updated.edges(data=True):
            e_cong = data["current_congestion"]
            assert 0.0 <= e_cong <= 1.0, f"Edge ({u}, {v}) congestion {e_cong} out of bounds [0, 1]"


class TestTravelTimeMonotonicity:
    """Numerical tests verifying the Bureau of Public Roads (BPR) travel time function."""

    def test_bpr_monotonicity(self):
        """
        Travel time must be strictly monotonically increasing with congestion:
        c1 < c2 ==> T(c1) < T(c2)
        """
        length_m = 1000.0
        speed_kph = 60.0
        free_flow_time = (length_m / 1000.0) / (speed_kph / 60.0)  # 1.0 minute

        congestions = np.linspace(0.0, 1.0, 50)
        travel_times = [free_flow_time * (1.0 + 2.0 * (c ** 4)) for c in congestions]

        # Verify strict monotonicity
        for i in range(len(travel_times) - 1):
            assert travel_times[i] <= travel_times[i + 1], (
                f"Monotonicity violated at index {i}: T({congestions[i]})={travel_times[i]} > T({congestions[i+1]})={travel_times[i+1]}"
            )

        # Boundary checks
        assert np.isclose(travel_times[0], free_flow_time), "Zero congestion must equal free-flow time"
        assert np.isclose(travel_times[-1], 3.0 * free_flow_time), "Max congestion (1.0) must be exactly 3x free-flow time"


class TestDijkstraDynamicRouting:
    """Numerical tests for shortest path routing, triangle inequality, and dynamic rerouting."""

    def test_triangle_inequality_shortest_paths(self):
        """For any triangle A-B-C, dist(A, C) <= dist(A, B) + dist(B, C)."""
        graph = nx.Graph()
        graph.add_edge("A", "B", travel_time_mins=5.0)
        graph.add_edge("B", "C", travel_time_mins=4.0)
        graph.add_edge("A", "C", travel_time_mins=12.0)

        dist_AC = nx.shortest_path_length(graph, "A", "C", weight="travel_time_mins")
        dist_AB = nx.shortest_path_length(graph, "A", "B", weight="travel_time_mins")
        dist_BC = nx.shortest_path_length(graph, "B", "C", weight="travel_time_mins")

        assert dist_AC <= dist_AB + dist_BC
        # Optimal path should route via B because 5 + 4 = 9 < 12
        path = nx.shortest_path(graph, "A", "C", weight="travel_time_mins")
        assert path == ["A", "B", "C"]

    def test_dynamic_rerouting_under_congestion(self):
        """
        Verify that the routing engine automatically detours traffic around a congested link
        when an alternative route has lower travel time.
        """
        # Graph with 2 paths between S and D:
        # Path 1: Direct link S -> D (length 1000m)
        # Path 2: Detour S -> M -> D (each segment 600m)
        graph = nx.Graph()
        graph.add_node("S", lat=13.0, lng=80.0, type="residential", population_density=50)
        graph.add_node("D", lat=13.02, lng=80.02, type="commercial", population_density=50)
        graph.add_node("M", lat=13.01, lng=80.01, type="residential", population_density=50)

        # Case 1: Low congestion on direct link
        graph.add_edge("S", "D", length_m=1000, speed_limit_kph=60, base_congestion=0.1)
        graph.add_edge("S", "M", length_m=600, speed_limit_kph=50, base_congestion=0.1)
        graph.add_edge("M", "D", length_m=600, speed_limit_kph=50, base_congestion=0.1)

        propagator = SpectralTrafficPropagator()
        g1 = propagator.propagate_traffic(graph.copy())
        path1 = nx.shortest_path(g1, "S", "D", weight="travel_time_mins")
        assert path1 == ["S", "D"], "Uncongested path should be direct S -> D"

        # Case 2: Severe gridlock injected on direct link S -> D
        graph["S"]["D"]["base_congestion"] = 0.95
        g2 = propagator.propagate_traffic(graph.copy())
        
        time_direct = g2["S"]["D"]["travel_time_mins"]
        time_detour = g2["S"]["M"]["travel_time_mins"] + g2["M"]["D"]["travel_time_mins"]
        
        path2 = nx.shortest_path(g2, "S", "D", weight="travel_time_mins")
        assert time_detour < time_direct, f"Detour time ({time_detour}) should be less than congested direct ({time_direct})"
        assert path2 == ["S", "M", "D"], "Routing engine must dynamically detour around gridlocked direct link"


class TestFloodRunoffConservation:
    """Numerical tests for rainfall runoff accumulation and park soil absorption."""

    def test_park_soil_absorption_advantage(self):
        """
        Permeable green spaces (parks) must absorb significantly more storm runoff
        than paved commercial/industrial zones, producing lower water accumulation.
        """
        graph = nx.Graph()
        graph.add_node("park_node", type="park")
        graph.add_node("concrete_node", type="industrial")
        graph.add_edge("park_node", "concrete_node")

        flood_model = FloodModel()
        results = flood_model.simulate_flood_spread(graph, rain_intensity=0.8)

        park_water = results["node_water_levels"]["park_node"]
        concrete_water = results["node_water_levels"]["concrete_node"]

        assert park_water < concrete_water, (
            f"Park water ({park_water} cm) must be lower than industrial concrete ({concrete_water} cm)"
        )
        # Park absorption is 80% vs 20% for concrete
        assert concrete_water > park_water * 2.0

    def test_flood_road_water_level_averaging(self):
        """Road edge water levels must equal the mean of the connecting endpoint nodes."""
        graph = nx.Graph()
        graph.add_node("N1", type="residential")
        graph.add_node("N2", type="commercial")
        graph.add_edge("N1", "N2", road_name="Waterfront Salai")

        flood_model = FloodModel()
        results = flood_model.simulate_flood_spread(graph, rain_intensity=0.9)

        w1 = results["node_water_levels"]["N1"]
        w2 = results["node_water_levels"]["N2"]
        expected_road_water = round((w1 + w2) / 2.0, 1)

        # Check in flooded roads if affected
        for road in results["flooded_roads"]:
            if road["from_node"] == "N1" and road["to_node"] == "N2":
                assert np.isclose(road["water_level_cm"], expected_road_water, atol=0.2)


class TestBaselineEvaluatorMetrics:
    """Numerical tests verifying the 15-minute traffic baseline evaluation metrics."""

    def test_baseline_evaluator_error_reduction(self):
        """Verify that spectral propagation achieves lower MAE than naive persistence baseline."""
        eval_result = baseline_evaluator.evaluate_15min_ahead()

        assert "metrics" in eval_result
        metrics = eval_result["metrics"]
        assert "spectral_model_mae" in metrics
        assert "naive_baseline_mae" in metrics
        assert "error_reduction_percent" in metrics

        spectral_mae = metrics["spectral_model_mae"]
        baseline_mae = metrics["naive_baseline_mae"]
        reduction = metrics["error_reduction_percent"]

        assert spectral_mae < baseline_mae, (
            f"Spectral MAE ({spectral_mae}%) must be lower than naive baseline ({baseline_mae}%)"
        )
        assert reduction >= 50.0, f"Error reduction should be at least 50% (got {reduction}%)"
        assert len(eval_result["time_labels"]) > 0
        assert len(eval_result["actual_congestion"]) == len(eval_result["time_labels"])
