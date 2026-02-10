"""Domain dataclasses for arXiv paper metadata."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Author:
    """An arXiv paper author."""

    name: str
    affiliation: str


@dataclass(frozen=True)
class Paper:
    """Full metadata for an arXiv paper."""

    arxiv_id: str
    title: str
    summary: str
    authors: list["Author"]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    pdf_url: str
    abstract_url: str
    doi: str
    comment: str
    journal_ref: str


@dataclass(frozen=True)
class SearchResult:
    """Result set from an arXiv search query."""

    total_results: int
    start_index: int
    items_per_page: int
    papers: list[Paper]
