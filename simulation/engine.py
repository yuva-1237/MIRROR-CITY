import os
import json
import numpy as np
import networkx as nx
from typing import Dict, Any, List
from configs.config import settings
from gis.spatial import find_nearest_node, find_nearest_edge, haversine_distance
from simulation.spectral_propagator import SpectralTrafficPropagator

class SimulationEngine:
    def __init__(self):
        self.spectral_propagator = SpectralTrafficPropagator()
        self.gnn = self.spectral_propagator  # backward-compat alias
        self.baseline_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "configs", "city_graph_baseline.json")
        )

    def load_baseline_graph(self) -> nx.Graph:
        """Load the baseline graph from the JSON file config."""
        if not os.path.exists(self.baseline_path):
            raise FileNotFoundError(f"Baseline city graph not found at {self.baseline_path}. Run seed script first.")
            
        with open(self.baseline_path, "r") as f:
            data = json.load(f)

        graph = nx.Graph()
        
        # Load nodes
        for node in data["nodes"]:
            graph.add_node(
                node["id"],
                name=node["name"],
                lat=node["lat"],
                lng=node["lng"],
                type=node["type"],
                population_density=node["population_density"],
                energy_demand=node.get("energy_demand", 50.0),
                pollution_level=node.get("pollution_level", 50.0)
            )
            
        # Load edges
        for edge in data["edges"]:
            graph.add_edge(
                edge["from_node"],
                edge["to_node"],
                road_name=edge["name"],
                length_m=edge["length_m"],
                speed_limit_kph=edge["speed_limit_kph"],
                lanes=edge["lanes"],
                base_congestion=edge["base_congestion"],
                current_congestion=edge["base_congestion"],
                travel_time_mins=(edge["length_m"] / 1000.0) / (edge["speed_limit_kph"] / 60.0)
            )
            
        return graph

    def run_simulation(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run the full simulation on the city graph with the proposed infrastructure modifications.
        """
        graph = self.load_baseline_graph()
        construction_cost = 0.0

        # Apply proposed changes
        for elem in elements:
            # Geocode the element coordinate
            loc = json.loads(elem["location_geojson"])
            lng, lat = loc["coordinates"]

            # Calculate cost by element type
            cost_map = {
                "hospital": 120000000.0,
                "metro": 75000000.0,
                "green_space": 8000000.0,
                "road_widening": 4000000.0,
                "flyover": 18000000.0,
                "closure": 50000.0
            }
            construction_cost += cost_map.get(elem["type"], 0.0)

            # Apply spatial effects to the graph
            if elem["type"] == "closure":
                # Find nearest road segment and disconnect it
                edge = find_nearest_edge(graph, lat, lng)
                if edge and graph.has_edge(*edge):
                    graph.remove_edge(*edge)
            elif elem["type"] == "road_widening":
                edge = find_nearest_edge(graph, lat, lng)
                if edge and graph.has_edge(*edge):
                    # Double capacity (halve congestion, increase lanes)
                    graph.edges[edge]["lanes"] += 1
                    graph.edges[edge]["base_congestion"] = max(0.05, graph.edges[edge]["base_congestion"] * 0.5)
                    graph.edges[edge]["speed_limit_kph"] += 10.0
            elif elem["type"] == "flyover":
                edge = find_nearest_edge(graph, lat, lng)
                if edge and graph.has_edge(*edge):
                    # Add grade separation: reduce congestion and increase speed limit
                    graph.edges[edge]["base_congestion"] = max(0.05, graph.edges[edge]["base_congestion"] * 0.4)
                    graph.edges[edge]["speed_limit_kph"] += 20.0
            elif elem["type"] == "hospital":
                node = find_nearest_node(graph, lat, lng)
                if node:
                    graph.nodes[node]["type"] = "hospital"
            elif elem["type"] == "metro":
                node = find_nearest_node(graph, lat, lng)
                if node:
                    graph.nodes[node]["type"] = "station"
                    # Metro stations reduce congestion on surrounding edges within 1.2km
                    for u, v, data in graph.edges(data=True):
                        u_lat, u_lng = graph.nodes[u]["lat"], graph.nodes[u]["lng"]
                        dist = haversine_distance(lat, lng, u_lat, u_lng)
                        if dist < 1200.0:
                            data["base_congestion"] = max(0.05, data["base_congestion"] * 0.7)
            elif elem["type"] == "green_space":
                node = find_nearest_node(graph, lat, lng)
                if node:
                    graph.nodes[node]["type"] = "park"
                    # Parks reduce pollution on adjacent nodes within 1km
                    for n in graph.nodes():
                        n_lat, n_lng = graph.nodes[n]["lat"], graph.nodes[n]["lng"]
                        dist = haversine_distance(lat, lng, n_lat, n_lng)
                        if dist < 1000.0:
                            graph.nodes[n]["pollution_level"] = max(10.0, graph.nodes[n].get("pollution_level", 50.0) - 20.0)

        # Run spectral graph propagation to compute final edge congestion & travel times
        graph = self.spectral_propagator.propagate_traffic(graph)

        # 1. Traffic Congestion & Average Travel Time Calculations (Dijkstra Commuting Paths)
        res_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "residential"]
        dest_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") in ["commercial", "industrial"]]
        
        travel_times = []
        for src in res_nodes:
            for dst in dest_nodes:
                try:
                    # Shortest path using dynamic travel time (incorporating congestion)
                    time_mins = nx.shortest_path_length(graph, src, dst, weight="travel_time_mins")
                    travel_times.append(time_mins)
                except nx.NetworkXNoPath:
                    # Assign heavy detour/gridlock penalty if road closure disconnected path
                    travel_times.append(90.0)

        avg_travel_time = np.mean(travel_times) if travel_times else 25.0

        # 2. Emergency Response Time Calculations
        hospital_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == "hospital"]
        emergency_times = []
        for src in hospital_nodes:
            for dst in res_nodes:
                try:
                    time_mins = nx.shortest_path_length(graph, src, dst, weight="travel_time_mins")
                    emergency_times.append(time_mins)
                except nx.NetworkXNoPath:
                    emergency_times.append(45.0)

        avg_emergency = np.mean(emergency_times) if emergency_times else 15.0

        # 3. Healthcare Coverage Index (percent of residential within 1.8km of hospital)
        covered_res = 0
        for res in res_nodes:
            res_lat, res_lng = graph.nodes[res]["lat"], graph.nodes[res]["lng"]
            covered = False
            for hosp in hospital_nodes:
                h_lat, h_lng = graph.nodes[hosp]["lat"], graph.nodes[hosp]["lng"]
                if haversine_distance(res_lat, res_lng, h_lat, h_lng) < 1800.0:
                    covered = True
                    break
            if covered:
                covered_res += 1
                
        healthcare_coverage = (covered_res / len(res_nodes) * 100.0) if res_nodes else 0.0

        # 4. Carbon Footprint (Daily metric tons CO2 estimated from congestion profile)
        total_co2 = 0.0
        total_congestion = 0.0
        edge_count = 0
        for u, v, data in graph.edges(data=True):
            cong = data.get("current_congestion", 0.1)
            length = data.get("length_m", 500)
            lanes = data.get("lanes", 2)
            # Emission estimate: CO2 proportional to congestion level, lanes, and length
            total_co2 += (cong * length * lanes * 0.25) / 1000.0 # scale to metric tons
            total_congestion += cong
            edge_count += 1

        avg_congestion = (total_congestion / edge_count) if edge_count > 0 else 0.2
        traffic_score = round(100.0 * (1.0 - avg_congestion), 1)

        # 5. Sustainability, Risk, and ROI scoring
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospital_count = sum(1 for e in elements if e["type"] == "hospital")
        park_count = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")

        sustainability = max(10.0, min(100.0, 60.0 - (total_co2 / 10.0) + (park_count * 12.0) + (metro_count * 8.0)))
        risk_level = max(5.0, min(100.0, 15.0 - (park_count * 4.0) + (closures * 15.0) - (hospital_count * 2.0)))

        # Economic delta calculation
        economic_growth_pct = (metro_count * 2.5) + (hospital_count * 1.5) + (park_count * 0.8) - (closures * 2.2)

        # ROI percentage (Benefits vs Cost)
        if construction_cost > 0:
            benefit_val = (metro_count * 15.0) + (hospital_count * 10.0) + (park_count * 4.0) - (closures * 8.0)
            roi = round((benefit_val * 10000000.0 / construction_cost) * 100.0, 1)
        else:
            roi = 0.0

        return {
            "traffic_score": round(traffic_score, 1),
            "cost": round(construction_cost, 2),
            "carbon_footprint": round(total_co2, 2),
            "travel_time": round(avg_travel_time, 1),
            "emergency_response": round(avg_emergency, 1),
            "economic_growth": round(economic_growth_pct, 2),
            "population_coverage": round(healthcare_coverage, 1),
            "construction_cost": round(construction_cost, 2),
            "risk_level": round(risk_level, 1),
            "sustainability_score": round(sustainability, 1),
            "roi": roi
        }
