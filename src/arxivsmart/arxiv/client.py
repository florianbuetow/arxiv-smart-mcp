"""arXiv API client with rate limiting and persistent connection."""

import logging

import httpx
import markdownify

from arxivsmart.arxiv.parser import parse_entry, parse_search_response
from arxivsmart.arxiv.rate_limiter import RateLimiter
from arxivsmart.arxiv.types import Paper, SearchResult
from arxivsmart.config import ArxivConfig

logger = logging.getLogger(__name__)


class ArxivClient:
    """HTTP client for the arXiv API with rate limiting.

    Maintains a single persistent connection as required by arXiv API terms:
    "limit requests to a single connection at a time."
    """

    def __init__(self, config: ArxivConfig, rate_limiter: RateLimiter) -> None:
        """Initialize client with config, rate limiter, and persistent HTTP connection."""
        self._config = config
        self._rate_limiter = rate_limiter
        self._http = httpx.Client(timeout=config.request_timeout_seconds)

    def close(self) -> None:
        """Close the persistent HTTP connection."""
        self._http.close()

    def search(
        self,
        query: str,
        start: int,
        max_results: int,
        sort_by: str,
        sort_order: str,
    ) -> SearchResult:
        """Search arXiv for papers matching the query."""
        params: dict[str, str | int] = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        with self._rate_limiter:
            response = self._http.get(self._config.base_url, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"arXiv API returned status {response.status_code}: {response.text}")

        return parse_search_response(response.content)

    def get_paper(self, arxiv_id: str) -> Paper:
        """Fetch metadata for a single paper by arXiv ID."""
        params: dict[str, str] = {
            "id_list": arxiv_id,
        }

        with self._rate_limiter:
            response = self._http.get(self._config.base_url, params=params)

        if response.status_code != 200:
            raise RuntimeError(f"arXiv API returned status {response.status_code}: {response.text}")

        from defusedxml import ElementTree

        root = ElementTree.fromstring(response.content)
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        if len(entries) == 0:
            raise ValueError(f"no paper found with arXiv ID: {arxiv_id}")

        return parse_entry(entries[0])

    def download_pdf(self, arxiv_id: str) -> bytes:
        """Download PDF bytes for a paper."""
        url = f"{self._config.pdf_base_url}/{arxiv_id}"

        with self._rate_limiter:
            response = self._http.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"PDF download failed with status {response.status_code}")

        return response.content

    def fetch_html(self, arxiv_id: str) -> str:
        """Fetch HTML rendering of a paper from ar5iv.labs.arxiv.org."""
        url = f"{self._config.html_base_url}/{arxiv_id}"

        with self._rate_limiter:
            response = self._http.get(url)

        if response.status_code != 200:
            raise RuntimeError(f"HTML fetch failed with status {response.status_code}")

        return response.text

    def fetch_markdown(self, arxiv_id: str) -> str:
        """Fetch HTML rendering and convert to markdown."""
        html_content = self.fetch_html(arxiv_id)
        return markdownify.markdownify(html_content)
