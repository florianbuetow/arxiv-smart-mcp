"""Search routes for arXiv paper queries."""

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from arxivsmart.api.models.search import PaperSummary, SearchRequest, SearchResponse
from arxivsmart.api.utils import ensure_healthy, error_response, get_arxiv_client, success_response

router = APIRouter(prefix="/v1")


@router.post("/search")
async def search(request: Request) -> JSONResponse:
    """Search arXiv for papers matching query."""
    guard_response = ensure_healthy(request)
    if guard_response is not None:
        return guard_response

    try:
        body: object = await request.json()
        search_request = SearchRequest.model_validate(body)
    except Exception as exc:
        return error_response(status=400, message=str(exc))

    arxiv_client = get_arxiv_client(request)

    try:
        result = await asyncio.to_thread(
            arxiv_client.search,
            query=search_request.query,
            start=search_request.start,
            max_results=search_request.max_results,
            sort_by=search_request.sort_by,
            sort_order=search_request.sort_order,
        )
    except Exception as exc:
        return error_response(status=502, message=str(exc))

    papers = [
        PaperSummary(
            arxiv_id=paper.arxiv_id,
            title=paper.title,
            summary=paper.summary,
            authors=[author.name for author in paper.authors],
            primary_category=paper.primary_category,
            published=paper.published,
            updated=paper.updated,
            pdf_url=paper.pdf_url,
        )
        for paper in result.papers
    ]

    response = SearchResponse(
        total_results=result.total_results,
        start_index=result.start_index,
        items_per_page=result.items_per_page,
        papers=papers,
    )

    return success_response(status=200, data=response.model_dump())
