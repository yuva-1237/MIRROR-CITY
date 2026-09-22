"""
services/climate/enso_cache.py — In-memory TTL Cache with structured observability for ENSO data
"""

import time
import logging
from typing import Optional, Dict, Any
from configs.config import settings

logger = logging.getLogger("climate.enso")


class EnsoCache:
    def __init__(self, default_ttl: int = 21600):
        self._default_ttl = getattr(settings, "ENSO_CACHE_TTL", default_ttl)
        self._cached_data: Optional[Dict[str, Any]] = None
        self._cached_ts: float = 0.0

    @property
    def ttl(self) -> int:
        return getattr(settings, "ENSO_CACHE_TTL", self._default_ttl)

    def get(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached ENSO data if present and not expired.
        Logs cache hits and misses for observability.
        """
        now = time.time()
        if self._cached_data is not None and (now - self._cached_ts) < self.ttl:
            logger.info("[CLIMATE] ENSO cache hit")
            return self._cached_data
        
        logger.info("[CLIMATE] ENSO cache miss")
        return None

    def set(self, data: Dict[str, Any]) -> None:
        """Stores ENSO data in cache with current timestamp."""
        self._cached_data = data
        self._cached_ts = time.time()

    def invalidate(self) -> None:
        """Manually clear cache."""
        self._cached_data = None
        self._cached_ts = 0.0

    def is_valid(self) -> bool:
        """Checks if current cache is still fresh."""
        return self._cached_data is not None and (time.time() - self._cached_ts) < self.ttl


enso_cache = EnsoCache()
