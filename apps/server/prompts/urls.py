"""
URL routing configuration for Prompt Registry API endpoints and Dashboard.
"""

from django.urls import include, path

from apps.server.prompts.views.api import SDKPromptFetchAPIView
from apps.server.prompts.views.dashboard import (
    DashboardLoginView,
    DashboardLogoutView,
    DashboardPromptCreateView,
    DashboardPromptDeleteView,
    DashboardPromptListView,
    DashboardPromptUpdateView,
)

# SDK Read-Only API URLs
api_urlpatterns = [
    path("prompts/<str:slug>/", SDKPromptFetchAPIView.as_view(), name="sdk-prompt-fetch"),
]

# Dashboard URLs
dashboard_urlpatterns = [
    path("login/", DashboardLoginView.as_view(), name="dashboard-login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard-logout"),
    path("", DashboardPromptListView.as_view(), name="dashboard-prompt-list"),
    path("prompts/create/", DashboardPromptCreateView.as_view(), name="dashboard-prompt-create"),
    path(
        "prompts/<int:pk>/edit/",
        DashboardPromptUpdateView.as_view(),
        name="dashboard-prompt-update",
    ),
    path(
        "prompts/<int:pk>/delete/",
        DashboardPromptDeleteView.as_view(),
        name="dashboard-prompt-delete",
    ),
]

urlpatterns = [
    # Dashboard routes
    path("", include(dashboard_urlpatterns)),
    # API routes
    path("v1/", include(api_urlpatterns)),
]
