"""Tests for HTTP clients."""

import pytest

from arxivsmart.clients.base import BaseClient


class TestBaseClient:
    def test_valid_initialization(self):
        client = BaseClient(host="localhost", port=7001)
        assert client._base_url == "http://localhost:7001"

    def test_empty_host_raises(self):
        with pytest.raises(ValueError, match="host must not be empty"):
            BaseClient(host="  ", port=7001)

    def test_zero_port_raises(self):
        with pytest.raises(ValueError, match="must be greater than 0"):
            BaseClient(host="localhost", port=0)

    def test_port_too_high_raises(self):
        with pytest.raises(ValueError, match="must be less than or equal to 65535"):
            BaseClient(host="localhost", port=70000)

    def test_as_object_map_valid(self):
        client = BaseClient(host="localhost", port=7001)
        result = client._as_object_map({"key": "value"}, "test")
        assert result == {"key": "value"}

    def test_as_object_map_not_dict_raises(self):
        client = BaseClient(host="localhost", port=7001)
        with pytest.raises(RuntimeError, match="must be a JSON object"):
            client._as_object_map("not a dict", "test")

    def test_as_object_map_non_string_key_raises(self):
        client = BaseClient(host="localhost", port=7001)
        with pytest.raises(RuntimeError, match="contains a non-string key"):
            client._as_object_map({1: "value"}, "test")
