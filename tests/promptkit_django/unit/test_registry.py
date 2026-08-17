from __future__ import annotations

import importlib

import pytest
from django.test.utils import override_settings
from promptkit_django.apps import PromptKitDjangoConfig
from promptkit_django.configuration import create_client
from promptkit_django.exceptions import PromptKitDjangoNotInitializedError
from promptkit_django.registry import get_client


def configured_app() -> PromptKitDjangoConfig:
    return PromptKitDjangoConfig("promptkit_django", importlib.import_module("promptkit_django"))


def promptkit_settings() -> dict[str, object]:
    return {"BASE_URL": "https://registry.example.com", "API_KEY": "test-api-key"}


def test_ready_registers_one_client_when_called_repeatedly() -> None:
    config = configured_app()

    with override_settings(PROMPTKIT=promptkit_settings()):
        config.ready()
        first = config.client
        config.ready()

    assert config.client is first


def test_get_client_returns_registered_client(monkeypatch: pytest.MonkeyPatch) -> None:
    config = configured_app()
    client = create_client(promptkit_settings())
    config.client = client
    monkeypatch.setattr("promptkit_django.registry.apps.get_app_config", lambda label: config)

    assert get_client() is client
    client.close()


def test_get_client_rejects_missing_or_unready_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "promptkit_django.registry.apps.get_app_config",
        lambda label: (_ for _ in ()).throw(LookupError(label)),
    )

    with pytest.raises(PromptKitDjangoNotInitializedError):
        get_client()

    config = configured_app()
    monkeypatch.setattr("promptkit_django.registry.apps.get_app_config", lambda label: config)
    with pytest.raises(PromptKitDjangoNotInitializedError):
        get_client()
