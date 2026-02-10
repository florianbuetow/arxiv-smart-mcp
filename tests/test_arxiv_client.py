"""Tests for the arXiv API client."""

from unittest.mock import MagicMock, patch

import pytest

from arxivsmart.arxiv.client import ArxivClient
from arxivsmart.arxiv.rate_limiter import RateLimiter
from arxivsmart.config import ArxivConfig

SAMPLE_SEARCH_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <opensearch:totalResults>1</opensearch:totalResults>
  <opensearch:startIndex>0</opensearch:startIndex>
  <opensearch:itemsPerPage>1</opensearch:itemsPerPage>
  <entry>
    <id>http://arxiv.org/abs/2301.00001v1</id>
    <title>Test Paper</title>
    <summary>Abstract text.</summary>
    <author><name>Author One</name></author>
    <category term="cs.AI" />
    <arxiv:primary_category term="cs.AI" />
    <published>2023-01-01T00:00:00Z</published>
    <updated>2023-01-01T00:00:00Z</updated>
  </entry>
</feed>"""


def _make_config() -> ArxivConfig:
    return ArxivConfig(
        base_url="https://export.arxiv.org/api/query",
        pdf_base_url="https://arxiv.org/pdf",
        html_base_url="https://ar5iv.labs.arxiv.org/html",
        rate_limit_seconds=0.01,
        request_timeout_seconds=30.0,
        max_results_limit=2000,
    )


def _make_client() -> ArxivClient:
    config = _make_config()
    rate_limiter = RateLimiter(min_interval_seconds=config.rate_limit_seconds)
    return ArxivClient(config=config, rate_limiter=rate_limiter)


class TestArxivClientSearch:
    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_search_returns_results(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_SEARCH_XML

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        result = client.search(
            query="quantum computing",
            start=0,
            max_results=10,
            sort_by="relevance",
            sort_order="descending",
        )

        assert result.total_results == 1
        assert len(result.papers) == 1
        assert result.papers[0].arxiv_id == "2301.00001v1"

    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_search_non_200_raises(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        with pytest.raises(RuntimeError, match="arXiv API returned status 503"):
            client.search(
                query="test",
                start=0,
                max_results=10,
                sort_by="relevance",
                sort_order="descending",
            )


class TestArxivClientGetPaper:
    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_get_paper_returns_paper(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = SAMPLE_SEARCH_XML

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        paper = client.get_paper("2301.00001v1")
        assert paper.arxiv_id == "2301.00001v1"
        assert paper.title == "Test Paper"


class TestArxivClientDownloadPdf:
    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_download_pdf_returns_bytes(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 fake content"

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        pdf_bytes = client.download_pdf("2301.00001v1")
        assert pdf_bytes == b"%PDF-1.4 fake content"

    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_download_pdf_non_200_raises(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        with pytest.raises(RuntimeError, match="PDF download failed"):
            client.download_pdf("nonexistent")


class TestArxivClientFetchHtml:
    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_fetch_html_returns_string(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>paper content</body></html>"

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        html = client.fetch_html("2301.00001v1")
        assert "<html>" in html


class TestArxivClientFetchMarkdown:
    @patch("arxivsmart.arxiv.client.httpx.Client")
    def test_fetch_markdown_converts_html(self, mock_client_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Title</h1><p>Content</p></body></html>"

        mock_instance = MagicMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__ = MagicMock(return_value=mock_instance)
        mock_instance.__exit__ = MagicMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        client = _make_client()
        md = client.fetch_markdown("2301.00001v1")
        assert isinstance(md, str)
        assert len(md) > 0
