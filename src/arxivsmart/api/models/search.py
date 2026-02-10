"""Search endpoint API models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class SearchRequest(BaseModel):
    """Search request payload."""

    model_config = ConfigDict(extra="forbid")

    query: str
    start: int
    max_results: int
    sort_by: Literal["relevance", "lastUpdatedDate", "submittedDate"]
    sort_order: Literal["ascending", "descending"]

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        """Ensure query is non-empty text."""
        if value.strip() == "":
            raise ValueError("query must not be empty")
        return value

    @field_validator("start")
    @classmethod
    def validate_start(cls, value: int) -> int:
        """Ensure start index is non-negative."""
        if value < 0:
            raise ValueError("start must be greater than or equal to 0")
        return value

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, value: int) -> int:
        """Ensure max_results is within valid range."""
        if value < 1:
            raise ValueError("max_results must be greater than or equal to 1")
        if value > 2000:
            raise ValueError("max_results must be less than or equal to 2000")
        return value


class PaperSummary(BaseModel):
    """Abbreviated paper metadata for search results."""

    model_config = ConfigDict(extra="forbid")

    arxiv_id: str
    title: str
    summary: str
    authors: list[str]
    primary_category: str
    published: str
    updated: str
    pdf_url: str


class SearchResponse(BaseModel):
    """Search response payload."""

    model_config = ConfigDict(extra="forbid")

    total_results: int
    start_index: int
    items_per_page: int
    papers: list[PaperSummary]
