"""
API Key authentication backend for Django REST Framework.
"""

import os
from typing import Any

from django.conf import settings
from django.http import HttpRequest
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication


class APIKeyUser:
    """
    Authenticated principal representing an API Key client.
    """

    is_authenticated: bool = True
    is_anonymous: bool = False
    is_staff: bool = False
    is_superuser: bool = False

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def __str__(self) -> str:
        return f"APIKeyUser({self.api_key})"


class APIKeyAuthentication(BaseAuthentication):
    """
    Custom authentication backend that validates X-API-Key header.
    """

    www_authenticate_realm: str = "api"

    def authenticate(self, request: HttpRequest) -> tuple[Any, Any] | None:
        """
        Authenticate incoming request using X-API-Key header.
        """
        api_key: str | None = request.META.get("HTTP_X_API_KEY")
        expected_key: str = getattr(
            settings,
            "PROMPTKIT_API_KEY",
            os.getenv("PROMPTKIT_API_KEY", "dev-secret-key"),
        )

        if not api_key:
            raise exceptions.AuthenticationFailed("Invalid or missing API Key.")

        if api_key != expected_key:
            raise exceptions.AuthenticationFailed("Invalid or missing API Key.")

        return (APIKeyUser(api_key), api_key)

    def authenticate_header(self, request: HttpRequest) -> str:
        """
        Return a string to be used as the value of the WWW-Authenticate header in a 401 response.
        """
        return f'Api-Key realm="{self.www_authenticate_realm}"'
