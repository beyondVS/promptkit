from typing import Any

import httpx
import pytest
from promptkit import (
    AuthenticationError,
    CommunicationError,
    InvalidConfigurationError,
    InvalidLabelError,
    InvalidRequestError,
    InvalidResponseError,
    LabelNotFoundError,
    NoDeployableVersionError,
    PromptKitClient,
    PromptNotFoundError,
    RateLimitError,
    RedirectError,
)


def test_fetches_on_live_prompt_with_authenticated_exact_request(
    api_key: str,
    mock_transport: Any,
    prompt_payload: dict[str, Any],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=prompt_payload)

    client = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(handler),
    )

    prompt = client.fetch("support-reply")

    assert prompt.slug == "support-reply"
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert str(requests[0].url) == "https://registry.example.com/api/v1/prompts/support-reply/"
    assert requests[0].headers["X-PromptKit-Api-Key"] == api_key
    assert requests[0].url.params == httpx.QueryParams()
    assert client.timeout == 10.0


def test_fetches_explicit_label_and_uses_overridden_timeout(
    api_key: str,
    mock_transport: Any,
    prompt_payload: dict[str, Any],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params == httpx.QueryParams({"label": "latest"})
        return httpx.Response(200, json=prompt_payload)

    client = PromptKitClient(
        "https://registry.example.com/",
        api_key,
        timeout=2.5,
        transport=mock_transport(handler),
    )

    assert client.fetch("support-reply", label="latest").label == "latest"
    assert client.timeout == 2.5


@pytest.mark.parametrize("slug,label", [("", None), ("   ", None), ("support", "production")])
def test_rejects_invalid_request_without_calling_transport(
    api_key: str,
    mock_transport: Any,
    slug: str,
    label: str | None,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    client = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(handler),
    )

    expected_error = InvalidLabelError if label == "production" else InvalidRequestError
    with pytest.raises(expected_error) as error:
        client.fetch(slug, label=label)

    assert calls == 0
    assert api_key not in str(error.value)


@pytest.mark.parametrize("base_url", ["http://registry.example.com", "ftp://registry.example.com"])
def test_rejects_unsafe_registry_url(api_key: str, base_url: str) -> None:
    with pytest.raises(InvalidConfigurationError) as error:
        PromptKitClient(base_url, api_key)

    assert api_key not in str(error.value)


@pytest.mark.parametrize(
    ("status_code", "body", "error_type"),
    [
        (401, {}, AuthenticationError),
        (404, {}, PromptNotFoundError),
        (404, {"error": "no_deployable_version"}, NoDeployableVersionError),
        (404, {"error": "label_not_found"}, LabelNotFoundError),
        (400, {"error": "invalid_label"}, InvalidLabelError),
        (429, {}, RateLimitError),
        (302, {}, RedirectError),
    ],
)
def test_maps_api_failures_to_public_errors(
    api_key: str,
    mock_transport: Any,
    status_code: int,
    body: dict[str, Any],
    error_type: type[Exception],
) -> None:
    client = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(lambda request: httpx.Response(status_code, json=body)),
    )

    with pytest.raises(error_type):
        client.fetch("support-reply")


@pytest.mark.parametrize("failure", ["timeout", "connection"])
def test_maps_transport_failures_without_retry(
    api_key: str,
    mock_transport: Any,
    failure: str,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if failure == "timeout":
            raise httpx.ReadTimeout("timed out", request=request)
        raise httpx.ConnectError("connection failed", request=request)

    client = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(handler),
    )

    with pytest.raises(CommunicationError):
        client.fetch("support-reply")

    assert calls == 1


def test_rejects_malformed_or_incomplete_success_response(
    api_key: str,
    mock_transport: Any,
    prompt_payload: dict[str, Any],
) -> None:
    malformed = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(lambda request: httpx.Response(200, content=b"not-json")),
    )
    incomplete_payload = prompt_payload.copy()
    del incomplete_payload["sections"]
    incomplete = PromptKitClient(
        "https://registry.example.com",
        api_key,
        transport=mock_transport(lambda request: httpx.Response(200, json=incomplete_payload)),
    )

    with pytest.raises(InvalidResponseError):
        malformed.fetch("support-reply")
    with pytest.raises(InvalidResponseError):
        incomplete.fetch("support-reply")
