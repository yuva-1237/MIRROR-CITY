import random
import time
import math
import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SensorSimulator:
    def __init__(self):
        self.baseline_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "configs", "city_graph_baseline.json")
        )
        self.nodes = []
        self.edges = []
        self.load_baseline()
        
        # Keep track of simulated public transit vehicle positions
        self.transit_vehicles = self.init_transit_vehicles()
        
    def load_baseline(self):
        if os.path.exists(self.baseline_path):
            try:
                with open(self.baseline_path, "r") as f:
                    data = json.load(f)
                    self.nodes = data.get("nodes", [])
                    self.edges = data.get("edges", [])
            except Exception as e:
                logger.error(f"Error loading baseline in simulator: {e}")

    def init_transit_vehicles(self) -> List[Dict[str, Any]]:
        # Initialize 6 buses and 4 metros moving along edges
        vehicles = []
        # Bus 101, 102, 103, Metro M1, M2
        for i in range(5):
            vehicles.append({
                "id": f"bus_{101 + i}",
                "type": "bus",
                "route": f"Route {10 + i}",
                "node_index": random.randint(0, len(self.nodes) - 1) if self.nodes else 0,
                "target_node_index": random.randint(0, len(self.nodes) - 1) if self.nodes else 0,
                "progress": 0.0, # 0.0 to 1.0 between nodes
                "speed_kph": 30.0,
                "lat": 37.7624,
                "lng": -122.4219
            })
        for i in range(3):
            vehicles.append({
                "id": f"metro_{i + 1}",
                "type": "metro",
                "route": f"Line {chr(65 + i)}",
                "node_index": random.randint(0, len(self.nodes) - 1) if self.nodes else 0,
                "target_node_index": random.randint(0, len(self.nodes) - 1) if self.nodes else 0,
                "progress": 0.0,
                "speed_kph": 60.0,
                "lat": 37.7624,
                "lng": -122.4219
            })
        return vehicles

    def update_transit_positions(self, dt: float = 3.0):
        """Move transit vehicles along the city nodes."""
        if not self.nodes:
            return
        
        for vehicle in self.transit_vehicles:
            vehicle["progress"] += (vehicle["speed_kph"] / 3600.0) * dt * 5.0 # Speed up for display
            if vehicle["progress"] >= 1.0:
                vehicle["progress"] = 0.0
                vehicle["node_index"] = vehicle["target_node_index"]
                vehicle["target_node_index"] = random.randint(0, len(self.nodes) - 1)
            
            # Interpolate lat/lng
            n1 = self.nodes[vehicle["node_index"]]
            n2 = self.nodes[vehicle["target_node_index"]]
            vehicle["lat"] = n1["lat"] + (n2["lat"] - n1["lat"]) * vehicle["progress"]
            vehicle["lng"] = n1["lng"] + (n2["lng"] - n1["lng"]) * vehicle["progress"]

    def generate_readings(self, weather_state: Dict[str, Any], elements: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate high-fidelity real-time telemetry sensor readings."""
        if elements is None:
            elements = []
            
        now = datetime.now()
        hour = now.hour + now.minute / 60.0
        
        # Diurnal curves (Traffic, Power, Crowd peaks)
        # Peak 1: 8:00 AM (commute), Peak 2: 5:30 PM (commute)
        commute_factor = 0.3 + 0.7 * (math.exp(-((hour - 8.0)/1.5)**2) + math.exp(-((hour - 17.5)/2.0)**2))
        # Power peaks in evening
        power_factor = 0.4 + 0.6 * (math.exp(-((hour - 19.0)/3.0)**2) + 0.3 * math.exp(-((hour - 12.0)/2.0)**2))
        
        # Weather influence
        rain_intensity = weather_state.get("rain_intensity", 0.0) # 0.0 to 1.0
        wind_speed = weather_state.get("wind_speed", 10.0)
        temp = weather_state.get("temp", 18.0)
        
        # Update transit vehicles
        self.update_transit_positions(3.0)
        
        # Traffic Sensor Readings
        traffic_sensors = {}
        for edge in self.edges:
            edge_id = f"{edge['from_node']}_{edge['to_node']}"
            base_congest = edge.get("base_congestion", 20.0)
            
            # Weather decreases speed and increases congestion
            weather_congestion_add = rain_intensity * 35.0
            noise = random.uniform(-5.0, 5.0)
            
            congestion = min(100.0, max(5.0, base_congest * commute_factor * (1.0 + rain_intensity * 0.5) + weather_congestion_add + noise))
            vehicle_count = int(congestion * edge.get("lanes", 2) * 0.6)
            
            # Check for closures in elements
            is_closed = any(e for e in elements if e.get("type") == "closure" and edge_id in e.get("location_geojson", ""))
            if is_closed:
                congestion = 100.0
                vehicle_count = 0
                avg_speed = 0.0
            else:
                avg_speed = max(5.0, edge.get("speed_limit_kph", 50.0) * (1.0 - (congestion / 120.0)) * (1.0 - rain_intensity * 0.2))

            traffic_sensors[edge_id] = {
                "congestion_percentage": round(congestion, 1),
                "vehicle_count": vehicle_count,
                "average_speed_kph": round(avg_speed, 1),
                "incident_reported": random.random() < 0.005 # 0.5% chance of live accident
            }

        # Air Quality Sensor Readings
        air_quality_sensors = {}
        for node in self.nodes:
            # Base pollution + commute factors + weather (rain washes pollution, wind scatters it)
            base_pollution = node.get("pollution_level", 50.0)
            rain_wash = -15.0 * rain_intensity
            wind_scatter = -0.5 * (wind_speed - 10.0)
            commute_pollution = 20.0 * commute_factor
            
            pm25 = max(5.0, base_pollution * 0.7 + commute_pollution + rain_wash + wind_scatter + random.uniform(-3, 3))
            pm10 = pm25 * 1.5 + random.uniform(-2, 2)
            co2 = 380 + pm25 * 1.8 + random.uniform(-10, 10)
            no2 = pm25 * 0.6 + random.uniform(-2, 2)
            
            # AQI formula approximation
            aqi = min(500.0, max(10.0, pm25 * 1.2 + random.uniform(-5, 5)))
            
            air_quality_sensors[node["id"]] = {
                "aqi": int(aqi),
                "pm2_5": round(pm25, 1),
                "pm10": round(pm10, 1),
                "co2": int(co2),
                "no2": round(no2, 1)
            }

        # Flood Sensors
        flood_sensors = {}
        # Place 4 specific flood sensors at low-lying residential/industrial nodes
        flood_susceptible_nodes = [n["id"] for n in self.nodes if n["type"] in ["industrial", "residential"]][:6]
        for i, node_id in enumerate(flood_susceptible_nodes):
            # Water level rises with rain
            base_level = 5.0 # cm
            rain_rise = rain_intensity * rain_intensity * 120.0 # up to 120cm rise
            noise = random.uniform(-0.5, 0.5)
            
            level = max(0.0, base_level + rain_rise + noise)
            flow_rate = rain_intensity * 15.0 + random.uniform(0.1, 0.5) if level > 5.0 else 0.1
            
            flood_sensors[f"flood_sensor_{i}"] = {
                "node_id": node_id,
                "water_level_cm": round(level, 1),
                "flow_rate_m3_s": round(flow_rate, 2),
                "alert_status": "danger" if level > 60.0 else ("warning" if level > 25.0 else "normal")
            }

        # Power Grid Telemetry
        power_grid = {}
        for i, node in enumerate(self.nodes[:10]):
            base_demand = node.get("energy_demand", 50.0)
            # Weather temperature correlation (ac/heating loads)
            temp_addition = max(0.0, (temp - 24.0) * 3.0) + max(0.0, (15.0 - temp) * 1.5)
            load = min(100.0, max(10.0, base_demand * power_factor + temp_addition + random.uniform(-4, 4)))
            voltage = 230.0 * (1.0 - (load / 1000.0)) + random.uniform(-1, 1)
            
            power_grid[f"power_node_{i}"] = {
                "node_id": node["id"],
                "load_percentage": round(load, 1),
                "voltage_v": round(voltage, 1),
                "grid_stability": "stable" if load < 85.0 else "critical"
            }

        # Crowd Density
        crowd_sensors = {}
        for node in self.nodes:
            base_density = 0.1 # people / m^2
            commute_crowd = commute_factor * 1.5 if node["type"] in ["commercial", "school"] else commute_factor * 0.5
            rain_impact = -0.5 * rain_intensity # people go indoors in rain
            density = max(0.02, base_density + commute_crowd + rain_impact + random.uniform(-0.05, 0.05))
            
            crowd_sensors[node["id"]] = {
                "density_people_m2": round(density, 2),
                "total_count": int(density * 1000), # simulated zone area 1000m^2
                "alert_level": "crowded" if density > 1.2 else "normal"
            }

        return {
            "timestamp": now.isoformat(),
            "traffic": traffic_sensors,
            "air_quality": air_quality_sensors,
            "flood": flood_sensors,
            "power": power_grid,
            "crowd": crowd_sensors,
            "transit": self.transit_vehicles
        }

    def set_active_nodes_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]], disable_transit: bool = False):
        self.nodes = nodes
        self.edges = edges
        if disable_transit:
            self.transit_vehicles = []
        else:
            self.transit_vehicles = self.init_transit_vehicles()

