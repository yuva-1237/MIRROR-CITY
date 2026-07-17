import random
import networkx as nx
from typing import Dict, Any, List

class DisasterModel:
    def __init__(self):
        self.active_disaster = None
        self.disaster_severity = 0.0 # 0.0 to 1.0
        self.ticks_remaining = 0
        self.recovery_rate = 0.0
        
    def trigger_disaster(self, disaster_type: str, severity: float):
        """Trigger an emergency disaster scenario (earthquake, flood, fire, explosion)."""
        self.active_disaster = disaster_type
        self.disaster_severity = severity
        self.ticks_remaining = random.randint(15, 30) # number of clock cycles to recovery
        self.recovery_rate = 1.0 / self.ticks_remaining

    def update_disaster(self) -> Dict[str, Any]:
        """Update active disaster recovery parameters."""
        if not self.active_disaster:
            return {"active": False}
            
        self.ticks_remaining -= 1
        self.disaster_severity = max(0.0, self.disaster_severity - self.recovery_rate)
        
        if self.ticks_remaining <= 0 or self.disaster_severity <= 0.05:
            resolved_disaster = self.active_disaster
            self.active_disaster = None
            self.disaster_severity = 0.0
            return {
                "active": False,
                "event": "resolved",
                "resolved_disaster": resolved_disaster
            }
            
        # Estimate metrics
        affected_population = int(self.disaster_severity * 85000)
        infra_damage_percent = self.disaster_severity * 75.0
        estimated_recovery_time_hrs = self.ticks_remaining * 2
        economic_loss_millions = self.disaster_severity * 150.0
        
        return {
            "active": True,
            "disaster_type": self.active_disaster,
            "severity": round(self.disaster_severity, 2),
            "affected_population": affected_population,
            "infrastructure_damage_percentage": round(infra_damage_percent, 1),
            "estimated_recovery_time_hrs": estimated_recovery_time_hrs,
            "economic_loss_millions": round(economic_loss_millions, 1)
        }
        
    def get_impact_modifiers(self) -> Dict[str, Any]:
        """Returns adjustments to apply to traffic, grid, and power based on disasters."""
        if not self.active_disaster:
            return {}
            
        sev = self.disaster_severity
        if self.active_disaster == "earthquake":
            return {
                "traffic_congestion_add": sev * 50.0,
                "power_grid_load_add": sev * 30.0,
                "speed_multiplier": 0.4,
                "risk_multiplier": 3.0
            }
        elif self.active_disaster == "fire":
            return {
                "traffic_congestion_add": sev * 25.0,
                "power_grid_load_add": sev * 15.0,
                "speed_multiplier": 0.7,
                "risk_multiplier": 2.0
            }
        elif self.active_disaster == "power_outage":
            return {
                "power_grid_load_add": 100.0, # grid crash
                "traffic_congestion_add": sev * 40.0, # traffic lights off
                "speed_multiplier": 0.5,
                "risk_multiplier": 1.8
            }
        return {}

disaster_model = DisasterModel()
