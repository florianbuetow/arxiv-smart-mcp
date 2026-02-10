"""HTTP client for arxivsmart paper endpoints."""

from typing import cast

import httpx

from arxivsmart.arxiv.types import Author, Paper
from arxivsmart.clients.base import BaseClient


class PaperClient(BaseClient):
    """Client for arXiv paper operations via the arxivsmart service."""

    def get_paper(self, arxiv_id: str) -> Paper:
        """Get full paper metadata."""
        data = self._request(method="GET", path=f"/v1/paper/{arxiv_id}", payload=None, require_healthy=True)
        return _parse_paper_detail(data)

    def download_pdf(self, arxiv_id: str) -> bytes:
        """Download PDF bytes for a paper."""
        self._ensure_healthy()
        with httpx.Client(base_url=self._base_url, timeout=30.0) as client:
            response = client.get(f"/v1/paper/{arxiv_id}/pdf")

        if response.status_code != 200:
            raise RuntimeError(f"PDF download failed with status {response.status_code}")

        return response.content

    def get_html(self, arxiv_id: str) -> str:
        """Get HTML rendering of a paper."""
        data = self._request(method="GET", path=f"/v1/paper/{arxiv_id}/html", payload=None, require_healthy=True)
        return _require_str(data, "content")

    def get_markdown(self, arxiv_id: str) -> str:
        """Get markdown rendering of a paper."""
        data = self._request(method="GET", path=f"/v1/paper/{arxiv_id}/markdown", payload=None, require_healthy=True)
        return _require_str(data, "content")


def _require_str(data: dict[str, object], key: str) -> str:
    """Extract and validate a required string field from a data dict."""
    value = data[key]
    if not isinstance(value, str):
        raise RuntimeError(f"{key} must be a string")
    return value


def _require_str_list(data: dict[str, object], key: str) -> list[str]:
    """Extract and validate a required list of strings from a data dict."""
    raw = data[key]
    if not isinstance(raw, list):
        raise RuntimeError(f"{key} must be a list")
    result: list[str] = []
    for item in cast(list[object], raw):
        if not isinstance(item, str):
            raise RuntimeError(f"{key} items must be strings")
        result.append(item)
    return result


def _parse_authors(data: dict[str, object]) -> list[Author]:
    """Parse author detail objects from response data."""
    raw_authors = data["authors"]
    if not isinstance(raw_authors, list):
        raise RuntimeError("authors must be a list")

    authors: list[Author] = []
    for raw_author in cast(list[object], raw_authors):
        if not isinstance(raw_author, dict):
            raise RuntimeError("each author must be an object")
        author_dict = cast(dict[str, object], raw_author)
        name = author_dict.get("name")
        if not isinstance(name, str):
            raise RuntimeError("author name must be a string")
        affiliation = author_dict.get("affiliation")
        if not isinstance(affiliation, str):
            raise RuntimeError("author affiliation must be a string")
        authors.append(Author(name=name, affiliation=affiliation))
    return authors


def _parse_paper_detail(data: dict[str, object]) -> Paper:
    """Parse paper detail response into a Paper domain object."""
    return Paper(
        arxiv_id=_require_str(data, "arxiv_id"),
        title=_require_str(data, "title"),
        summary=_require_str(data, "summary"),
        authors=_parse_authors(data),
        categories=_require_str_list(data, "categories"),
        primary_category=_require_str(data, "primary_category"),
        published=_require_str(data, "published"),
        updated=_require_str(data, "updated"),
        pdf_url=_require_str(data, "pdf_url"),
        abstract_url=_require_str(data, "abstract_url"),
        doi=_require_str(data, "doi"),
        comment=_require_str(data, "comment"),
        journal_ref=_require_str(data, "journal_ref"),
    )
