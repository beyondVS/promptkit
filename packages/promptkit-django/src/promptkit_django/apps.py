"""Django application configuration for eager PromptKit client registration."""

from __future__ import annotations

from django.apps import AppConfig
from django.conf import settings
from promptkit import PromptKitClient

from promptkit_django.configuration import (
    PromptKitSettings,
    create_client_from_settings,
    load_settings,
)


class PromptKitDjangoConfig(AppConfig):
    """Validate settings and register one PromptKit client during app startup."""

    default = True
    name = "promptkit_django"
    verbose_name = "PromptKit Django Integration"

    client: PromptKitClient | None = None
    client_settings: PromptKitSettings | None = None

    def ready(self) -> None:
        """Create the lifecycle-scoped client exactly once after settings load."""
        if getattr(self, "client", None) is None:
            validated = load_settings(getattr(settings, "PROMPTKIT", None))
            self.client = create_client_from_settings(validated)
            self.client_settings = validated
