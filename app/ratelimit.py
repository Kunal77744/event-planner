"""Sliding window rate limiter."""

import time
from collections import defaultdict, deque

from .config import RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW_SECONDS


class RateLimiter:
    """Sliding-window in-memory rate limiter per client IP address."""

    def __init__(
        self,
        limit: int = RATE_LIMIT_MAX_REQUESTS,
        window: int = RATE_LIMIT_WINDOW_SECONDS,
    ) -> None:
        """Initialize rate limiter.

        Args:
            limit: Maximum requests allowed within the window.
            window: Duration of the sliding window in seconds.
        """
        self.limit = limit
        self.window = window
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def check(self, client: str) -> bool:
        """Check if request from client is allowed within the current window.

        Args:
            client: Unique client identifier (e.g. client IP).

        Returns:
            True if request is permitted, False if limit exceeded.
        """
        now = time.monotonic()
        q = self._hits[client]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

    def clear(self) -> None:
        """Clear all rate limit state."""
        self._hits.clear()
