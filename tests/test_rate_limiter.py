"""Tests for the arXiv API rate limiter."""

import threading
import time

import pytest

from arxivsmart.arxiv.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_invalid_interval_raises(self):
        with pytest.raises(ValueError, match="must be greater than 0"):
            RateLimiter(min_interval_seconds=0.0)

    def test_negative_interval_raises(self):
        with pytest.raises(ValueError, match="must be greater than 0"):
            RateLimiter(min_interval_seconds=-1.0)

    def test_context_manager_basic(self):
        limiter = RateLimiter(min_interval_seconds=0.01)
        with limiter:
            pass

    def test_rate_limiting_enforces_delay(self):
        limiter = RateLimiter(min_interval_seconds=0.1)

        with limiter:
            pass

        start = time.monotonic()
        with limiter:
            elapsed = time.monotonic() - start

        assert elapsed >= 0.09

    def test_thread_safety(self):
        limiter = RateLimiter(min_interval_seconds=0.05)
        results: list[float] = []
        lock = threading.Lock()

        def worker():
            with limiter, lock:
                results.append(time.monotonic())

        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 3
        sorted_times = sorted(results)
        for i in range(1, len(sorted_times)):
            gap = sorted_times[i] - sorted_times[i - 1]
            assert gap >= 0.04

    def test_acquire_release_manual(self):
        limiter = RateLimiter(min_interval_seconds=0.01)
        limiter.acquire()
        limiter.release()
