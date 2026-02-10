"""Tests for API request and response models."""

import pytest
from pydantic import ValidationError

from arxivsmart.api.models.info import HealthResponse, InfoResponse, ShutdownResponse
from arxivsmart.api.models.paper import AuthorDetail, PaperContentResponse, PaperDetailResponse
from arxivsmart.api.models.search import PaperSummary, SearchRequest, SearchResponse


class TestSearchRequest:
    def test_valid_request(self):
        req = SearchRequest(
            query="quantum computing",
            start=0,
            max_results=10,
            sort_by="relevance",
            sort_order="descending",
        )
        assert req.query == "quantum computing"

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(
                query="  ",
                start=0,
                max_results=10,
                sort_by="relevance",
                sort_order="descending",
            )

    def test_negative_start_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                start=-1,
                max_results=10,
                sort_by="relevance",
                sort_order="descending",
            )

    def test_zero_max_results_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                start=0,
                max_results=0,
                sort_by="relevance",
                sort_order="descending",
            )

    def test_max_results_over_2000_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                start=0,
                max_results=2001,
                sort_by="relevance",
                sort_order="descending",
            )

    def test_invalid_sort_by_raises(self):
        with pytest.raises(ValidationError):
            SearchRequest(
                query="test",
                start=0,
                max_results=10,
                sort_by="invalid",
                sort_order="descending",
            )


class TestPaperSummary:
    def test_valid_summary(self):
        summary = PaperSummary(
            arxiv_id="2301.00001v1",
            title="Test",
            summary="Abstract",
            authors=["Alice"],
            primary_category="cs.AI",
            published="2023-01-01",
            updated="2023-01-01",
            pdf_url="https://arxiv.org/pdf/2301.00001v1",
        )
        assert summary.arxiv_id == "2301.00001v1"


class TestSearchResponse:
    def test_valid_response(self):
        resp = SearchResponse(
            total_results=1,
            start_index=0,
            items_per_page=1,
            papers=[
                PaperSummary(
                    arxiv_id="2301.00001v1",
                    title="Test",
                    summary="Abstract",
                    authors=["Alice"],
                    primary_category="cs.AI",
                    published="2023-01-01",
                    updated="2023-01-01",
                    pdf_url="https://arxiv.org/pdf/2301.00001v1",
                )
            ],
        )
        assert resp.total_results == 1


class TestHealthResponse:
    def test_healthy(self):
        resp = HealthResponse(status="healthy")
        assert resp.status == "healthy"

    def test_shutting_down(self):
        resp = HealthResponse(status="shutting_down")
        assert resp.status == "shutting_down"


class TestInfoResponse:
    def test_valid(self):
        resp = InfoResponse(config={"key": "value"})
        assert resp.config["key"] == "value"


class TestShutdownResponse:
    def test_valid(self):
        resp = ShutdownResponse(message="shutdown initiated")
        assert resp.message == "shutdown initiated"


class TestPaperDetailResponse:
    def test_valid(self):
        resp = PaperDetailResponse(
            arxiv_id="2301.00001v1",
            title="Test",
            summary="Abstract",
            authors=[AuthorDetail(name="Alice", affiliation="MIT")],
            categories=["cs.AI"],
            primary_category="cs.AI",
            published="2023-01-01",
            updated="2023-01-01",
            pdf_url="https://arxiv.org/pdf/2301.00001v1",
            abstract_url="http://arxiv.org/abs/2301.00001v1",
            doi="10.1234/test",
            comment="10 pages",
            journal_ref="Nature",
        )
        assert resp.arxiv_id == "2301.00001v1"


class TestPaperContentResponse:
    def test_html_content(self):
        resp = PaperContentResponse(
            arxiv_id="2301.00001v1",
            content="<html>test</html>",
            content_type="html",
        )
        assert resp.content_type == "html"

    def test_markdown_content(self):
        resp = PaperContentResponse(
            arxiv_id="2301.00001v1",
            content="# Title",
            content_type="markdown",
        )
        assert resp.content_type == "markdown"
