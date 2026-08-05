"""
Core API and Landing Views for promptkit server.
"""

from typing import Any

from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """
    Public health check endpoint.
    """

    authentication_classes: list[Any] = []
    permission_classes: list[Any] = [permissions.AllowAny]

    def get(self, request: Request) -> Response:
        """
        Return server status OK.
        """
        return Response(
            {"status": "ok", "service": "promptkit-server"},
            status=status.HTTP_200_OK,
        )


class LandingView(TemplateView):
    """
    Public landing page view.
    """

    template_name = "core/landing.html"
