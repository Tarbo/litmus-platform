from collections import defaultdict, deque
from collections.abc import Callable
from time import monotonic


class InMemoryRateLimiter:
    def __init__(self):
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        now_fn: Callable[[], float] = monotonic,
    ) -> bool:
        now = now_fn()
        window_start = now - window_seconds
        bucket = self._events[key]

        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= limit:
            return False

        bucket.append(now)
        return True
