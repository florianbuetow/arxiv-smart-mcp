"""End-to-end test fixtures for arxivsmart service."""

import subprocess
import time

import httpx
import pytest


@pytest.fixture(scope="session")
def service_url():
    """Start the arxivsmart service and yield its base URL."""
    process = subprocess.Popen(
        ["uv", "run", "src/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = "http://127.0.0.1:7171"
    max_wait = 15
    start_time = time.time()

    while time.time() - start_time < max_wait:
        try:
            resp = httpx.get(f"{base_url}/v1/health", timeout=2.0)
            if resp.status_code == 200:
                yield base_url
                httpx.post(f"{base_url}/v1/shutdown", timeout=5.0)
                process.wait(timeout=10)
                return
        except Exception:
            time.sleep(0.5)

    process.kill()
    pytest.fail("Service did not start within timeout")
