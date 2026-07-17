import asyncio
import json
import datetime
from typing import Dict, Any, List
from database.connection import SessionLocal
from database.schema import LiveMetric, MapElement
from services.ws_manager import ws_manager
from services.sensor_simulator import SensorSimulator
from services.weather_service import weather_service
from services.data_validator import data_validator
from ai.agent_coordinator import AgentCoordinator
from simulation.continuous_engine import continuous_engine

class CityClock:
    def __init__(self):
        self.simulator = SensorSimulator()
        self.coordinator = AgentCoordinator()
        self.running = False
        self.task = None
        self.tick_count = 0
        
    def start(self):
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self.loop())
            print("Mirror City v2 Clock Started!")

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            
    async def loop(self):
        while self.running:
            try:
                self.tick_count += 1
                
                # 1. Fetch current weather
                current_weather = weather_service.get_weather()
                rain_val = current_weather.get("rain_intensity", 0.0)
                
                # 2. Fetch active scenario elements from DB
                db = SessionLocal()
                active_elements = []
                try:
                    elements = db.query(MapElement).all()
                    for elem in elements:
                        active_elements.append({
                            "type": elem.type,
                            "name": elem.name,
                            "location_geojson": elem.location_geojson,
                            "radius": elem.radius,
                            "capacity": elem.capacity,
                            "cost": elem.cost
                        })
                except Exception as db_err:
                    print(f"Database error in clock loop: {db_err}")
                finally:
                    db.close()
                
                # 3. Run continuous simulation models (GNN + Flood + Crowd + Disaster)
                sim_results = continuous_engine.run_tick(rain_val)
                
                # 4. Generate sensor telemetry
                telemetry = self.simulator.generate_readings(current_weather, active_elements)
                telemetry["weather"] = current_weather
                
                # Overlay simulation outputs on telemetry
                telemetry["flood_simulation"] = sim_results["flood"]
                telemetry["crowd_simulation"] = sim_results["crowd"]
                telemetry["disaster"] = sim_results["disaster"]

                # 4b. Validate telemetry & compute data quality summary
                data_quality = data_validator.validate_telemetry_batch(telemetry)
                data_quality["weather_source"]     = current_weather.get("source", "simulation")
                data_quality["weather_confidence"] = current_weather.get("confidence", 65)
                
                # 5. Run Multi-Agent collaborative reasoning loop
                agent_results = self.coordinator.run_live_cycle(telemetry, elements=active_elements)
                
                # 6. Calculate predictions
                predictions = self.calculate_predictions(telemetry, agent_results)
                
                # 7. Save snapshot metrics in database
                self.save_metric_snapshot(telemetry)
                
                # 8. Package complete city state
                payload = {
                    "tick": self.tick_count,
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "telemetry": telemetry,
                    "agent_outputs": agent_results["agent_outputs"],
                    "master_recommendation": agent_results["master_recommendation"],
                    "predictions": predictions,
                    "active_elements": active_elements,
                    "active_city": continuous_engine.active_city_metadata,
                    "buildings": continuous_engine.buildings_layer,
                    "city_graph": self._get_serialized_graph(),
                    "data_quality": data_quality,
                }
                
                # 9. Broadcast to WebSocket clients
                await ws_manager.broadcast(payload)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in CityClock loop tick {self.tick_count}: {e}")
                
            await asyncio.sleep(3.0) # Tick every 3 seconds

    def _get_serialized_graph(self) -> Dict[str, Any]:
        graph = continuous_engine.load_graph()
        nodes = []
        for n, attrs in graph.nodes(data=True):
            nodes.append({
                "id": n,
                "lat": attrs.get("lat"),
                "lng": attrs.get("lng"),
                "type": attrs.get("type", "residential"),
                "population_density": attrs.get("population_density", 50.0),
                "energy_demand": attrs.get("energy_demand", 50.0),
                "pollution_level": attrs.get("pollution_level", 50.0)
            })
        edges = []
        for u, v, attrs in graph.edges(data=True):
            edges.append({
                "from_node": u,
                "to_node": v,
                "name": attrs.get("road_name", "Local Street"),
                "length_m": attrs.get("length_m", 400.0),
                "speed_limit_kph": attrs.get("speed_limit_kph", 50.0),
                "lanes": attrs.get("lanes", 2),
                "base_congestion": attrs.get("base_congestion", 0.1)
            })
        return {"nodes": nodes, "edges": edges}

    def calculate_predictions(self, telemetry: Dict[str, Any], agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Formulate predictions across multiple time horizons."""
        congest = agent_results["agent_outputs"]["traffic"]["predictions"]
        aqi = agent_results["agent_outputs"]["pollution"]["predictions"]
        flood = agent_results["agent_outputs"]["flood"]["predictions"]
        
        return {
            "5m": {
                "traffic_congestion": congest["5m"]["predicted_congestion_percentage"],
                "aqi": aqi["5m"]["predicted_aqi"],
                "water_level": flood["5m"]["predicted_water_level_cm"],
                "alert": agent_results["master_recommendation"]["alert_level"]
            },
            "15m": {
                "traffic_congestion": round(congest["5m"]["predicted_congestion_percentage"] * 1.02, 1),
                "aqi": int(aqi["5m"]["predicted_aqi"] * 1.03),
                "water_level": round(flood["5m"]["predicted_water_level_cm"] * 1.05, 1),
                "alert": agent_results["master_recommendation"]["alert_level"]
            },
            "1h": {
                "traffic_congestion": congest["1h"]["predicted_congestion_percentage"],
                "aqi": aqi["1h"]["predicted_aqi"],
                "water_level": flood["1h"]["predicted_water_level_cm"],
                "alert": agent_results["master_recommendation"]["alert_level"]
            },
            "24h": {
                "traffic_congestion": round(congest["1h"]["predicted_congestion_percentage"] * 0.95, 1),
                "aqi": int(aqi["1h"]["predicted_aqi"] * 0.96),
                "water_level": round(flood["1h"]["predicted_water_level_cm"] * 0.9, 1),
                "alert": "normal"
            },
            "7d": {
                "traffic_congestion": round(congest["1h"]["predicted_congestion_percentage"] * 0.9, 1),
                "aqi": int(aqi["1h"]["predicted_aqi"] * 0.92),
                "water_level": round(flood["1h"]["predicted_water_level_cm"] * 0.8, 1),
                "alert": "normal"
            }
        }

    def save_metric_snapshot(self, telemetry: Dict[str, Any]):
        """Save snapshot of average metrics to database."""
        db = SessionLocal()
        try:
            congestions = [t["congestion_percentage"] for t in telemetry["traffic"].values()]
            avg_congestion = sum(congestions) / len(congestions) if congestions else 0.0
            
            aqis = [n["aqi"] for n in telemetry["air_quality"].values()]
            avg_aqi = sum(aqis) / len(aqis) if aqis else 0.0
            
            loads = [p["load_percentage"] for p in telemetry["power"].values()]
            avg_load = sum(loads) / len(loads) if loads else 0.0
            
            levels = [f["water_level_cm"] for f in telemetry["flood"].values()]
            max_flood = max(levels) if levels else 0.0
            
            densities = [c["density_people_m2"] for c in telemetry["crowd"].values()]
            avg_crowd = sum(densities) / len(densities) if densities else 0.0
            
            snapshot = {
                "avg_congestion": round(avg_congestion, 1),
                "avg_aqi": int(avg_aqi),
                "avg_power_load": round(avg_load, 1),
                "max_flood_level": round(max_flood, 1),
                "avg_crowd_density": round(avg_crowd, 2)
            }
            
            metric = LiveMetric(
                timestamp=datetime.datetime.utcnow(),
                metrics_json=json.dumps(snapshot)
            )
            db.add(metric)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Error saving metric snapshot: {e}")
        finally:
            db.close()

# Singleton clock instance
city_clock = CityClock()
