"""API response and app-state guard helpers."""

from typing import cast

from fastapi import Request
from fastapi.responses import JSONResponse

from arxivsmart.arxiv.client import ArxivClient
from arxivsmart.config import Config


def success_response(status: int, data: dict[str, object]) -> JSONResponse:
    """Build a success envelope response."""
    return JSONResponse(status_code=status, content={"status": status, "data": data})


def error_response(status: int, message: str) -> JSONResponse:
    """Build an error envelope response."""
    return JSONResponse(status_code=status, content={"status": status, "error": message})


def ensure_healthy(request: Request) -> JSONResponse | None:
    """Return a 503 envelope when app state is not healthy, or None when healthy."""
    app_status = request.app.state.app_status
    if app_status != "healthy":
        return error_response(status=503, message=f"service is {app_status}")

    return None


def get_arxiv_client(request: Request) -> ArxivClient:
    """Get ArxivClient instance from FastAPI app state."""
    if not hasattr(request.app.state, "arxiv_client"):
        raise RuntimeError("arxiv_client is not initialized on app state")
    return cast(ArxivClient, request.app.state.arxiv_client)


def get_config(request: Request) -> Config:
    """Get config instance from FastAPI app state."""
    if not hasattr(request.app.state, "config"):
        raise RuntimeError("config is not initialized on app state")
    return cast(Config, request.app.state.config)
