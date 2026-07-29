"""
URL routing configuration for Prompt Registry API endpoints.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.server.prompts.views import PromptViewSet, SectionViewSet

router = DefaultRouter()
router.register(r"prompts", PromptViewSet, basename="prompt")
router.register(r"sections", SectionViewSet, basename="section")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "prompts/<int:prompt_id>/sections/",
        SectionViewSet.as_view({"get": "list", "post": "create"}),
        name="prompt-sections-list",
    ),
]
