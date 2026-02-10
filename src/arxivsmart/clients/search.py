"""HTTP client for arxivsmart search endpoints."""

from typing import cast

from arxivsmart.arxiv.types import Author, Paper, SearchResult
from arxivsmart.clients.base import BaseClient


class SearchClient(BaseClient):
    """Client for arXiv search operations via the arxivsmart service."""

    def search(
        self,
        query: str,
        start: int,
        max_results: int,
        sort_by: str,
        sort_order: str,
    ) -> SearchResult:
        """Search for papers via the arxivsmart service."""
        payload: dict[str, object] = {
            "query": query,
            "start": start,
            "max_results": max_results,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }
        data = self._request(method="POST", path="/v1/search", payload=payload, require_healthy=True)
        return _parse_search_result(data)


def _require_str(data: dict[str, object], key: str) -> str:
    """Extract and validate a required string field from a data dict."""
    value = data[key]
    if not isinstance(value, str):
        raise RuntimeError(f"{key} must be a string")
    return value


def _require_int(data: dict[str, object], key: str) -> int:
    """Extract and validate a required integer field from a data dict."""
    value = data[key]
    if not isinstance(value, int):
        raise RuntimeError(f"{key} must be an integer")
    return value


def _parse_authors_summary(data: dict[str, object]) -> list[Author]:
    """Parse author name strings from search response summary."""
    raw_authors = data["authors"]
    if not isinstance(raw_authors, list):
        raise RuntimeError("authors must be a list")

    authors: list[Author] = []
    for raw_author in cast(list[object], raw_authors):
        if not isinstance(raw_author, str):
            raise RuntimeError("author name must be a string")
        authors.append(Author(name=raw_author, affiliation=""))
    return authors


def _parse_search_result(data: dict[str, object]) -> SearchResult:
    """Parse search response data into domain objects."""
    raw_papers = data["papers"]
    if not isinstance(raw_papers, list):
        raise RuntimeError("papers must be a list")

    papers: list[Paper] = []
    for raw_paper in cast(list[object], raw_papers):
        if not isinstance(raw_paper, dict):
            raise RuntimeError("each paper must be an object")
        papers.append(_parse_paper_summary(cast(dict[str, object], raw_paper)))

    return SearchResult(
        total_results=_require_int(data, "total_results"),
        start_index=_require_int(data, "start_index"),
        items_per_page=_require_int(data, "items_per_page"),
        papers=papers,
    )


def _parse_paper_summary(data: dict[str, object]) -> Paper:
    """Parse a paper summary from search response into a Paper domain object."""
    return Paper(
        arxiv_id=_require_str(data, "arxiv_id"),
        title=_require_str(data, "title"),
        summary=_require_str(data, "summary"),
        authors=_parse_authors_summary(data),
        categories=[],
        primary_category=_require_str(data, "primary_category"),
        published=_require_str(data, "published"),
        updated=_require_str(data, "updated"),
        pdf_url=_require_str(data, "pdf_url"),
        abstract_url="",
        doi="",
        comment="",
        journal_ref="",
    )
