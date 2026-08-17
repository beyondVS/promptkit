"""Validation for the host project's ``PROMPTKIT`` Django setting."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite

from promptkit import InvalidConfigurationError, PromptKitClient
from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator

from promptkit_django.exceptions import PromptKitDjangoConfigurationError


class PromptKitSettings(BaseModel):
    """Validated values used to construct one read-only PromptKit client."""

    model_config = ConfigDict(extra="forbid", strict=True)

    BASE_URL: str
    API_KEY: SecretStr
    TIMEOUT: float = 10.0
    CACHE_TTL: float = 60.0

    @field_validator("BASE_URL", mode="before")
    @classmethod
    def validate_base_url(cls, value: object) -> str:
        """Require a non-blank base URL before core SDK validation."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("API_KEY", mode="before")
    @classmethod
    def validate_api_key(cls, value: object) -> str:
        """Require a non-blank API key without rendering its value."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value

    @field_validator("TIMEOUT", mode="before")
    @classmethod
    def validate_timeout_type(cls, value: object) -> object:
        """Reject booleans before Pydantic treats them as numbers."""
        if isinstance(value, bool):
            raise ValueError("must be a positive finite number")
        return value

    @field_validator("TIMEOUT")
    @classmethod
    def validate_timeout_value(cls, value: float) -> float:
        """Require a positive finite request timeout."""
        if not isfinite(value) or value <= 0:
            raise ValueError("must be a positive finite number")
        return value

    @field_validator("CACHE_TTL", mode="before")
    @classmethod
    def validate_cache_ttl_type(cls, value: object) -> object:
        """Reject booleans before Pydantic treats them as numbers."""
        if isinstance(value, bool):
            raise ValueError("must be a non-negative finite number")
        return value

    @field_validator("CACHE_TTL")
    @classmethod
    def validate_cache_ttl_value(cls, value: float) -> float:
        """Require a finite cache duration that can explicitly disable caching."""
        if not isfinite(value) or value < 0:
            raise ValueError("must be a non-negative finite number")
        return value


def load_settings(value: object) -> PromptKitSettings:
    """Parse a ``PROMPTKIT`` mapping and expose only safe configuration failures."""
    if not isinstance(value, Mapping):
        raise PromptKitDjangoConfigurationError("Invalid PROMPTKIT configuration for: PROMPTKIT")

    try:
        return PromptKitSettings.model_validate(dict(value))
    except ValidationError as error:
        names = sorted({str(detail["loc"][0]) for detail in error.errors() if detail["loc"]})
        fields = ", ".join(names) if names else "PROMPTKIT"
        raise PromptKitDjangoConfigurationError(
            f"Invalid PROMPTKIT configuration for: {fields}"
        ) from None


def create_client(value: object) -> PromptKitClient:
    """Validate host settings and construct the configured core SDK client."""
    settings = load_settings(value)
    return create_client_from_settings(settings)


def create_client_from_settings(settings: PromptKitSettings) -> PromptKitClient:
    """Construct a core client from already validated Django integration settings."""
    try:
        return PromptKitClient(
            base_url=settings.BASE_URL,
            api_key=settings.API_KEY.get_secret_value(),
            timeout=settings.TIMEOUT,
        )
    except (InvalidConfigurationError, UnicodeError, ValueError):
        raise PromptKitDjangoConfigurationError(
            "Invalid PROMPTKIT configuration for: BASE_URL, API_KEY, TIMEOUT"
        ) from None
