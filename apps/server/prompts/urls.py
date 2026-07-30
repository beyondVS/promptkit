"""
URL routing configuration for Prompt Registry API endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.server.prompts.views import (
    PromptCategoryViewSet,
    PromptViewSet,
    SectionViewSet,
    VersionViewSet,
)

router = DefaultRouter()
router.register(r"categories", PromptCategoryViewSet, basename="category")
router.register(r"prompts", PromptViewSet, basename="prompt")
router.register(r"sections", SectionViewSet, basename="section")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "prompts/<int:prompt_id>/sections/",
        SectionViewSet.as_view({"get": "list", "post": "create"}),
        name="prompt-sections-list",
    ),
    path(
        "prompts/<int:prompt_id>/versions/",
        VersionViewSet.as_view({"get": "list", "post": "create"}),
        name="prompt-versions-list",
    ),
    path(
        "prompts/<int:prompt_id>/versions/<int:version_number>/",
        VersionViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="prompt-versions-detail",
    ),
    path(
        "prompts/<int:prompt_id>/versions/rollback/",
        VersionViewSet.as_view({"post": "rollback"}),
        name="prompt-versions-rollback",
    ),
    path(
        "prompts/<int:prompt_id>/versions/diff/",
        VersionViewSet.as_view({"get": "diff"}),
        name="prompt-versions-diff",
    ),
]
