"""Synchronous HTTP client for retrieving prompts from a PromptKit registry."""

from __future__ import annotations

from ipaddress import ip_address
from typing import Any
from urllib.parse import quote, urlsplit

import httpx
from pydantic import ValidationError

from promptkit.exceptions import (
    AuthenticationError,
    CommunicationError,
    InvalidConfigurationError,
    InvalidLabelError,
    InvalidRequestError,
    InvalidResponseError,
    LabelNotFoundError,
    NoDeployableVersionError,
    PromptNotFoundError,
    RateLimitError,
    RedirectError,
)
from promptkit.models import RetrievedPrompt


class PromptKitClient:
    """Retrieve published prompts using the PromptKit read-only API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        normalized_base_url = self._validate_base_url(base_url)
        if not isinstance(api_key, str) or not api_key.strip():
            raise InvalidConfigurationError("api_key must be a non-empty string")
        if isinstance(timeout, bool) or timeout <= 0:
            raise InvalidConfigurationError("timeout must be positive")

        self.timeout = timeout
        self._client = httpx.Client(
            base_url=normalized_base_url,
            headers={"X-PromptKit-Api-Key": api_key},
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=False,
        )

    def fetch(self, slug: str, *, label: str | None = None) -> RetrievedPrompt:
        """Fetch the on-live prompt or an explicitly labelled published version."""
        if not isinstance(slug, str) or not slug.strip():
            raise InvalidRequestError("slug must be a non-empty string")
        if label is not None and (not isinstance(label, str) or not label.strip()):
            raise InvalidLabelError("label must be a non-empty string when supplied")
        if label is not None and label.casefold() == "production":
            raise InvalidLabelError("the production label is not supported")

        path = f"api/v1/prompts/{quote(slug, safe='')}/"
        params: dict[str, Any] | None = None if label is None else {"label": label}
        try:
            response = self._client.get(path, params=params)
        except httpx.RequestError as error:
            raise CommunicationError("unable to communicate with the PromptKit registry") from error

        self._raise_for_error_response(response)
        try:
            return RetrievedPrompt.model_validate(response.json())
        except (ValidationError, ValueError, TypeError) as error:
            raise InvalidResponseError("registry returned an invalid prompt response") from error

    def close(self) -> None:
        """Close the underlying synchronous HTTP client."""
        self._client.close()

    @staticmethod
    def _validate_base_url(base_url: str) -> str:
        if not isinstance(base_url, str) or not base_url.strip():
            raise InvalidConfigurationError("base_url must be a non-empty URL")

        parsed = urlsplit(base_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise InvalidConfigurationError(
                "base_url must not include credentials, a query, or a fragment"
            )
        if not parsed.hostname:
            raise InvalidConfigurationError("base_url must include a hostname")
        if parsed.scheme == "https":
            return base_url.rstrip("/") + "/"
        if parsed.scheme == "http" and PromptKitClient._is_loopback_host(parsed.hostname):
            return base_url.rstrip("/") + "/"
        raise InvalidConfigurationError("base_url must use HTTPS or loopback HTTP")

    @staticmethod
    def _is_loopback_host(hostname: str) -> bool:
        if hostname == "localhost" or hostname.endswith(".localhost"):
            return True
        try:
            return ip_address(hostname).is_loopback
        except ValueError:
            return False

    @staticmethod
    def _raise_for_error_response(response: httpx.Response) -> None:
        if 200 <= response.status_code < 300:
            return
        if 300 <= response.status_code < 400:
            raise RedirectError("registry returned a redirect response")
        if response.status_code == 401:
            raise AuthenticationError("registry rejected the API key")
        if response.status_code == 429:
            raise RateLimitError("registry rate limit exceeded")

        error_code = PromptKitClient._error_code(response)
        if response.status_code == 404:
            if error_code == "no_deployable_version":
                raise NoDeployableVersionError("prompt has no deployable version")
            if error_code == "label_not_found":
                raise LabelNotFoundError("requested label was not found")
            raise PromptNotFoundError("prompt was not found")
        if response.status_code == 400 and error_code == "invalid_label":
            raise InvalidLabelError("requested label is invalid")
        raise InvalidResponseError(
            f"registry returned unsupported HTTP status {response.status_code}"
        )

    @staticmethod
    def _error_code(response: httpx.Response) -> str | None:
        try:
            body = response.json()
        except ValueError:
            return None
        if isinstance(body, dict):
            error_code = body.get("error")
            if isinstance(error_code, str):
                return error_code
        return None
