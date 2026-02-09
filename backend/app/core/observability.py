from __future__ import annotations

import threading
import time
from collections import defaultdict


class InMemoryRequestMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.time()
        self._total_requests = 0
        self._total_server_errors = 0
        self._total_duration_ms = 0
        self._status_counts: dict[str, int] = defaultdict(int)
        self._endpoint_counts: dict[str, int] = defaultdict(int)

    def record(self, method: str, path: str, status_code: int, duration_ms: int) -> None:
        endpoint_key = f'{method} {path}'
        status_key = str(status_code)
        with self._lock:
            self._total_requests += 1
            self._total_duration_ms += max(0, duration_ms)
            self._status_counts[status_key] += 1
            self._endpoint_counts[endpoint_key] += 1
            if status_code >= 500:
                self._total_server_errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            average_duration_ms = 0.0
            if self._total_requests:
                average_duration_ms = round(self._total_duration_ms / self._total_requests, 2)
            top_endpoints = sorted(self._endpoint_counts.items(), key=lambda item: item[1], reverse=True)[:10]
            return {
                'uptime_seconds': int(max(0, time.time() - self._started_at)),
                'total_requests': self._total_requests,
                'total_server_errors': self._total_server_errors,
                'average_duration_ms': average_duration_ms,
                'status_counts': dict(self._status_counts),
                'top_endpoints': [{'endpoint': key, 'count': count} for key, count in top_endpoints],
            }
