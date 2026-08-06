"""
URL routing configuration for Prompt Registry Dashboard.
Mounted under /dashboard/ in config/urls.py.
"""

from django.urls import path

from apps.server.prompts.views.dashboard import (
    DashboardCategoryDeleteView,
    DashboardCategoryListView,
    DashboardCategoryUpdateView,
    DashboardLabelRemoveView,
    DashboardLabelSetView,
    DashboardLoginView,
    DashboardLogoutView,
    DashboardOnLiveClearView,
    DashboardOnLiveSetView,
    DashboardPlaygroundView,
    DashboardPromptCreateView,
    DashboardPromptDeleteView,
    DashboardPromptDetailView,
    DashboardPromptListView,
    DashboardPromptUpdateView,
    DashboardSectionCreateView,
    DashboardSectionDeleteView,
    DashboardSectionUpdateView,
    DashboardVariableCreateView,
    DashboardVariableDeleteView,
    DashboardVariableSchemaView,
    DashboardVariableUpdateView,
    DashboardVersionCloneView,
    DashboardVersionDeleteView,
    DashboardVersionPublishView,
)

urlpatterns = [
    # Auth
    path("login/", DashboardLoginView.as_view(), name="dashboard-login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard-logout"),
    # Categories
    path("categories/", DashboardCategoryListView.as_view(), name="dashboard-category-list"),
    path(
        "categories/<int:pk>/edit/",
        DashboardCategoryUpdateView.as_view(),
        name="dashboard-category-update",
    ),
    path(
        "categories/<int:pk>/delete/",
        DashboardCategoryDeleteView.as_view(),
        name="dashboard-category-delete",
    ),
    # Prompts
    path("", DashboardPromptListView.as_view(), name="dashboard-prompt-list"),
    path("prompts/create/", DashboardPromptCreateView.as_view(), name="dashboard-prompt-create"),
    path("prompts/<int:pk>/", DashboardPromptDetailView.as_view(), name="dashboard-prompt-detail"),
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
    # On-Live & Label Management
    path(
        "prompts/<int:pk>/on-live/set/",
        DashboardOnLiveSetView.as_view(),
        name="dashboard-on-live-set",
    ),
    path(
        "prompts/<int:pk>/on-live/clear/",
        DashboardOnLiveClearView.as_view(),
        name="dashboard-on-live-clear",
    ),
    path(
        "prompts/<int:pk>/labels/set/", DashboardLabelSetView.as_view(), name="dashboard-label-set"
    ),
    path(
        "prompts/<int:pk>/labels/remove/",
        DashboardLabelRemoveView.as_view(),
        name="dashboard-label-remove",
    ),
    # Version Lifecycle Actions
    path(
        "versions/<int:version_id>/publish/",
        DashboardVersionPublishView.as_view(),
        name="dashboard-version-publish",
    ),
    path(
        "versions/<int:version_id>/clone/",
        DashboardVersionCloneView.as_view(),
        name="dashboard-version-clone",
    ),
    path(
        "versions/<int:version_id>/delete/",
        DashboardVersionDeleteView.as_view(),
        name="dashboard-version-delete",
    ),
    path(
        "versions/<int:version_id>/playground/",
        DashboardPlaygroundView.as_view(),
        name="dashboard-playground",
    ),
    path(
        "api/versions/<int:version_id>/variables/",
        DashboardVariableSchemaView.as_view(),
        name="dashboard-variable-schema",
    ),
    # Sections CUD
    path(
        "versions/<int:version_id>/sections/create/",
        DashboardSectionCreateView.as_view(),
        name="dashboard-section-create",
    ),
    path(
        "sections/<int:pk>/edit/",
        DashboardSectionUpdateView.as_view(),
        name="dashboard-section-update",
    ),
    path(
        "sections/<int:pk>/delete/",
        DashboardSectionDeleteView.as_view(),
        name="dashboard-section-delete",
    ),
    # Variables CUD
    path(
        "versions/<int:version_id>/variables/create/",
        DashboardVariableCreateView.as_view(),
        name="dashboard-variable-create",
    ),
    path(
        "variables/<int:pk>/edit/",
        DashboardVariableUpdateView.as_view(),
        name="dashboard-variable-update",
    ),
    path(
        "variables/<int:pk>/delete/",
        DashboardVariableDeleteView.as_view(),
        name="dashboard-variable-delete",
    ),
]
