"""
middleware/rate_limit.py — Mirror City Rate Limiting Middleware
===============================================================
Per-IP sliding-window rate limiter implemented as a pure ASGI middleware
(no slowapi dependency required — uses only stdlib + starlette).

Limits:
  • /api/auth/*      → 10 req / 60 s  (brute-force protection)
  • /api/admin/*     → 30 req / 60 s
  • WebSocket paths  → unlimited (long-lived connections)
  • Everything else  → 120 req / 60 s
"""

import time
import asyncio
from collections import deque, defaultdict
from typing import Callable, Dict, Deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


# ---------------------------------------------------------------------------
# Route-based limits  (path_prefix → (max_requests, window_seconds))
# ---------------------------------------------------------------------------
ROUTE_LIMITS = [
    ("/api/auth",  10,  60),
    ("/api/admin", 30,  60),
    ("/ws",         0,   0),  # 0 = unlimited
    ("/",         120,  60),  # catch-all
]

_LOCK = asyncio.Lock()

# ip → deque of timestamps
_buckets: Dict[str, Dict[str, Deque[float]]] = defaultdict(lambda: defaultdict(deque))


def _get_limit(path: str):
    """Return (max_requests, window_s) for a given path."""
    for prefix, max_req, window in ROUTE_LIMITS:
        if path.startswith(prefix):
            return max_req, window
    return 120, 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path

        max_req, window_s = _get_limit(path)

        if max_req == 0 or window_s == 0:
            # Unlimited (WebSocket etc.)
            return await call_next(request)

        now = time.monotonic()
        route_key = path.split("/")[2] if path.count("/") >= 2 else "root"
        bucket_key = f"{ip}:{route_key}"

        async with _LOCK:
            bucket = _buckets[bucket_key]["ts"]
            # Evict timestamps outside the window
            cutoff = now - window_s
            while bucket and bucket[0] < cutoff:
                bucket.popleft()

            if len(bucket) >= max_req:
                retry_after = int(window_s - (now - bucket[0])) + 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": f"Rate limit exceeded. Max {max_req} requests per {window_s}s.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            bucket.append(now)

        response = await call_next(request)

        # Expose rate-limit headers
        remaining = max(0, max_req - len(_buckets[bucket_key]["ts"]))
        response.headers["X-RateLimit-Limit"]     = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"]    = f"{window_s}s"

        return response
