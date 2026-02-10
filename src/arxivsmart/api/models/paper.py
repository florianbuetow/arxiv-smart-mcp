"""Paper endpoint API models."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class AuthorDetail(BaseModel):
    """Detailed author information."""

    model_config = ConfigDict(extra="forbid")

    name: str
    affiliation: str


class PaperDetailResponse(BaseModel):
    """Full paper metadata response."""

    model_config = ConfigDict(extra="forbid")

    arxiv_id: str
    title: str
    summary: str
    authors: list[AuthorDetail]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    pdf_url: str
    abstract_url: str
    doi: str
    comment: str
    journal_ref: str


class PaperContentResponse(BaseModel):
    """Paper content response for HTML or markdown."""

    model_config = ConfigDict(extra="forbid")

    arxiv_id: str
    content: str
    content_type: Literal["markdown", "html"]
