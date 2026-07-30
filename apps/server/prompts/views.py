"""
Django REST Framework ViewSets for Prompt & Section Registry CRUD and Search.
"""

from typing import Any

from django.db.models import Count, ProtectedError, QuerySet, RestrictedError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from apps.server.prompts.filters import PromptFilter
from apps.server.prompts.models import Prompt, PromptCategory, Section
from apps.server.prompts.serializers import (
    PromptCategoryCreateSerializer,
    PromptCategorySerializer,
    PromptDetailSerializer,
    PromptSerializer,
    SectionCreateSerializer,
    SectionSerializer,
)


class PromptCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PromptCategory CRUD operations with prompt_count metadata.
    """

    queryset = PromptCategory.objects.annotate(prompt_count=Count("prompts"))

    def get_serializer_class(self) -> type:
        if self.action in ["create", "update", "partial_update"]:
            return PromptCategoryCreateSerializer
        return PromptCategorySerializer

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Delete a category, protecting against deletion when linked prompts exist.
        """
        instance = self.get_object()
        if instance.prompts.exists():
            return Response(
                {"detail": "Cannot delete category with linked prompts."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except (ProtectedError, RestrictedError):
            return Response(
                {"detail": "Cannot delete category with linked prompts."},
                status=status.HTTP_409_CONFLICT,
            )


class PromptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Prompt asset CRUD operations and multidimensional search.
    """

    queryset = Prompt.objects.all()

    def get_queryset(self) -> QuerySet[Prompt]:
        queryset = super().get_queryset()
        queryset = PromptFilter.filter_queryset(queryset, self.request.query_params)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            fields = [f.strip() for f in ordering.split(",") if f.strip()]
            valid_fields = [
                "created_at",
                "-created_at",
                "updated_at",
                "-updated_at",
                "name",
                "-name",
                "slug",
                "-slug",
            ]
            ordering_fields = [f for f in fields if f in valid_fields]
            if ordering_fields:
                queryset = queryset.order_by(*ordering_fields)
        return queryset

    def get_serializer_class(self) -> type:
        if self.action == "retrieve":
            return PromptDetailSerializer
        return PromptSerializer


class SectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Section CRUD operations.
    """

    queryset = Section.objects.all()

    def get_queryset(self) -> QuerySet[Section]:
        queryset = super().get_queryset()
        prompt_id = self.kwargs.get("prompt_id")
        if prompt_id is not None:
            prompt = get_object_or_404(Prompt, pk=prompt_id)
            version = prompt.versions.filter(version_number=1).first()
            if not version:
                return Section.objects.none()
            return queryset.filter(version=version)
        return queryset

    def get_serializer_class(self) -> type:
        if self.action in ["create", "update", "partial_update"]:
            return SectionCreateSerializer
        return SectionSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Handle creation of a Section for a specific Prompt (via Version v1).
        """
        prompt_id = kwargs.get("prompt_id") or request.data.get("prompt")
        if prompt_id:
            prompt = get_object_or_404(Prompt, pk=prompt_id)
            version = prompt.get_or_create_default_version()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(version=version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return super().create(request, *args, **kwargs)
