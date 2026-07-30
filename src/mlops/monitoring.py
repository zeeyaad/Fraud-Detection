from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Optional

from ..config import AppConfig, configure_logging

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


try:
    from prometheus_client import Counter, Histogram, start_http_server
except ImportError:  # pragma: no cover
    Counter = None
    Histogram = None
    start_http_server = None


class PredictionMetrics:
    def __init__(self, port: Optional[int] = None, enabled: Optional[bool] = None):
        self.enabled = enabled if enabled is not None else config.prometheus_enabled
        self.port = port or config.prometheus_port
        self.prediction_requests = None
        self.prediction_latency = None
        self.prediction_errors = None

        if self.enabled and Counter and Histogram and start_http_server:
            self.prediction_requests = Counter(
                "fraud_inference_requests_total",
                "Total number of inference requests",
            )
            self.prediction_latency = Histogram(
                "fraud_inference_latency_seconds",
                "Inference request latency in seconds",
            )
            self.prediction_errors = Counter(
                "fraud_inference_errors_total",
                "Total number of inference errors",
            )
            try:
                start_http_server(self.port)
                logger.info("Prometheus metrics server started on port %s", self.port)
            except Exception:
                logger.exception("Failed to start Prometheus metrics server")
                self.enabled = False
        else:
            if self.enabled:
                logger.warning("Prometheus client not available; metrics disabled")

    def observe_request(self, count: int = 1) -> None:
        if self.prediction_requests is not None:
            self.prediction_requests.inc(count)

    def observe_latency(self, seconds: float) -> None:
        if self.prediction_latency is not None:
            self.prediction_latency.observe(seconds)

    def observe_error(self, count: int = 1) -> None:
        if self.prediction_errors is not None:
            self.prediction_errors.inc(count)

    @contextmanager
    def time_request(self):
        start = time.perf_counter()
        try:
            yield
        except Exception:
            self.observe_error()
            raise
        finally:
            elapsed = time.perf_counter() - start
            self.observe_latency(elapsed)
