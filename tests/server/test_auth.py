"""
Unit and integration tests for API Key authentication and URL routing (apps.server.core).
Follows PromptKit Constitution hybrid test architecture rules using django.test.TestCase.
"""

from typing import Any

from django.contrib import admin
from django.test import Client, TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.server.core.views import HealthCheckView
from apps.server.prompts.auth import PromptKitAPIKeyAuthentication


# Private Test-Only View for validating API Key Protected routes
class _TestProtectedView(APIView):
    authentication_classes: list[Any] = [PromptKitAPIKeyAuthentication]
    permission_classes: list[Any] = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(
            {"message": "Authenticated successfully with API Key."},
            status=status.HTTP_200_OK,
        )


# Test-only URL pattern configuration
test_urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="api-v1-health"),
    path("api/v1/protected/", _TestProtectedView.as_view(), name="api-v1-protected-test"),
]


@override_settings(ROOT_URLCONF=__name__)
class APIKeyAuthenticationTests(TestCase):
    """
    Tests for public health check and API Key protected endpoint access.
    """

    def setUp(self) -> None:
        self.client: Client = Client()

    def test_public_health_check_endpoint_returns_200(self) -> None:
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok", "service": "promptkit-server"})

    def test_protected_endpoint_without_api_key_returns_401(self) -> None:
        response = self.client.get("/api/v1/protected/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(), {"detail": "Invalid or missing X-PromptKit-Api-Key header."}
        )

    def test_protected_endpoint_with_invalid_api_key_returns_401(self) -> None:
        response = self.client.get(
            "/api/v1/protected/",
            HTTP_X_API_KEY="wrong-secret-key",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.json(), {"detail": "Invalid or missing X-PromptKit-Api-Key header."}
        )

    def test_protected_endpoint_with_valid_api_key_returns_200(self) -> None:
        response = self.client.get(
            "/api/v1/protected/",
            HTTP_X_API_KEY="dev-secret-key",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {"message": "Authenticated successfully with API Key."},
        )


# Export urlpatterns so Django's URLResolver can load __name__ as ROOT_URLCONF during test execution
urlpatterns = test_urlpatterns
