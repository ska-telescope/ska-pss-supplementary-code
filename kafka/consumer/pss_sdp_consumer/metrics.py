from __future__ import annotations
import logging
import time
from typing import Callable

# Throughput is logged, not exported. When a metrics backend lands
# (Prometheus client, statsd, OTLP), wire it in here: the record_*
# methods are the natural fan-out point, and the periodic tick is
# already running. Kept deliberately out of scope for AT4-2181.

_log = logging.getLogger(__name__)


class ThroughputLogger:
    def __init__(self, interval_s: float, clock: Callable[[], float] = time.monotonic):
        self._interval_s = float(interval_s)
        self._clock = clock
        self._started_at = clock()
        self._last_log_at = self._started_at

        # Cumulative
        self.processed_count = 0
        self.processed_bytes = 0
        self.poison_count = 0
        self.poison_bytes = 0

        # Per-interval (reset at each tick)
        self._iv_processed = 0
        self._iv_processed_bytes = 0
        self._iv_poison = 0

    def record_processed(self, value_bytes: int) -> None:
        self.processed_count += 1
        self.processed_bytes += value_bytes
        self._iv_processed += 1
        self._iv_processed_bytes += value_bytes

    def record_poison(self, value_bytes: int) -> None:
        self.poison_count += 1
        self.poison_bytes += value_bytes
        self._iv_poison += 1

    def maybe_log(self) -> None:
        if self._interval_s <= 0:
            return
        now = self._clock()
        elapsed = now - self._last_log_at
        if elapsed < self._interval_s:
            return
        rate = self._iv_processed / elapsed if elapsed > 0 else 0.0
        mb = self._iv_processed_bytes / (1024 * 1024)
        uptime = now - self._started_at
        _log.info(
            "throughput interval=%.1fs processed=%d poison=%d rate=%.1f msg/s "
            "bytes=%.2f MB cumulative processed=%d poison=%d uptime=%.0fs",
            elapsed, self._iv_processed, self._iv_poison, rate, mb,
            self.processed_count, self.poison_count, uptime,
        )
        self._iv_processed = 0
        self._iv_processed_bytes = 0
        self._iv_poison = 0
        self._last_log_at = now

    def summary(self) -> None:
        uptime = self._clock() - self._started_at
        _log.info(
            "throughput summary processed=%d poison=%d bytes=%d uptime=%.0fs",
            self.processed_count, self.poison_count, self.processed_bytes, uptime,
        )
