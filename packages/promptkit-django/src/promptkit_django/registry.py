"""Access to the client registered by the active Django Apps registry."""

from __future__ import annotations

from django.apps import apps
from promptkit import PromptKitClient

from promptkit_django.apps import PromptKitDjangoConfig
from promptkit_django.exceptions import PromptKitDjangoNotInitializedError


def get_client() -> PromptKitClient:
    """Return the client registered during Django startup without lazy creation."""
    try:
        config = apps.get_app_config("promptkit_django")
    except LookupError as error:
        raise PromptKitDjangoNotInitializedError(
            "PromptKit Django integration is not installed or initialized"
        ) from error

    if not isinstance(config, PromptKitDjangoConfig) or config.client is None:
        raise PromptKitDjangoNotInitializedError("PromptKit Django integration is not initialized")
    return config.client
