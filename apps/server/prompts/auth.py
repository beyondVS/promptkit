"""
Authentication backend for Prompt Registry SDK Read-only requests.
Validates X-PromptKit-Api-Key HTTP header against settings.PROMPTKIT_API_KEY.
"""

from typing import Any

from django.conf import settings
from django.http import HttpRequest
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class PromptKitAPIKeyUser:
    """
    Authenticated principal representing a promptkit SDK client.
    """

    is_authenticated: bool = True
    is_anonymous: bool = False
    is_staff: bool = False
    is_superuser: bool = False

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def __str__(self) -> str:
        return f"PromptKitAPIKeyUser({self.api_key})"


class PromptKitAPIKeyAuthentication(BaseAuthentication):  # type: ignore[misc]
    """
    Validates X-PromptKit-Api-Key (or X-API-Key) HTTP header for SDK Read-only requests.
    """

    www_authenticate_realm: str = "promptkit-api"

    def authenticate(self, request: HttpRequest) -> tuple[Any, Any] | None:
        api_key: str | None = (
            request.headers.get("x-promptkit-api-key")
            or request.headers.get("X-PromptKit-Api-Key")
            or request.META.get("HTTP_X_PROMPTKIT_API_KEY")
            or request.headers.get("x-api-key")
            or request.headers.get("X-API-Key")
            or request.META.get("HTTP_X_API_KEY")
        )
        expected_key: str = str(settings.PROMPTKIT_API_KEY)

        if not api_key or api_key != expected_key:
            raise exceptions.AuthenticationFailed("Invalid or missing X-PromptKit-Api-Key header.")

        return (PromptKitAPIKeyUser(api_key), api_key)

    def authenticate_header(self, request: HttpRequest) -> str:
        return f'PromptKit-Api-Key realm="{self.www_authenticate_realm}"'
