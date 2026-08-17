"""Access to the client registered by the active Django Apps registry."""

from __future__ import annotations

from django.apps import apps
from promptkit import PromptKitClient

from promptkit_django.apps import PromptKitDjangoConfig
from promptkit_django.configuration import PromptKitSettings
from promptkit_django.exceptions import PromptKitDjangoNotInitializedError


def _get_config() -> PromptKitDjangoConfig:
    """Return the initialized integration app config without lazy creation."""
    try:
        config = apps.get_app_config("promptkit_django")
    except LookupError as error:
        raise PromptKitDjangoNotInitializedError(
            "PromptKit Django integration is not installed or initialized"
        ) from error

    if not isinstance(config, PromptKitDjangoConfig) or config.client is None:
        raise PromptKitDjangoNotInitializedError("PromptKit Django integration is not initialized")
    return config


def get_client() -> PromptKitClient:
    """Return the client registered during Django startup without lazy creation."""
    client = _get_config().client
    if client is None:
        raise PromptKitDjangoNotInitializedError("PromptKit Django integration is not initialized")
    return client


def get_client_settings() -> PromptKitSettings:
    """Return validated lifecycle settings for Django-only integration helpers."""
    client_settings = _get_config().client_settings
    if client_settings is None:
        raise PromptKitDjangoNotInitializedError("PromptKit Django integration is not initialized")
    return client_settings
