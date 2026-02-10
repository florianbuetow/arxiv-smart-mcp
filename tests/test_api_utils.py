"""Tests for API utility functions."""

import json
from unittest.mock import MagicMock

from arxivsmart.api.utils import ensure_healthy, error_response, success_response


class TestSuccessResponse:
    def test_returns_json_with_status_and_data(self):
        resp = success_response(status=200, data={"key": "value"})
        assert resp.status_code == 200
        body = json.loads(resp.body)
        assert body["status"] == 200
        assert body["data"]["key"] == "value"


class TestErrorResponse:
    def test_returns_json_with_status_and_error(self):
        resp = error_response(status=400, message="bad request")
        assert resp.status_code == 400
        body = json.loads(resp.body)
        assert body["status"] == 400
        assert body["error"] == "bad request"


class TestEnsureHealthy:
    def test_returns_none_when_healthy(self):
        request = MagicMock()
        request.app.state.app_status = "healthy"
        result = ensure_healthy(request)
        assert result is None

    def test_returns_503_when_shutting_down(self):
        request = MagicMock()
        request.app.state.app_status = "shutting_down"
        result = ensure_healthy(request)
        assert result is not None
        assert result.status_code == 503
