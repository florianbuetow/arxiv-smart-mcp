"""Tests for API routes using FastAPI TestClient."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from arxivsmart.api.app import create_app
from arxivsmart.arxiv.types import Author, Paper, SearchResult
from arxivsmart.config import ArxivConfig, Config, ServiceConfig


def _make_config() -> Config:
    return Config(
        service=ServiceConfig(
            host="127.0.0.1",
            port=7171,
            reload=False,
            log_level="INFO",
        ),
        arxiv=ArxivConfig(
            base_url="https://export.arxiv.org/api/query",
            pdf_base_url="https://arxiv.org/pdf",
            html_base_url="https://ar5iv.labs.arxiv.org/html",
            rate_limit_seconds=0.01,
            request_timeout_seconds=30.0,
            max_results_limit=2000,
        ),
    )


def _make_app():
    config = _make_config()
    return create_app(config=config)


def _sample_search_result() -> SearchResult:
    return SearchResult(
        total_results=1,
        start_index=0,
        items_per_page=1,
        papers=[
            Paper(
                arxiv_id="2301.00001v1",
                title="Test Paper",
                summary="Test abstract.",
                authors=[Author(name="Alice", affiliation="MIT")],
                categories=["cs.AI"],
                primary_category="cs.AI",
                published="2023-01-01T00:00:00Z",
                updated="2023-01-01T00:00:00Z",
                pdf_url="http://arxiv.org/pdf/2301.00001v1",
                abstract_url="http://arxiv.org/abs/2301.00001v1",
                doi="10.1234/test",
                comment="10 pages",
                journal_ref="Nature 2023",
            ),
        ],
    )


class TestHealthEndpoint:
    def test_health_returns_200(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == 200
        assert data["data"]["status"] == "healthy"


class TestInfoEndpoint:
    def test_info_returns_config(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "config" in data["data"]


class TestSearchEndpoint:
    @patch("arxivsmart.api.routes_search.asyncio.to_thread")
    def test_search_returns_results(self, mock_to_thread):
        mock_to_thread.return_value = _sample_search_result()

        app = _make_app()
        client = TestClient(app)
        resp = client.post(
            "/v1/search",
            json={
                "query": "quantum computing",
                "start": 0,
                "max_results": 10,
                "sort_by": "relevance",
                "sort_order": "descending",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total_results"] == 1
        assert len(data["data"]["papers"]) == 1

    def test_search_invalid_body_returns_400(self):
        app = _make_app()
        client = TestClient(app)
        resp = client.post("/v1/search", json={"query": ""})
        assert resp.status_code == 400


class TestPaperEndpoint:
    @patch("arxivsmart.api.routes_paper.asyncio.to_thread")
    def test_get_paper_returns_detail(self, mock_to_thread):
        mock_to_thread.return_value = _sample_search_result().papers[0]

        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/paper/2301.00001v1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["arxiv_id"] == "2301.00001v1"

    @patch("arxivsmart.api.routes_paper.asyncio.to_thread")
    def test_get_paper_pdf_returns_bytes(self, mock_to_thread):
        mock_to_thread.return_value = b"%PDF-1.4 fake"

        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/paper/2301.00001v1/pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    @patch("arxivsmart.api.routes_paper.asyncio.to_thread")
    def test_get_paper_html_returns_content(self, mock_to_thread):
        mock_to_thread.return_value = "<html>content</html>"

        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/paper/2301.00001v1/html")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["content_type"] == "html"

    @patch("arxivsmart.api.routes_paper.asyncio.to_thread")
    def test_get_paper_markdown_returns_content(self, mock_to_thread):
        mock_to_thread.return_value = "# Title\n\nContent"

        app = _make_app()
        client = TestClient(app)
        resp = client.get("/v1/paper/2301.00001v1/markdown")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["content_type"] == "markdown"
