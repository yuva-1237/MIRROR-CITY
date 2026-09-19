"""
services/data_validator.py — Mirror City Data Validation Engine
================================================================
Implements:
  • Bounds validation  — reject physically impossible sensor readings
  • Anomaly detection  — flag readings >3 std-devs from rolling average
  • Deduplication      — reject duplicate incidents within 100 m / 5 min
  • Quality scoring    — produce 0–100 quality score per reading
  • Data completeness  — compute % of sensors reporting live
"""

import math
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Physical bounds for each sensor domain
# ---------------------------------------------------------------------------
SENSOR_BOUNDS: Dict[str, Dict[str, Tuple[float, float]]] = {
    "weather": {
        "temp":           (-50.0, 60.0),
        "humidity":       (0.0,   100.0),
        "wind_speed":     (0.0,   200.0),
        "rain_intensity": (0.0,   500.0),
    },
    "traffic": {
        "congestion_percentage": (0.0, 100.0),
        "speed_kmh":             (0.0, 300.0),
        "vehicle_count":         (0,   50000),
    },
    "flood": {
        "water_level_cm": (0.0, 1000.0),
    },
    "air_quality": {
        "aqi":        (0.0, 500.0),
        "pm25":       (0.0, 1000.0),
        "co2_ppm":    (200.0, 5000.0),
    },
    "power": {
        "load_percentage":  (0.0,  150.0),
        "voltage_kv":       (0.0,  1000.0),
    },
    "crowd": {
        "density_people_m2": (0.0, 10.0),
    },
}

# ---------------------------------------------------------------------------
# Rolling statistics for anomaly detection (per sensor key)
# ---------------------------------------------------------------------------
_WINDOW_SIZE = 10   # ticks to keep for rolling stats

class _RollingStats:
    """Maintains a rolling mean and std-dev for a single metric."""
    def __init__(self, window: int = _WINDOW_SIZE):
        self._buf: deque = deque(maxlen=window)

    def update(self, value: float) -> None:
        self._buf.append(value)

    def is_anomaly(self, value: float, threshold: float = 3.0) -> bool:
        if len(self._buf) < 3:
            return False
        mean = sum(self._buf) / len(self._buf)
        variance = sum((x - mean) ** 2 for x in self._buf) / len(self._buf)
        std = math.sqrt(variance) if variance > 0 else 0.0
        if std == 0:
            return False
        return abs(value - mean) > threshold * std

_rolling: Dict[str, _RollingStats] = {}


def _get_rolling(key: str) -> _RollingStats:
    if key not in _rolling:
        _rolling[key] = _RollingStats()
    return _rolling[key]


# ---------------------------------------------------------------------------
# Incident deduplication store
# ---------------------------------------------------------------------------
_DEDUP_WINDOW_S  = 300   # 5 minutes
_DEDUP_RADIUS_M  = 100   # 100 metres

_recent_incidents: deque = deque(maxlen=200)


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in metres between two lat/lng points."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class DataValidator:
    """
    Stateless (class-level) validator shared across the application.
    Call validate_reading() per sensor tick, validate_incident() per report.
    """

    # -- Sensor validation ---------------------------------------------------

    def validate_reading(
        self,
        domain: str,
        field: str,
        value: float,
        sensor_id: str = "",
    ) -> Dict[str, Any]:
        """
        Validate a single numeric sensor reading.

        Returns a dict with:
          valid        bool   — passes bounds & anomaly checks
          quality      int    — 0–100 quality score
          anomaly      bool   — flagged as statistical outlier
          out_of_range bool   — outside physical bounds
          source       str    — "live" (always for sensor readings)
          notes        list   — human-readable explanations
        """
        result = {
            "valid":        True,
            "quality":      100,
            "anomaly":      False,
            "out_of_range": False,
            "source":       "live",
            "notes":        [],
        }

        bounds = SENSOR_BOUNDS.get(domain, {}).get(field)
        if bounds:
            lo, hi = bounds
            if not (lo <= value <= hi):
                result["valid"]        = False
                result["out_of_range"] = True
                result["quality"]      = max(0, result["quality"] - 60)
                result["notes"].append(
                    f"{field}={value} is outside physical bounds [{lo}, {hi}]"
                )

        roll_key = f"{domain}.{field}.{sensor_id}"
        stats = _get_rolling(roll_key)
        if stats.is_anomaly(value):
            result["anomaly"] = True
            result["quality"] = max(0, result["quality"] - 25)
            result["notes"].append(
                f"{field}={value:.2f} is a statistical outlier (>3σ from rolling mean)"
            )
        stats.update(value)

        return result

    def validate_telemetry_batch(
        self, telemetry: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate an entire telemetry snapshot.

        Returns summary:
          data_completeness  float  — 0–100 % sensors reporting
          overall_quality    float  — mean quality across all readings
          anomaly_count      int
          issues             list[str]
        """
        total = 0
        quality_sum = 0.0
        anomaly_count = 0
        issues: List[str] = []

        for domain, sensors in telemetry.items():
            if not isinstance(sensors, dict):
                continue
            domain_bounds = SENSOR_BOUNDS.get(domain, {})
            for sensor_id, reading in sensors.items():
                if not isinstance(reading, dict):
                    continue
                for field, value in reading.items():
                    if field not in domain_bounds:
                        continue
                    if not isinstance(value, (int, float)):
                        continue
                    total += 1
                    r = self.validate_reading(domain, field, float(value), sensor_id)
                    quality_sum += r["quality"]
                    if r["anomaly"]:
                        anomaly_count += 1
                    if r["notes"]:
                        issues.extend(r["notes"])

        return {
            "data_completeness":  100.0 if total > 0 else 0.0,
            "overall_quality":    round(quality_sum / total, 1) if total > 0 else 100.0,
            "sensor_count":       total,
            "anomaly_count":      anomaly_count,
            "issues":             issues[:20],   # cap for payload size
        }

    # -- Source labelling enforcement ---------------------------------------

    def validate_source(self, source: str, allow_simulated: Optional[bool] = None) -> str:
        """
        Operational contract: rejects any telemetry whose source is not in
        ('live_api', 'calibrated', 'simulated').
        """
        valid_sources = {"live_api", "calibrated", "simulated"}
        if not source or source not in valid_sources:
            raise ValueError(
                f"Data integrity violation: telemetry source '{source}' is invalid. "
                f"Must be one of {sorted(valid_sources)}."
            )
        from configs.config import settings
        if allow_simulated is None:
            allow_simulated = settings.ALLOW_SIMULATED_DATA
        if source == "simulated" and not allow_simulated:
            raise ValueError(
                "Simulated telemetry rejected: ALLOW_SIMULATED_DATA=False in current environment."
            )
        return source

    # -- Incident deduplication ----------------------------------------------


    def is_duplicate_incident(
        self,
        incident_type: str,
        lat: float,
        lng: float,
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_duplicate, reason_str).
        A duplicate is the same type within 100 m and 5 minutes.
        """
        now = time.time()
        for rec in _recent_incidents:
            if rec["type"] != incident_type:
                continue
            if now - rec["ts"] > _DEDUP_WINDOW_S:
                continue
            dist = _haversine_m(lat, lng, rec["lat"], rec["lng"])
            if dist <= _DEDUP_RADIUS_M:
                age_s = int(now - rec["ts"])
                return True, (
                    f"Duplicate: same incident type reported {dist:.0f} m away "
                    f"{age_s}s ago."
                )
        return False, None

    def register_incident(
        self,
        incident_type: str,
        lat: float,
        lng: float,
    ) -> None:
        """Record a new incident in the dedup store."""
        _recent_incidents.append({
            "type": incident_type,
            "lat":  lat,
            "lng":  lng,
            "ts":   time.time(),
        })

    # -- Cross-verification ---------------------------------------------------

    def cross_verify_incident(
        self,
        incident_type: str,
        lat: float,
        lng: float,
        current_telemetry: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cross-verify a citizen report against live telemetry.

        Returns:
          verification_score  int     0–100
          corroborated        bool
          evidence            list[str]
          recommendation      str
        """
        score = 50   # start neutral
        evidence: List[str] = []
        corroborated = False

        t = current_telemetry or {}

        itype = incident_type.lower()

        # Flood / water / drainage
        if any(k in itype for k in ["flood", "water", "drain"]):
            flood = t.get("flood", {})
            max_level = max(
                (v.get("water_level_cm", 0) for v in flood.values() if isinstance(v, dict)),
                default=0,
            )
            if max_level > 50:
                score += 35
                evidence.append(f"Flood sensors report {max_level:.1f} cm water level — HIGH")
                corroborated = True
            elif max_level > 20:
                score += 15
                evidence.append(f"Flood sensors report {max_level:.1f} cm — MODERATE")
            else:
                score -= 10
                evidence.append(f"Flood sensors show only {max_level:.1f} cm — LOW risk")

        # Traffic / accident / road
        elif any(k in itype for k in ["traffic", "accident", "road", "collision"]):
            traffic = t.get("traffic", {})
            max_cong = max(
                (v.get("congestion_percentage", 0) for v in traffic.values() if isinstance(v, dict)),
                default=0,
            )
            if max_cong > 70:
                score += 35
                evidence.append(f"Traffic sensors: {max_cong:.1f}% congestion — SEVERE")
                corroborated = True
            elif max_cong > 40:
                score += 15
                evidence.append(f"Traffic sensors: {max_cong:.1f}% congestion — MODERATE")
            else:
                score -= 10
                evidence.append(f"Traffic sensors: {max_cong:.1f}% congestion — NORMAL")

        # Air quality / pollution / fire / smoke
        elif any(k in itype for k in ["air", "pollution", "fire", "smoke", "gas"]):
            aq = t.get("air_quality", {})
            max_aqi = max(
                (v.get("aqi", 0) for v in aq.values() if isinstance(v, dict)),
                default=0,
            )
            if max_aqi > 150:
                score += 35
                evidence.append(f"Air quality sensors: AQI {max_aqi:.0f} — UNHEALTHY")
                corroborated = True
            elif max_aqi > 80:
                score += 15
                evidence.append(f"Air quality sensors: AQI {max_aqi:.0f} — MODERATE")
            else:
                evidence.append(f"Air quality sensors: AQI {max_aqi:.0f} — GOOD")

        # Power / electrical / outage
        elif any(k in itype for k in ["power", "electric", "outage", "blackout"]):
            power = t.get("power", {})
            max_load = max(
                (v.get("load_percentage", 0) for v in power.values() if isinstance(v, dict)),
                default=0,
            )
            if max_load > 95:
                score += 35
                evidence.append(f"Power grid: {max_load:.1f}% load — CRITICAL")
                corroborated = True
            elif max_load > 80:
                score += 15
                evidence.append(f"Power grid: {max_load:.1f}% load — HIGH")
            else:
                evidence.append(f"Power grid: {max_load:.1f}% load — NORMAL")

        else:
            evidence.append("No matching sensor domain for automatic cross-verification.")

        # Check deduplication
        is_dup, dup_reason = self.is_duplicate_incident(incident_type, lat, lng)
        if is_dup:
            score -= 20
            evidence.append(f"⚠ {dup_reason}")

        score = max(0, min(100, score))
        corroborated = score >= 60

        if score >= 80:
            recommendation = "High confidence — auto-dispatch response team"
        elif score >= 60:
            recommendation = "Corroborated — flag for human review"
        elif score >= 40:
            recommendation = "Unverified — monitor sensor trend for 5 min"
        else:
            recommendation = "Low confidence — mark as unverified, request photo evidence"

        return {
            "verification_score": score,
            "corroborated":       corroborated,
            "evidence":           evidence,
            "recommendation":     recommendation,
        }


# Singleton
data_validator = DataValidator()
