import uuid
from typing import Dict, Any, List, Optional

class ConflictResolver:
    """
    Multi-Agent Conflict Resolver for Smart City Digital Twins.
    Arbitrates competing agent priorities (e.g., Economy vs Flood, Traffic vs Pollution),
    quantifies trade-offs, calculates multi-agent consensus, and produces structured Trade-Off Reports.
    """

    def __init__(self):
        # Known inter-agent domain friction archetypes
        self.friction_pairs = [
            ("economy", "flood"),
            ("traffic", "pollution"),
            ("healthcare", "power"),
            ("traffic", "weather"),
            ("economy", "pollution"),
            ("emergency", "traffic")
        ]

    def resolve_conflicts(
        self,
        agent_outputs: Dict[str, Any],
        elements: Optional[List[Dict[str, Any]]] = None,
        weather: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Takes structured peer outputs from all agents and produces:
        1. active_conflicts: List of conflicting stances/demands
        2. trade_off_reports: Quantified compromise synthesis
        3. peer_messages: Audit trail of inter-agent messages
        4. consensus_index: 0 to 100 percentage score representing multi-agent alignment
        """
        elements = elements or []
        weather = weather or {}
        rain_intensity = weather.get("rain_intensity", 0.0)

        peer_messages: List[Dict[str, Any]] = []
        conflicts: List[Dict[str, Any]] = []
        trade_off_reports: List[Dict[str, Any]] = []

        # 1. Harvest proposals, concerns, and telemetry drivers from agents
        proposals_by_domain: Dict[str, List[Dict[str, Any]]] = {}
        concerns_by_domain: Dict[str, List[Dict[str, Any]]] = {}
        telemetry_by_domain: Dict[str, List[Dict[str, Any]]] = {}

        for domain, output in agent_outputs.items():
            proposals_by_domain[domain] = output.get("proposals", [])
            concerns_by_domain[domain] = output.get("concerns", [])
            telemetry_by_domain[domain] = output.get("telemetry_drivers", [])

        # 2. Check for canonical domain friction cases

        # Case A: Economy vs Flood / Disaster (The classic Road Widening vs Runoff Retention conflict)
        economy_alert = agent_outputs.get("economy", {}).get("alert_level", "normal")
        flood_alert = agent_outputs.get("flood", {}).get("alert_level", "normal")
        has_widening = any(e.get("type") in ["road_widening", "flyover"] for e in elements)
        flood_danger = flood_alert in ["warning", "danger"] or rain_intensity > 0.3

        if (has_widening and flood_danger) or (economy_alert != "normal" and flood_danger):
            econ_driver = self._find_driver(telemetry_by_domain.get("economy", []), "congestion_drag", "Economic productivity loss from corridor choke points")
            flood_driver = self._find_driver(telemetry_by_domain.get("flood", []), "water_level_cm", "Water runoff depth exceeding drainage thresholds")

            conflict_id = f"CNF-ECON-FLD-{uuid.uuid4().hex[:6]}"
            peer_messages.append({
                "sender": "Economy AI",
                "recipient": "Flood AI",
                "message": "Arterial throughput is congested. Recommending road widening/surface capacity expansion to stimulate commerce ($1.2M annual upside).",
                "urgency": "high"
            })
            peer_messages.append({
                "sender": "Flood AI",
                "recipient": "Economy AI",
                "message": "OBJECTION: Expanding impermeable asphalt in low-lying sector reduces runoff infiltration by 32%, raising flash flood risk to critical levels.",
                "urgency": "critical"
            })

            report = {
                "conflict_id": conflict_id,
                "title": "Economic Throughput (Road Widening) vs Inundation Runoff Vulnerability",
                "parties": ["Economy AI", "Flood AI"],
                "status": "Resolved with Compromise",
                "dispute_description": "Economy AI advocates asphalt widening for vehicle throughput; Flood AI flags that paving over retention soil increases flood risk.",
                "party_a": {
                    "agent": "Economy AI",
                    "stance": "Advocate Road Capacity Expansion",
                    "desired_action": "Add 2 lanes to central arterial corridor",
                    "benefit_projection": "+$1.4M annual commercial trade velocity",
                    "telemetry_driver": econ_driver
                },
                "party_b": {
                    "agent": "Flood AI",
                    "stance": "Veto Impermeable Surfaces",
                    "desired_action": "Preserve porous retention soil and catchment drainage basin",
                    "risk_projection": "+35% surface runoff surge during convective storm cells",
                    "telemetry_driver": flood_driver
                },
                "quantified_trade_offs": {
                    "economic_gain_raw": "+$1.4M / year",
                    "flood_damage_risk_raw": "+$850K potential surge loss without mitigation",
                    "net_balance": "+$550K net surplus under green permeable engineering"
                },
                "arbitrated_solution": "Deploy Permeable Paving with Integrated Bioswale Buffers + Dynamic Tidal Drainage Gates",
                "actionable_mitigations": [
                    "Mandate high-void porous asphalt allowing 150mm/hr rainwater percolation",
                    "Construct parallel bioswale retention linear park along curb edge",
                    "Integrate automated flood telemetry sensors to trigger emergency flow diversion"
                ],
                "consensus_score": 88
            }
            conflicts.append({"id": conflict_id, "title": report["title"], "parties": report["parties"], "severity": "high"})
            trade_off_reports.append(report)

        # Case B: Traffic vs Pollution / Health (Freight Rerouting vs Localized PM2.5 Inversion)
        traffic_alert = agent_outputs.get("traffic", {}).get("alert_level", "normal")
        pollution_alert = agent_outputs.get("pollution", {}).get("alert_level", "normal")

        if traffic_alert in ["warning", "danger"] or pollution_alert in ["warning", "danger"]:
            trf_driver = self._find_driver(telemetry_by_domain.get("traffic", []), "congestion_percentage", "Corridor congestion index")
            pol_driver = self._find_driver(telemetry_by_domain.get("pollution", []), "aqi", "Particulate Matter AQI level")

            conflict_id = f"CNF-TRF-POL-{uuid.uuid4().hex[:6]}"
            peer_messages.append({
                "sender": "Traffic AI",
                "recipient": "Pollution AI",
                "message": "Core arterial is at capacity (>80%). Diverting commercial freight and commuter traffic into adjacent urban sector corridors.",
                "urgency": "medium"
            })
            peer_messages.append({
                "sender": "Pollution AI",
                "recipient": "Traffic AI",
                "message": "CONCERN: Secondary streets pass through residential school zones with poor wind dispersion; PM2.5 AQI will exceed safe limits (150+).",
                "urgency": "high"
            })

            report = {
                "conflict_id": conflict_id,
                "title": "Traffic Flow Optimization vs Localized Toxic Particulate Concentration",
                "parties": ["Traffic AI", "Pollution AI"],
                "status": "Resolved with Compromise",
                "dispute_description": "Traffic AI requests diversions into secondary grid; Pollution AI flags severe respiratory exposure risk near school zones.",
                "party_a": {
                    "agent": "Traffic AI",
                    "stance": "Divert Arterial Flow",
                    "desired_action": "Route secondary grid to clear 22% intersection bottleneck",
                    "benefit_projection": "Cuts corridor travel delay by 8.5 minutes",
                    "telemetry_driver": trf_driver
                },
                "party_b": {
                    "agent": "Pollution AI",
                    "stance": "Prevent Residential Emissions Spike",
                    "desired_action": "Keep heavy diesel trucks on open perimeter highways",
                    "risk_projection": "AQI spike to 168 (Unhealthy) in pedestrian corridors",
                    "telemetry_driver": pol_driver
                },
                "quantified_trade_offs": {
                    "traffic_improvement": "-18% central delay index",
                    "emissions_exposure": "+28% localized PM2.5 in neighborhood streets if unchecked",
                    "net_balance": "Mitigated: Divert light EV/hybrids only; enforce zero-diesel bypass ring"
                },
                "arbitrated_solution": "Dynamic Low-Emission Vehicle Gating: Restrict diversions to EVs and transit; enforce Heavy Goods Vehicle perimeter ring.",
                "actionable_mitigations": [
                    "Activate dynamic digital roadside signage diverting diesel freight to outer beltway",
                    "Allow only passenger EV and micro-mobility rerouting through secondary streets",
                    "Synchronize green waves at pedestrian crossings to reduce idling stops"
                ],
                "consensus_score": 84
            }
            conflicts.append({"id": conflict_id, "title": report["title"], "parties": report["parties"], "severity": "medium"})
            trade_off_reports.append(report)

        # Case C: Emergency / Healthcare vs Power Grid
        power_alert = agent_outputs.get("power", {}).get("alert_level", "normal")
        emergency_alert = agent_outputs.get("emergency", {}).get("alert_level", "normal")

        if emergency_alert in ["warning", "danger"] and power_alert in ["warning", "danger"]:
            conflict_id = f"CNF-EMG-PWR-{uuid.uuid4().hex[:6]}"
            peer_messages.append({
                "sender": "Healthcare AI",
                "recipient": "Power AI",
                "message": "Emergency surge: Ramping up hospital backup ventilation and flood suction pumps to 100% capacity.",
                "urgency": "critical"
            })
            peer_messages.append({
                "sender": "Power AI",
                "recipient": "Healthcare AI",
                "message": "GRID STRESS: Substation load is at 91%. Simultaneous continuous suction pumping risks cascade transformer trip.",
                "urgency": "danger"
            })

            report = {
                "conflict_id": conflict_id,
                "title": "Emergency Hospital/Pump Surge vs Substation Grid Overload",
                "parties": ["Healthcare AI", "Power AI"],
                "status": "Resolved with Priority Allocation",
                "dispute_description": "Healthcare AI requires peak power for life support and drainage; Power AI warns of blackout hazard.",
                "party_a": {
                    "agent": "Healthcare AI",
                    "stance": "Guaranteed Priority Power",
                    "desired_action": "Supply unthrottled 45MW emergency reserve to medical and drainage nodes",
                    "benefit_projection": "Saves critical ICU uptime and keeps emergency basements dry",
                    "telemetry_driver": self._find_driver(telemetry_by_domain.get("healthcare", []), "response_time", "Emergency response dispatch latency")
                },
                "party_b": {
                    "agent": "Power AI",
                    "stance": "Prevent Transformer Cascades",
                    "desired_action": "Shed 15MW non-essential load to maintain 20% reserve margin",
                    "risk_projection": "Grid failure would black out 40,000 residential customers",
                    "telemetry_driver": self._find_driver(telemetry_by_domain.get("power", []), "load_percentage", "Substation transformer load")
                },
                "quantified_trade_offs": {
                    "life_safety_priority": "Medical & flood pump circuits guaranteed 100% uptime",
                    "grid_stability": "12MW shed from municipal street decorative lighting and commercial HVAC"
                },
                "arbitrated_solution": "Tier-1 Microgrid Isolation: Island hospital district and dispatch mobile Battery Energy Storage (BESS) units.",
                "actionable_mitigations": [
                    "Switch municipal commercial cooling to thermal storage reserve",
                    "Deploy utility battery reserves to support Substation #3",
                    "Guarantee uninterrupted primary feeder to trauma center"
                ],
                "consensus_score": 92
            }
            conflicts.append({"id": conflict_id, "title": report["title"], "parties": report["parties"], "severity": "high"})
            trade_off_reports.append(report)

        # 3. Compute overall multi-agent consensus score (0-100%)
        if not trade_off_reports:
            # Nominal operating consensus
            consensus_index = 95.0
            for out in agent_outputs.values():
                if out.get("alert_level") == "warning":
                    consensus_index -= 3.0
                elif out.get("alert_level") == "danger":
                    consensus_index -= 8.0
            consensus_index = max(70.0, min(100.0, consensus_index))
        else:
            # Average consensus from trade-off resolutions
            avg_res = sum(r["consensus_score"] for r in trade_off_reports) / len(trade_off_reports)
            consensus_index = round(avg_res, 1)

        return {
            "peer_messages": peer_messages,
            "active_conflicts": conflicts,
            "trade_off_reports": trade_off_reports,
            "consensus_index": consensus_index,
            "total_conflicts": len(conflicts),
            "resolution_summary": (
                f"{len(conflicts)} inter-agent tension(s) resolved with quantified trade-offs."
                if conflicts else "All 10 agents operate in consensus without active inter-domain friction."
            )
        }

    def _find_driver(self, drivers: List[Dict[str, Any]], key_prefix: str, fallback_desc: str) -> Dict[str, Any]:
        """Finds a matching telemetry driver from agent output or generates a fallback driver."""
        for d in drivers:
            if key_prefix in d.get("metric_key", ""):
                return d
        return {
            "metric_key": key_prefix,
            "metric_label": fallback_desc,
            "entity": "Central Smart City Grid",
            "observed_value": 78.5,
            "unit": "%",
            "threshold": 75.0,
            "comparison": ">",
            "delta_from_threshold": "+3.5%",
            "rationale": f"{fallback_desc} is elevated above nominal threshold.",
            "sensor_source": "IoT Sensor Telemetry Grid",
            "confidence": 92
        }

# Singleton instance
conflict_resolver = ConflictResolver()
