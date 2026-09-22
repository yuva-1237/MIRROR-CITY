"""
services/enso_service.py — Authoritative ENSO Climate Data Collector & Classifier

Fetches, normalizes, and caches real-time and historical El Niño–Southern Oscillation
(ENSO) data from the NOAA Climate Prediction Center (CPC) ONI (Oceanic Niño Index).

Implements 6-hour caching (ENSO_CACHE_TTL), circuit breaker protection, and a verified
authoritative baseline fallback when external networks are inaccessible.
"""

import os
import json
import time
import urllib.request
import logging
from typing import Dict, Any, List, Optional
from configs.config import settings

logger = logging.getLogger("climate.enso")

SEASON_MAP = {
    "DJF": "December - February",
    "JFM": "January - March",
    "FMA": "February - April",
    "MAM": "March - May",
    "AMJ": "April - June",
    "MJJ": "May - July",
    "JJA": "June - August",
    "JAS": "July - September",
    "ASO": "August - October",
    "SON": "September - November",
    "OND": "October - December",
    "NDJ": "November - January"
}

from services.climate.enso_service import enso_coordinator_service

class EnsoService:
    def __init__(self):
        self._coordinator = enso_coordinator_service

    def get_current_enso(self, force_refresh: bool = False) -> Dict[str, Any]:
        return self._coordinator.get_current_enso(force_refresh=force_refresh)

    def get_timeline(self) -> Dict[str, Any]:
        return self._coordinator.get_timeline()


# Singleton export
enso_service = EnsoService()

