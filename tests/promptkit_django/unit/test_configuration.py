from __future__ import annotations

import math

import pytest
from promptkit_django.configuration import create_client, load_settings
from promptkit_django.exceptions import PromptKitDjangoConfigurationError


def valid_settings(**overrides: object) -> dict[str, object]:
    settings: dict[str, object] = {
        "BASE_URL": "https://registry.example.com",
        "API_KEY": "test-api-key",
        "TIMEOUT": 2.5,
    }
    settings.update(overrides)
    return settings


def test_load_settings_returns_declared_values_and_default_timeout() -> None:
    settings = load_settings(valid_settings(TIMEOUT=10.0))
    defaulted = load_settings({"BASE_URL": "https://registry.example.com", "API_KEY": "key"})

    assert settings.BASE_URL == "https://registry.example.com"
    assert settings.API_KEY.get_secret_value() == "test-api-key"
    assert settings.TIMEOUT == 10.0
    assert defaulted.TIMEOUT == 10.0
    assert defaulted.CACHE_TTL == 60.0
    assert "test-api-key" not in repr(settings)


@pytest.mark.parametrize(
    ("value", "expected_names"),
    [
        (None, {"PROMPTKIT"}),
        ({}, {"BASE_URL", "API_KEY"}),
        (valid_settings(BASE_URL=""), {"BASE_URL"}),
        (valid_settings(API_KEY="  "), {"API_KEY"}),
        (valid_settings(BASE_URL=1), {"BASE_URL"}),
        (valid_settings(TIMEOUT=True), {"TIMEOUT"}),
        (valid_settings(TIMEOUT=math.nan), {"TIMEOUT"}),
        (valid_settings(CACHE_TTL=True), {"CACHE_TTL"}),
        (valid_settings(CACHE_TTL=-1), {"CACHE_TTL"}),
        (valid_settings(CACHE_TTL=math.nan), {"CACHE_TTL"}),
        (valid_settings(UNKNOWN="value"), {"UNKNOWN"}),
    ],
)
def test_load_settings_reports_affected_names_without_secret_values(
    value: object, expected_names: set[str]
) -> None:
    secret = "test-api-key"

    with pytest.raises(PromptKitDjangoConfigurationError) as error:
        load_settings(value)

    message = str(error.value)
    assert expected_names <= set(message.replace(",", "").split())
    assert secret not in message


def test_load_settings_aggregates_every_invalid_and_unknown_key() -> None:
    with pytest.raises(PromptKitDjangoConfigurationError) as error:
        load_settings(
            {
                "BASE_URL": "",
                "API_KEY": "",
                "TIMEOUT": 0,
                "CACHE_TTL": -1,
                "UNKNOWN": "value",
            }
        )

    message = str(error.value)
    for name in ("BASE_URL", "API_KEY", "TIMEOUT", "CACHE_TTL", "UNKNOWN"):
        assert name in message


def test_cache_ttl_zero_is_valid_and_disables_cache_reuse() -> None:
    settings = load_settings(valid_settings(CACHE_TTL=0))

    assert settings.CACHE_TTL == 0.0


def test_create_client_uses_validated_values() -> None:
    client = create_client(valid_settings())

    assert client.timeout == 2.5
    client.close()


def test_create_client_normalizes_unsafe_url_without_secret_disclosure() -> None:
    secret = "credential-value"

    with pytest.raises(PromptKitDjangoConfigurationError) as error:
        create_client(valid_settings(BASE_URL="http://registry.example.com", API_KEY=secret))

    assert "BASE_URL" in str(error.value)
    assert secret not in str(error.value)


@pytest.mark.parametrize("api_key", [" key with spaces ", "비밀키"])
def test_api_key_edge_cases_never_disclose_the_value(api_key: str) -> None:
    try:
        client = create_client(valid_settings(API_KEY=api_key))
    except PromptKitDjangoConfigurationError as error:
        assert api_key not in str(error)
    else:
        client.close()
