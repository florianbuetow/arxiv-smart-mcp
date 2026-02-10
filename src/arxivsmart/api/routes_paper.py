"""Paper routes for arXiv paper detail and content retrieval."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from arxivsmart.api.models.paper import AuthorDetail, PaperContentResponse, PaperDetailResponse
from arxivsmart.api.utils import ensure_healthy, error_response, get_arxiv_client, success_response

router = APIRouter(prefix="/v1")


@router.get("/paper/{arxiv_id}/pdf", response_model=None)
async def get_paper_pdf(request: Request, arxiv_id: str) -> JSONResponse | Response:
    """Download PDF for a paper by arXiv ID."""
    guard_response = ensure_healthy(request)
    if guard_response is not None:
        return guard_response

    arxiv_client = get_arxiv_client(request)

    try:
        pdf_bytes = await asyncio.to_thread(arxiv_client.download_pdf, arxiv_id)
    except Exception as exc:
        return error_response(status=502, message=str(exc))

    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/paper/{arxiv_id}/html")
async def get_paper_html(request: Request, arxiv_id: str) -> JSONResponse:
    """Get HTML rendering of a paper by arXiv ID."""
    guard_response = ensure_healthy(request)
    if guard_response is not None:
        return guard_response

    arxiv_client = get_arxiv_client(request)

    try:
        html_content = await asyncio.to_thread(arxiv_client.fetch_html, arxiv_id)
    except Exception as exc:
        return error_response(status=502, message=str(exc))

    response = PaperContentResponse(
        arxiv_id=arxiv_id,
        content=html_content,
        content_type="html",
    )

    return success_response(status=200, data=response.model_dump())


@router.get("/paper/{arxiv_id}/markdown")
async def get_paper_markdown(request: Request, arxiv_id: str) -> JSONResponse:
    """Get markdown rendering of a paper by arXiv ID."""
    guard_response = ensure_healthy(request)
    if guard_response is not None:
        return guard_response

    arxiv_client = get_arxiv_client(request)

    try:
        markdown_content = await asyncio.to_thread(arxiv_client.fetch_markdown, arxiv_id)
    except Exception as exc:
        return error_response(status=502, message=str(exc))

    response = PaperContentResponse(
        arxiv_id=arxiv_id,
        content=markdown_content,
        content_type="markdown",
    )

    return success_response(status=200, data=response.model_dump())


@router.get("/paper/{arxiv_id}")
async def get_paper(request: Request, arxiv_id: str) -> JSONResponse:
    """Get full paper metadata by arXiv ID."""
    guard_response = ensure_healthy(request)
    if guard_response is not None:
        return guard_response

    arxiv_client = get_arxiv_client(request)

    try:
        paper = await asyncio.to_thread(arxiv_client.get_paper, arxiv_id)
    except Exception as exc:
        return error_response(status=502, message=str(exc))

    authors = [AuthorDetail(name=a.name, affiliation=a.affiliation) for a in paper.authors]

    response = PaperDetailResponse(
        arxiv_id=paper.arxiv_id,
        title=paper.title,
        summary=paper.summary,
        authors=authors,
        categories=paper.categories,
        primary_category=paper.primary_category,
        published=paper.published,
        updated=paper.updated,
        pdf_url=paper.pdf_url,
        abstract_url=paper.abstract_url,
        doi=paper.doi,
        comment=paper.comment,
        journal_ref=paper.journal_ref,
    )

    return success_response(status=200, data=response.model_dump())
