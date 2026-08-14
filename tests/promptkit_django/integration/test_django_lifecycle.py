from __future__ import annotations

import pytest
from django.test.utils import override_settings
from promptkit_django import get_client
from promptkit_django.exceptions import PromptKitDjangoConfigurationError


def installed_apps() -> list[str]:
    return ["promptkit_django"]


def valid_settings(**overrides: object) -> dict[str, object]:
    settings: dict[str, object] = {
        "BASE_URL": "https://registry.example.com",
        "API_KEY": "test-api-key",
    }
    settings.update(overrides)
    return settings


def test_startup_registers_client_with_default_timeout() -> None:
    with override_settings(PROMPTKIT=valid_settings()):
        with override_settings(INSTALLED_APPS=installed_apps()):
            client = get_client()

            assert client.timeout == 10.0
            assert get_client() is client
            client.close()


def test_fresh_app_registries_use_their_own_settings() -> None:
    with override_settings(PROMPTKIT=valid_settings(TIMEOUT=1.0)):
        with override_settings(INSTALLED_APPS=installed_apps()):
            first = get_client()
            assert first.timeout == 1.0
            first.close()

    with override_settings(PROMPTKIT=valid_settings(TIMEOUT=2.0)):
        with override_settings(INSTALLED_APPS=installed_apps()):
            second = get_client()
            assert second.timeout == 2.0
            second.close()


def test_invalid_settings_fail_during_application_startup() -> None:
    with pytest.raises(PromptKitDjangoConfigurationError) as error:
        with override_settings(PROMPTKIT={"BASE_URL": "", "API_KEY": "test-api-key"}):
            with override_settings(INSTALLED_APPS=installed_apps()):
                pass

    assert "BASE_URL" in str(error.value)
    assert "test-api-key" not in str(error.value)
