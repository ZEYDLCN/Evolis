"""Prometheus instrumentation — section 36.

Deliberately small: request latency/count/errors (the metrics FastAPI
middleware can observe for free), plus counters for the handful of
operations the spec calls out as worth watching (embedding generation, LLM
calls, background job runs). Wiring an actual Prometheus/Grafana stack to
scrape `/metrics` is a deployment concern outside this repo; this module
only owns exposing the numbers.
"""
from __future__ import annotations

import time
from contextlib import contextmanager

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

http_requests_total = Counter(
    "lifediff_http_requests_total",
    "Total HTTP requests handled",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "lifediff_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)

llm_calls_total = Counter(
    "lifediff_llm_calls_total",
    "LLM API calls, by purpose and outcome",
    ["purpose", "outcome"],  # purpose: extraction | cluster_naming | ask_explain ; outcome: success | error | fallback
)

embedding_generation_seconds = Histogram(
    "lifediff_embedding_generation_seconds",
    "Time spent generating a single embedding",
)

background_job_seconds = Histogram(
    "lifediff_background_job_seconds",
    "Background job runtime",
    ["job_name"],
)

background_job_errors_total = Counter(
    "lifediff_background_job_errors_total",
    "Background job failures",
    ["job_name"],
)


@contextmanager
def track_embedding_generation():
    start = time.perf_counter()
    try:
        yield
    finally:
        embedding_generation_seconds.observe(time.perf_counter() - start)


@contextmanager
def track_background_job(job_name: str):
    start = time.perf_counter()
    try:
        yield
    except Exception:
        background_job_errors_total.labels(job_name=job_name).inc()
        raise
    finally:
        background_job_seconds.labels(job_name=job_name).observe(time.perf_counter() - start)


def render_metrics() -> tuple[bytes, str]:
    """Returns (body, content_type) ready to hand straight to a Response."""
    return generate_latest(), CONTENT_TYPE_LATEST
