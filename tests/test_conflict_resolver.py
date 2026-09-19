import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from agents.conflict_resolver import ConflictResolver
from ai.agent_coordinator import AgentCoordinator

def test_conflict_resolver_economy_vs_flood():
    resolver = ConflictResolver()

    # Synthetic agent outputs with Economy proposal and Flood concern
    agent_outputs = {
        "economy": {
            "name": "Economy AI",
            "domain": "economy",
            "alert_level": "warning",
            "stance": "advocate",
            "proposals": [{
                "id": "PROP-ECN-01",
                "action": "Expand Arterial Capacity & Widen Commercial Corridors",
                "target": "Downtown Corridor",
                "cost": 15000.0,
                "estimated_benefit": "+$1.4M annual commercial trade velocity"
            }],
            "concerns": [],
            "telemetry_drivers": [{
                "metric_key": "congestion_drag",
                "metric_label": "Congestion Productivity Drag",
                "entity": "Downtown Corridor",
                "observed_value": 0.145,
                "unit": "$M/day",
                "threshold": 0.100,
                "comparison": ">",
                "delta_from_threshold": "+0.045 $M",
                "rationale": "Economy Agent flagged daily congestion drag = $0.145M, threshold = $0.100M"
            }]
        },
        "flood": {
            "name": "Flood AI",
            "domain": "flood",
            "alert_level": "danger",
            "stance": "oppose",
            "proposals": [],
            "concerns": [{
                "target": "Downtown Corridor",
                "issue": "Road widening and concrete paving reduces retention soil percolation",
                "severity": "critical",
                "conflicts_with_domain": "economy"
            }],
            "telemetry_drivers": [{
                "metric_key": "water_level_cm",
                "metric_label": "Runoff Surface Water Level",
                "entity": "Basin Catchment Sector 3",
                "observed_value": 18.2,
                "unit": "cm",
                "threshold": 15.0,
                "comparison": ">",
                "delta_from_threshold": "+3.2 cm",
                "rationale": "Disaster & Flood Agent flagged water level = 18.2 cm, overflow threshold = 15.0 cm"
            }]
        },
        "traffic": {
            "name": "Traffic AI",
            "domain": "traffic",
            "alert_level": "normal",
            "proposals": [],
            "concerns": [],
            "telemetry_drivers": []
        }
    }

    elements = [{"type": "road_widening", "name": "Arterial Widening Phase 1"}]
    weather = {"rain_intensity": 0.65}

    result = resolver.resolve_conflicts(agent_outputs, elements=elements, weather=weather)

    assert result["total_conflicts"] >= 1
    assert len(result["trade_off_reports"]) >= 1

    report = result["trade_off_reports"][0]
    assert "Economy AI" in report["parties"]
    assert "Flood AI" in report["parties"]
    assert "arbitrated_solution" in report
    assert "consensus_score" in report
    assert 50 <= report["consensus_score"] <= 100
    assert len(result["peer_messages"]) >= 2
    assert "consensus_index" in result

def test_agent_coordinator_live_cycle_integration():
    coordinator = AgentCoordinator()

    telemetry = {
        "traffic": {
            "node_2_2": {"congestion_percentage": 88.5},
            "node_2_3": {"congestion_percentage": 78.0}
        },
        "air_quality": {
            "node_2_2": {"aqi": 162}
        },
        "flood": {
            "sensor_1": {"water_level_cm": 17.5, "alert_status": "danger"}
        },
        "power": {
            "node_2_2": {"load_percentage": 82.0, "node_id": "substation_01"}
        },
        "crowd": {
            "plaza": {"density_people_m2": 0.8}
        },
        "weather": {
            "temp": 22.0,
            "condition": "Heavy Rain",
            "rain_intensity": 0.7
        },
        "transit": []
    }

    cycle = coordinator.run_live_cycle(telemetry, elements=[{"type": "road_widening"}])

    assert "agent_outputs" in cycle
    assert "master_recommendation" in cycle
    assert "collaboration_loop" in cycle

    loop = cycle["collaboration_loop"]
    assert "active_conflicts" in loop
    assert "trade_off_reports" in loop
    assert "consensus_index" in loop

    # Check that master recommendation has telemetry drivers
    rec = cycle["master_recommendation"]
    assert "telemetry_drivers" in rec
    assert len(rec["telemetry_drivers"]) > 0
    assert "observed_value" in rec["telemetry_drivers"][0]
    assert "threshold" in rec["telemetry_drivers"][0]
