"""Minimal in-memory sliding-window rate limiter.

Deliberately not a general-purpose limiter: it only guards a small set of
path prefixes (auth endpoints, where brute-forcing matters most) and keys
on client IP. Good enough for a single-instance deployment; a multi-replica
deployment needs a shared store (Redis, already provisioned for Celery)
instead of this process-local dict.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, path_prefixes: tuple[str, ...], max_requests: int, window_seconds: int):
        super().__init__(app)
        self.path_prefixes = path_prefixes
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if not any(request.url.path.startswith(p) for p in self.path_prefixes):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.monotonic()
        hits = self._hits[key]

        while hits and now - hits[0] > self.window_seconds:
            hits.popleft()

        if len(hits) >= self.max_requests:
            return JSONResponse(status_code=429, content={"detail": "Too many requests, please try again shortly."})

        hits.append(now)
        return await call_next(request)
