"""Type stubs for fastapi.responses — covers only the API surface used by arxivsmart."""

from typing import Any

class JSONResponse:
    status_code: int
    body: bytes

    def __init__(self, *, status_code: int = ..., content: Any = ..., **kwargs: Any) -> None: ...

class Response:
    status_code: int
    body: bytes
    media_type: str | None

    def __init__(self, *, content: Any = ..., status_code: int = ..., headers: dict[str, str] | None = ..., media_type: str | None = ..., **kwargs: Any) -> None: ...
