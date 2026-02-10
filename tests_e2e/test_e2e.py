"""End-to-end tests for arxivsmart service against live arXiv API.

These tests make real API calls to arXiv and respect rate limits.
Run with: just test-e2e
"""

import httpx


class TestHealthEndpoint:
    def test_health_returns_healthy(self, service_url):
        resp = httpx.get(f"{service_url}/v1/health", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "healthy"


class TestInfoEndpoint:
    def test_info_returns_config(self, service_url):
        resp = httpx.get(f"{service_url}/v1/info", timeout=10.0)
        assert resp.status_code == 200
        data = resp.json()
        assert "config" in data["data"]


class TestSearchEndpoint:
    def test_search_returns_results(self, service_url):
        resp = httpx.post(
            f"{service_url}/v1/search",
            json={
                "query": "all:electron",
                "start": 0,
                "max_results": 3,
                "sort_by": "submittedDate",
                "sort_order": "descending",
            },
            timeout=30.0,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total_results"] > 0
        assert len(data["data"]["papers"]) > 0


class TestPaperEndpoint:
    def test_get_paper_metadata(self, service_url):
        resp = httpx.get(f"{service_url}/v1/paper/2301.00001v1", timeout=30.0)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["arxiv_id"] == "2301.00001v1"
