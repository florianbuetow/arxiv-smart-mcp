"""Thread-safe rate limiter for arXiv API requests."""

import threading
import time
from types import TracebackType


class RateLimiter:
    """Enforces minimum time gap between arXiv API requests.

    Uses a threading lock to ensure single-connection access and
    tracks the last request time to enforce the rate limit window.
    """

    def __init__(self, min_interval_seconds: float) -> None:
        """Initialize rate limiter with explicit interval."""
        if min_interval_seconds <= 0.0:
            raise ValueError("min_interval_seconds must be greater than 0")

        self._min_interval_seconds = min_interval_seconds
        self._lock = threading.Lock()
        self._last_request_time: float = 0.0

    def acquire(self) -> None:
        """Block until the rate limit window has passed, then acquire the lock."""
        self._lock.acquire()
        elapsed = time.monotonic() - self._last_request_time
        remaining = self._min_interval_seconds - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def release(self) -> None:
        """Record current time and release the lock."""
        self._last_request_time = time.monotonic()
        self._lock.release()

    def __enter__(self) -> "RateLimiter":
        """Context manager entry — acquire the rate limiter."""
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit — release the rate limiter."""
        self.release()
