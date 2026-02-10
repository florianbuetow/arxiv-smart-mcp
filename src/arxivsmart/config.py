"""Configuration models and loader for arxivsmart."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, field_validator


class ServiceConfig(BaseModel):
    """Service process settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    host: str
    port: int
    reload: bool
    log_level: str

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        """Ensure host is non-empty text."""
        if value.strip() == "":
            raise ValueError("service.host must not be empty")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        """Ensure port is within the TCP port range."""
        if value <= 0:
            raise ValueError("service.port must be greater than 0")
        if value > 65535:
            raise ValueError("service.port must be less than or equal to 65535")
        return value

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Ensure log level is non-empty text."""
        if value.strip() == "":
            raise ValueError("service.log_level must not be empty")
        return value


class ArxivConfig(BaseModel):
    """arXiv API settings."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    base_url: str
    pdf_base_url: str
    html_base_url: str
    rate_limit_seconds: float
    request_timeout_seconds: float
    max_results_limit: int

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        """Ensure base URL is non-empty text."""
        if value.strip() == "":
            raise ValueError("arxiv.base_url must not be empty")
        return value

    @field_validator("pdf_base_url")
    @classmethod
    def validate_pdf_base_url(cls, value: str) -> str:
        """Ensure PDF base URL is non-empty text."""
        if value.strip() == "":
            raise ValueError("arxiv.pdf_base_url must not be empty")
        return value

    @field_validator("html_base_url")
    @classmethod
    def validate_html_base_url(cls, value: str) -> str:
        """Ensure HTML base URL is non-empty text."""
        if value.strip() == "":
            raise ValueError("arxiv.html_base_url must not be empty")
        return value

    @field_validator("rate_limit_seconds")
    @classmethod
    def validate_rate_limit_seconds(cls, value: float) -> float:
        """Ensure rate limit is strictly positive."""
        if value <= 0.0:
            raise ValueError("arxiv.rate_limit_seconds must be greater than 0")
        return value

    @field_validator("request_timeout_seconds")
    @classmethod
    def validate_request_timeout_seconds(cls, value: float) -> float:
        """Ensure request timeout is strictly positive."""
        if value <= 0.0:
            raise ValueError("arxiv.request_timeout_seconds must be greater than 0")
        return value

    @field_validator("max_results_limit")
    @classmethod
    def validate_max_results_limit(cls, value: int) -> int:
        """Ensure max results limit is strictly positive."""
        if value <= 0:
            raise ValueError("arxiv.max_results_limit must be greater than 0")
        return value


class Config(BaseModel):
    """Root application configuration."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    service: ServiceConfig
    arxiv: ArxivConfig

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Config":
        """Load and validate configuration from a YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as file_handle:
            loaded: object = yaml.safe_load(file_handle)

        if not isinstance(loaded, dict):
            raise ValueError("config root must be a mapping")

        return cls.model_validate(loaded)

    def get_service_config(self) -> ServiceConfig:
        """Return service configuration."""
        return self.service

    def get_arxiv_config(self) -> ArxivConfig:
        """Return arXiv configuration."""
        return self.arxiv

    def validate_startup(self) -> None:
        """Validate prerequisites required to boot the service."""
