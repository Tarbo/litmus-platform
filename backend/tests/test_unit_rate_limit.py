from app.core.rate_limit import InMemoryRateLimiter


def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()
    now = [100.0]

    def now_fn():
        return now[0]

    assert limiter.allow('k', limit=2, window_seconds=60, now_fn=now_fn) is True
    assert limiter.allow('k', limit=2, window_seconds=60, now_fn=now_fn) is True
    assert limiter.allow('k', limit=2, window_seconds=60, now_fn=now_fn) is False


def test_rate_limiter_resets_after_window():
    limiter = InMemoryRateLimiter()
    now = [100.0]

    def now_fn():
        return now[0]

    assert limiter.allow('k', limit=1, window_seconds=10, now_fn=now_fn) is True
    assert limiter.allow('k', limit=1, window_seconds=10, now_fn=now_fn) is False
    now[0] = 111.0
    assert limiter.allow('k', limit=1, window_seconds=10, now_fn=now_fn) is True
