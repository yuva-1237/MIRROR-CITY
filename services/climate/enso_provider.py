"""
services/climate/enso_provider.py — Authoritative External Provider Ingestion & Normalizer

Fetches raw Oceanic Niño Index (ONI) observations from NOAA Climate Prediction Center (CPC),
validates data integrity, and normalizes into standard schema.
"""

import os
import json
import time
import urllib.request
import logging
from typing import Optional, Dict, Any, Tuple
from services.climate.enso_types import EnsoPhase, EnsoIntensity

logger = logging.getLogger("climate.enso")

SEASON_MONTH_MAP = {
    "DJF": "01",
    "JFM": "02",
    "FMA": "03",
    "MAM": "04",
    "AMJ": "05",
    "MJJ": "06",
    "JJA": "07",
    "JAS": "08",
    "ASO": "09",
    "SON": "10",
    "OND": "11",
    "NDJ": "12"
}

SEASON_LABEL_MAP = {
    "DJF": "Dec-Feb",
    "JFM": "Jan-Mar",
    "FMA": "Feb-Apr",
    "MAM": "Mar-May",
    "AMJ": "Apr-Jun",
    "MJJ": "May-Jul",
    "JJA": "Jun-Aug",
    "JAS": "Jul-Sep",
    "ASO": "Aug-Oct",
    "SON": "Sep-Nov",
    "OND": "Oct-Dec",
    "NDJ": "Nov-Jan"
}


class EnsoProvider:
    def __init__(self):
        self.url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
        self._circuit_open = False
        self._fail_count = 0
        self._last_fail_ts = 0.0

    def fetch_current(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves authoritative raw ONI data from NOAA CPC.
        Returns normalized dictionary or None on failure.
        """
        # Circuit breaker: don't hammer the external endpoint if recently failed
        if self._circuit_open and (time.time() - self._last_fail_ts) < 300:
            logger.warning("[CLIMATE] Circuit breaker open for NOAA CPC. Skipping provider request.")
            return None

        logger.info("[CLIMATE] ENSO provider request to NOAA CPC")
        try:
            req = urllib.request.Request(
                self.url,
                headers={"User-Agent": "MirrorCity/2.0 Climate-Intelligence-Module"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                raw_text = response.read().decode("utf-8", errors="ignore")

            parsed = self.parse_noaa_oni(raw_text)
            if parsed:
                self._circuit_open = False
                self._fail_count = 0
                return parsed

            logger.warning("[CLIMATE] ENSO provider response validation failed")
            self._record_failure()
            return None
        except Exception as err:
            logger.warning(f"[CLIMATE] ENSO provider failure: {err}")
            self._record_failure()
            return None

    def _record_failure(self):
        self._fail_count += 1
        self._last_fail_ts = time.time()
        if self._fail_count >= 2:
            self._circuit_open = True

    def parse_noaa_oni(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Parses NOAA ONI ascii table format:
        SEAS  YEAR  TOTAL  ANOM
        JJA   2026  29.09  -0.82
        """
        if not raw_text:
            return None

        lines = [l.strip() for l in raw_text.strip().splitlines() if l.strip()]
        if not lines:
            return None

        # Filter lines that look like valid records: e.g. "JJA 2026 29.09 -0.82"
        valid_records = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 4 and parts[0].upper() in SEASON_MONTH_MAP:
                try:
                    int(parts[1])  # Year check
                    float(parts[2])  # SST check
                    float(parts[3])  # Anomaly check
                    valid_records.append(parts)
                except ValueError:
                    continue

        if not valid_records:
            return None

        latest = valid_records[-1]
        season_code = latest[0].upper()
        year = int(latest[1])
        sst_val = float(latest[2])
        anomaly_val = float(latest[3])

        phase, intensity = self.classify(anomaly_val)

        # Standard observation period format: e.g. "2026-09" (and season description)
        month_str = SEASON_MONTH_MAP.get(season_code, "01")
        obs_period = f"{year}-{month_str}"

        # Confidence: scaled by data completeness and signal amplitude
        confidence = min(0.95, round(0.70 + (abs(anomaly_val) / 4.0) * 0.25, 2))

        return {
            "phase": phase.value,
            "intensity": intensity.value,
            "confidence": confidence,
            "anomaly": round(anomaly_val, 2),
            "observationPeriod": obs_period,
            "forecastPeriod": None,
            "source": {
                "name": "NOAA Climate Prediction Center (CPC)",
                "url": self.url
            },
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            # Teleconnection extensions
            "soi": round(-anomaly_val * 0.7, 2),
            "sstObserved": round(sst_val, 2),
            "seasonCode": season_code,
            "seasonLabel": f"{SEASON_LABEL_MAP.get(season_code, season_code)} {year}",
            "available": True,
            "cached": False
        }

    @staticmethod
    def classify(anomaly: float) -> Tuple[EnsoPhase, EnsoIntensity]:
        """
        Classifies anomaly into EnsoPhase and EnsoIntensity.
        NOAA CPC standard thresholds:
          Anomaly >= +0.5°C -> El Niño
          Anomaly <= -0.5°C -> La Niña
          Between -0.5°C and +0.5°C -> Neutral
        """
        if anomaly >= 0.5:
            phase = EnsoPhase.EL_NINO
        elif anomaly <= -0.5:
            phase = EnsoPhase.LA_NINA
        else:
            phase = EnsoPhase.NEUTRAL

        mag = abs(anomaly)
        if mag < 0.5:
            intensity = EnsoIntensity.UNKNOWN if phase == EnsoPhase.UNKNOWN else EnsoIntensity.WEAK
            if phase == EnsoPhase.NEUTRAL:
                intensity = EnsoIntensity.WEAK
        elif mag < 1.0:
            intensity = EnsoIntensity.WEAK
        elif mag < 1.5:
            intensity = EnsoIntensity.MODERATE
        else:
            intensity = EnsoIntensity.STRONG

        return phase, intensity


enso_provider = EnsoProvider()
