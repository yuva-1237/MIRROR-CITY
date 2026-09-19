import os
import random
import time
import math
import logging
from typing import Dict, Any, Optional
from configs.config import settings

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Multi-tier fallback weather service.
    
    Tier 1: Live OpenWeatherMap API (if API key configured)
    Tier 2: Redis cache (last known good reading)
    Tier 3: Historical diurnal average model
    Tier 4: AI estimation (physics-based simulation)
    
    Each returned payload includes `source` (which tier was used)
    and `confidence` (0–100) so the frontend can display a data quality badge.
    """

    def __init__(self):
        # Prefer settings over raw os.getenv so key aliases are resolved
        self.api_key = settings.OPENWEATHER_API_KEY or os.getenv("OPENWEATHER_API_KEY", "")
        # Simulation state
        self.sim_time = 0.0
        self.is_raining = False
        # Circuit breaker
        self._fail_count    = 0
        self._MAX_FAILURES  = 3
        self._circuit_open  = False     # True = skip live API
        self._last_cache: Optional[Dict[str, Any]] = None
        self._last_cache_ts: float = 0.0

    # ------------------------------------------------------------------
    def get_weather(self) -> Dict[str, Any]:
        """
        Return current weather using the best available data tier.
        Always returns a dict that includes `source` and `confidence`.
        """
        # Tier 1: Live API (only if key exists and circuit is closed)
        if self.api_key and not self._circuit_open:
            result = self._try_live_api()
            if result:
                self._fail_count = 0
                self._circuit_open = False
                result["source"]     = "live_api"
                result["confidence"] = 98
                self._last_cache    = result
                self._last_cache_ts = time.time()
                return result
            else:
                self._fail_count += 1
                if self._fail_count >= self._MAX_FAILURES:
                    self._circuit_open = True
                    logger.warning("[WeatherService] Circuit breaker OPEN — switching to cache/simulation")

        # Tier 2: Redis / in-process cache (< 5 min old)
        if self._last_cache and (time.time() - self._last_cache_ts) < 300:
            cached = dict(self._last_cache)
            cached["source"]     = "cache"
            cached["confidence"] = 80
            cached["cached_at"]  = int(time.time() - self._last_cache_ts)
            return cached

        # Tier 3: Physics-based simulation (always available)
        return self._simulate()

    # ------------------------------------------------------------------
    def _try_live_api(self) -> Optional[Dict[str, Any]]:
        """Attempt to call the OpenWeatherMap API. Returns None on failure."""
        try:
            import urllib.request, json as _json
            url = (
                f"https://api.openweathermap.org/data/2.5/weather"
                f"?q=London&appid={self.api_key}&units=metric"
            )
            with urllib.request.urlopen(url, timeout=3) as resp:
                data = _json.loads(resp.read())
            return {
                "temp":           round(data["main"]["temp"], 1),
                "humidity":       int(data["main"]["humidity"]),
                "wind_speed":     round(data["wind"]["speed"] * 3.6, 1),  # m/s → km/h
                "rain_intensity": round(data.get("rain", {}).get("1h", 0.0), 2),
                "condition":      data["weather"][0]["main"],
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    def _simulate(self) -> Dict[str, Any]:
        """Tier 4: Physics-based diurnal simulation (always succeeds)."""
        self.sim_time += 0.05

        hour = (time.localtime().tm_hour + time.localtime().tm_min / 60.0)
        base_temp = 16.0 + 8.0 * math.sin((hour - 10.0) / 24.0 * 2.0 * math.pi)

        if random.random() < 0.01:
            self.is_raining = not self.is_raining

        rain_intensity = 0.0
        if self.is_raining:
            rain_intensity = 0.3 + 0.7 * abs(math.sin(self.sim_time * 0.2))

        wind_speed = 5.0 + 15.0 * rain_intensity + random.uniform(-2, 2)
        humidity   = 40.0 + 55.0 * rain_intensity + random.uniform(-5, 5)
        humidity   = min(100.0, max(10.0, humidity))

        condition = "Clear"
        if rain_intensity > 0.7:
            condition = "Heavy Rain"
        elif rain_intensity > 0.2:
            condition = "Light Rain"
        elif humidity > 85.0:
            condition = "Mist/Fog"
        elif random.random() < 0.3:
            condition = "Cloudy"

        return {
            "temp":           round(base_temp - rain_intensity * 3.0, 1),
            "humidity":       int(humidity),
            "wind_speed":     round(wind_speed, 1),
            "rain_intensity": round(rain_intensity, 2),
            "condition":      condition,
            "source":         "simulated",
            "confidence":     65,
        }


weather_service = WeatherService()
