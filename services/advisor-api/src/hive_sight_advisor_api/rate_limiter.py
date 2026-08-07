from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol


class RateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...


class InMemoryRateLimiter:
    """Sliding-window rate limiter. Correct for a single process only — see
    Slice 0013's Out Of Scope for the multi-instance limitation."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = self._clock()
        window_start = now - self._window_seconds
        hits = [hit for hit in self._hits.get(key, []) if hit > window_start]
        if len(hits) >= self._limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True
