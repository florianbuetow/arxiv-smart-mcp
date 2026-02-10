"""Type stubs for httpx — covers only the API surface used by arxivsmart."""

from types import TracebackType
from typing import Any

class Response:
    status_code: int
    text: str
    content: bytes
    headers: dict[str, str]

    def json(self) -> Any: ...

class Client:
    def __init__(self, *, base_url: str = ..., timeout: float = ..., **kwargs: Any) -> None: ...
    def __enter__(self) -> Client: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None: ...
    def request(self, *, method: str, url: str, json: Any = ..., **kwargs: Any) -> Response: ...
    def get(self, url: str, **kwargs: Any) -> Response: ...
    def post(self, url: str, **kwargs: Any) -> Response: ...
