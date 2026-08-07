from hive_sight_advisor_api.rate_limiter import InMemoryRateLimiter


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


def test_allows_requests_up_to_the_limit() -> None:
    limiter = InMemoryRateLimiter(limit=3, window_seconds=60, clock=_FakeClock())

    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is True


def test_blocks_the_request_after_the_limit_is_reached() -> None:
    limiter = InMemoryRateLimiter(limit=3, window_seconds=60, clock=_FakeClock())

    for _ in range(3):
        assert limiter.allow("1.2.3.4") is True

    assert limiter.allow("1.2.3.4") is False


def test_a_different_key_is_unaffected_by_another_keys_usage() -> None:
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, clock=_FakeClock())

    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is False
    assert limiter.allow("5.6.7.8") is True


def test_a_request_is_allowed_again_once_the_window_elapses() -> None:
    clock = _FakeClock()
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, clock=clock)

    assert limiter.allow("1.2.3.4") is True
    assert limiter.allow("1.2.3.4") is False

    clock.advance(61)

    assert limiter.allow("1.2.3.4") is True


def test_requests_still_within_the_window_do_not_reset_the_block() -> None:
    clock = _FakeClock()
    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, clock=clock)

    assert limiter.allow("1.2.3.4") is True
    clock.advance(59)
    assert limiter.allow("1.2.3.4") is False
