"""
URL configuration for promptkit server project.
"""

from django.contrib import admin
from django.urls import include, path

from apps.server.core.views import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", HealthCheckView.as_view(), name="api-v1-health"),
    path("api/v1/", include("apps.server.prompts.urls")),
]
