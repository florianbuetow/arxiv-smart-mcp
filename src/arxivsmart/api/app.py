"""FastAPI application factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from arxivsmart.api.routes_info import router as info_router
from arxivsmart.api.routes_paper import router as paper_router
from arxivsmart.api.routes_search import router as search_router
from arxivsmart.api.utils import error_response
from arxivsmart.arxiv.client import ArxivClient
from arxivsmart.arxiv.rate_limiter import RateLimiter
from arxivsmart.config import Config

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Wrap uncaught errors in the standard error envelope."""
    del request
    logger.exception("Unhandled exception")
    return error_response(status=500, message="Internal server error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle — close HTTP connection on shutdown."""
    yield
    arxiv_client: ArxivClient = app.state.arxiv_client
    arxiv_client.close()


def create_app(config: Config) -> FastAPI:
    """Create and configure FastAPI app with arXiv client."""
    config.validate_startup()

    arxiv_config = config.get_arxiv_config()

    rate_limiter = RateLimiter(min_interval_seconds=arxiv_config.rate_limit_seconds)
    arxiv_client = ArxivClient(config=arxiv_config, rate_limiter=rate_limiter)

    app = FastAPI(lifespan=lifespan)
    app.state.config = config
    app.state.arxiv_client = arxiv_client
    app.state.app_status = "healthy"
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(info_router)
    app.include_router(search_router)
    app.include_router(paper_router)

    return app
