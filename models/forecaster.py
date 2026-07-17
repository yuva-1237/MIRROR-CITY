import math
from typing import Dict, Any, List

class TemporalForecaster:
    def __init__(self):
        pass

    def generate_24h_forecast(self, elements: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """
        Generate hourly forecasts for the next 24 hours based on active infrastructure elements.
        Simulates the outputs of a trained Temporal Fusion Transformer/Prophet model.
        """
        hours = list(range(24))
        
        # Calculate modifiers based on elements
        metro_count = sum(1 for e in elements if e["type"] == "metro")
        hospital_count = sum(1 for e in elements if e["type"] == "hospital")
        park_count = sum(1 for e in elements if e["type"] == "green_space")
        closures = sum(1 for e in elements if e["type"] == "closure")
        widening = sum(1 for e in elements if e["type"] == "road_widening")
        flyovers = sum(1 for e in elements if e["type"] == "flyover")

        traffic_forecast = []
        pollution_forecast = []
        energy_forecast = []
        water_forecast = []

        for h in hours:
            # 1. Traffic Congestion Index (0-100)
            # Diurnal peaks at 8 AM (h=8) and 5 PM (h=17)
            base_traffic = 30.0 + 40.0 * (
                math.exp(-((h - 8) ** 2) / 3.0) + math.exp(-((h - 17) ** 2) / 4.0)
            )
            # Noise
            base_traffic += 3.0 * math.sin(h / 2.0)
            
            # Apply element modifiers
            traffic_modifier = 1.0 - (0.12 * metro_count) - (0.05 * widening) - (0.08 * flyovers) + (0.22 * closures)
            traffic_val = max(10.0, min(100.0, base_traffic * traffic_modifier))
            traffic_forecast.append(round(traffic_val, 2))

            # 2. Air Pollution Index (AQI, 0-300)
            # Cumulative traffic effects + daily temperature shifts peaking around 2 PM (h=14)
            base_pollution = 50.0 + 35.0 * (
                math.exp(-((h - 14) ** 2) / 8.0)
            ) + (0.4 * base_traffic)
            pollution_modifier = 1.0 - (0.15 * park_count) - (0.05 * metro_count) + (0.10 * closures)
            pollution_val = max(15.0, min(300.0, base_pollution * pollution_modifier))
            pollution_forecast.append(round(pollution_val, 2))

            # 3. Energy Demand (MW)
            # Higher during commercial hours (9 AM - 6 PM) and residential peak in evening (6 PM - 9 PM)
            base_energy = 80.0 + 50.0 * (
                math.exp(-((h - 14) ** 2) / 12.0) + math.exp(-((h - 20) ** 2) / 4.0)
            )
            energy_modifier = 1.0 + (0.08 * hospital_count) + (0.04 * metro_count) - (0.02 * park_count)
            energy_val = max(40.0, base_energy * energy_modifier)
            energy_forecast.append(round(energy_val, 2))

            # 4. Water Demand (Millions of Liters / Hour)
            # Peaks in morning (7 AM) and evening (7 PM)
            base_water = 12.0 + 8.0 * (
                math.exp(-((h - 7) ** 2) / 2.0) + math.exp(-((h - 19) ** 2) / 2.0)
            )
            water_modifier = 1.0 + (0.06 * hospital_count) + (0.01 * park_count)
            water_val = max(5.0, base_water * water_modifier)
            water_forecast.append(round(water_val, 2))

        return {
            "hours": hours,
            "traffic": traffic_forecast,
            "pollution": pollution_forecast,
            "energy": energy_forecast,
            "water": water_forecast
        }
