"""
URL configuration for promptkit server project.
"""

from django.contrib import admin
from django.urls import include, path

from apps.server.core.views import HealthCheckView, LandingView
from apps.server.prompts.views.api import SDKPromptFetchAPIView

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="api-v1-health"),
    path("api/v1/prompts/<str:slug>/", SDKPromptFetchAPIView.as_view(), name="sdk-prompt-fetch"),
    path("dashboard/", include("apps.server.prompts.urls")),
]
