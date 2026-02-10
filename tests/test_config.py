"""Tests for arxivsmart configuration loading and validation."""

import tempfile
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from arxivsmart.config import ArxivConfig, Config, ServiceConfig


def _write_yaml(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


def _valid_config_data() -> dict:
    return {
        "service": {
            "host": "127.0.0.1",
            "port": 7001,
            "reload": True,
            "log_level": "INFO",
        },
        "arxiv": {
            "base_url": "https://export.arxiv.org/api/query",
            "pdf_base_url": "https://arxiv.org/pdf",
            "html_base_url": "https://ar5iv.labs.arxiv.org/html",
            "rate_limit_seconds": 3.0,
            "request_timeout_seconds": 30.0,
            "max_results_limit": 2000,
        },
    }


class TestServiceConfig:
    def test_valid_service_config(self):
        config = ServiceConfig(host="127.0.0.1", port=7001, reload=True, log_level="INFO")
        assert config.host == "127.0.0.1"
        assert config.port == 7001

    def test_empty_host_raises(self):
        with pytest.raises(ValidationError):
            ServiceConfig(host="  ", port=7001, reload=True, log_level="INFO")

    def test_invalid_port_zero(self):
        with pytest.raises(ValidationError):
            ServiceConfig(host="localhost", port=0, reload=True, log_level="INFO")

    def test_invalid_port_too_high(self):
        with pytest.raises(ValidationError):
            ServiceConfig(host="localhost", port=70000, reload=True, log_level="INFO")

    def test_empty_log_level_raises(self):
        with pytest.raises(ValidationError):
            ServiceConfig(host="localhost", port=7001, reload=True, log_level="  ")


class TestArxivConfig:
    def test_valid_arxiv_config(self):
        config = ArxivConfig(
            base_url="https://export.arxiv.org/api/query",
            pdf_base_url="https://arxiv.org/pdf",
            html_base_url="https://ar5iv.labs.arxiv.org/html",
            rate_limit_seconds=3.0,
            request_timeout_seconds=30.0,
            max_results_limit=2000,
        )
        assert config.rate_limit_seconds == 3.0

    def test_empty_base_url_raises(self):
        with pytest.raises(ValidationError):
            ArxivConfig(
                base_url="  ",
                pdf_base_url="https://arxiv.org/pdf",
                html_base_url="https://ar5iv.labs.arxiv.org/html",
                rate_limit_seconds=3.0,
                request_timeout_seconds=30.0,
                max_results_limit=2000,
            )

    def test_zero_rate_limit_raises(self):
        with pytest.raises(ValidationError):
            ArxivConfig(
                base_url="https://export.arxiv.org/api/query",
                pdf_base_url="https://arxiv.org/pdf",
                html_base_url="https://ar5iv.labs.arxiv.org/html",
                rate_limit_seconds=0.0,
                request_timeout_seconds=30.0,
                max_results_limit=2000,
            )

    def test_negative_timeout_raises(self):
        with pytest.raises(ValidationError):
            ArxivConfig(
                base_url="https://export.arxiv.org/api/query",
                pdf_base_url="https://arxiv.org/pdf",
                html_base_url="https://ar5iv.labs.arxiv.org/html",
                rate_limit_seconds=3.0,
                request_timeout_seconds=-1.0,
                max_results_limit=2000,
            )

    def test_zero_max_results_raises(self):
        with pytest.raises(ValidationError):
            ArxivConfig(
                base_url="https://export.arxiv.org/api/query",
                pdf_base_url="https://arxiv.org/pdf",
                html_base_url="https://ar5iv.labs.arxiv.org/html",
                rate_limit_seconds=3.0,
                request_timeout_seconds=30.0,
                max_results_limit=0,
            )


class TestConfig:
    def test_from_yaml_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            _write_yaml(config_path, _valid_config_data())
            config = Config.from_yaml(config_path)
            assert config.service.host == "127.0.0.1"
            assert config.arxiv.rate_limit_seconds == 3.0

    def test_from_yaml_missing_file(self):
        with pytest.raises(FileNotFoundError):
            Config.from_yaml(Path("/nonexistent/config.yaml"))

    def test_from_yaml_invalid_content(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("not a mapping", encoding="utf-8")
            with pytest.raises(ValueError, match="config root must be a mapping"):
                Config.from_yaml(config_path)

    def test_from_yaml_extra_fields_rejected(self):
        data = _valid_config_data()
        data["unknown_field"] = "should fail"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            _write_yaml(config_path, data)
            with pytest.raises(ValidationError):
                Config.from_yaml(config_path)

    def test_get_service_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            _write_yaml(config_path, _valid_config_data())
            config = Config.from_yaml(config_path)
            service = config.get_service_config()
            assert service.port == 7001

    def test_get_arxiv_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            _write_yaml(config_path, _valid_config_data())
            config = Config.from_yaml(config_path)
            arxiv = config.get_arxiv_config()
            assert arxiv.max_results_limit == 2000

    def test_validate_startup_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            _write_yaml(config_path, _valid_config_data())
            config = Config.from_yaml(config_path)
            config.validate_startup()
