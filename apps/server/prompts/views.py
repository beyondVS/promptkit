"""
Django REST Framework ViewSets for Prompt & Section Registry CRUD and Search.
"""

import difflib
from typing import Any

from django.db.models import Count, ProtectedError, QuerySet, RestrictedError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from apps.server.prompts.filters import PromptFilter
from apps.server.prompts.models import Prompt, PromptCategory, Section, Version
from apps.server.prompts.serializers import (
    PromptCategoryCreateSerializer,
    PromptCategorySerializer,
    PromptDetailSerializer,
    PromptSerializer,
    RollbackRequestSerializer,
    SectionCreateSerializer,
    SectionSerializer,
    VersionDiffResponseSerializer,
    VersionSerializer,
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


class VersionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for immutable Version snapshots, rollback, and line diff comparison.
    """

    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    lookup_field = "version_number"

    def get_queryset(self) -> QuerySet[Version]:
        queryset = super().get_queryset()
        prompt_id = self.kwargs.get("prompt_id")
        if prompt_id is not None:
            prompt = get_object_or_404(Prompt, pk=prompt_id)
            return queryset.filter(prompt=prompt).order_by("-version_number")
        return queryset.order_by("-version_number")

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Protect version immutability: block direct POST creation."""
        return Response(
            {
                "detail": (
                    "Method 'POST' not allowed directly on version resources. "
                    "Version snapshots are created automatically or via rollback."
                )
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Protect version immutability: block PUT modification."""
        return Response(
            {"detail": "Method 'PUT' not allowed. Version snapshots are immutable."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Protect version immutability: block PATCH modification."""
        return Response(
            {"detail": "Method 'PATCH' not allowed. Version snapshots are immutable."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Protect version immutability: block DELETE removal."""
        return Response(
            {"detail": "Method 'DELETE' not allowed. Version snapshots cannot be deleted."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["post"], url_path="rollback")
    def rollback(self, request: Request, prompt_id: int | None = None) -> Response:
        """
        Roll back prompt to a past target version by creating a new latest version (Append-Only).
        """
        prompt_pk = prompt_id or self.kwargs.get("prompt_id")
        prompt = get_object_or_404(Prompt, pk=prompt_pk)

        serializer = RollbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_version_num = serializer.validated_data["target_version"]
        user_changelog = serializer.validated_data.get("changelog", "").strip()

        target_version = prompt.versions.filter(version_number=target_version_num).first()
        if not target_version:
            return Response(
                {"detail": f"Target version {target_version_num} not found for this prompt."},
                status=status.HTTP_404_NOT_FOUND,
            )

        latest_version = prompt.versions.order_by("-version_number").first()
        next_version_num = (latest_version.version_number + 1) if latest_version else 1
        changelog = user_changelog or f"Rolled back to v{target_version_num}"

        new_version = Version.objects.create(
            prompt=prompt,
            version_number=next_version_num,
            template_text=target_version.template_text,
            changelog=changelog,
        )

        return Response(VersionSerializer(new_version).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="diff")
    def diff(self, request: Request, prompt_id: int | None = None) -> Response:
        """
        Compare template text between two versions and return structured line-by-line diff.
        """
        prompt_pk = prompt_id or self.kwargs.get("prompt_id")
        prompt = get_object_or_404(Prompt, pk=prompt_pk)

        from_v_str = request.query_params.get("from_version")
        to_v_str = request.query_params.get("to_version")

        if not from_v_str or not to_v_str or not from_v_str.isdigit() or not to_v_str.isdigit():
            return Response(
                {"detail": "from_version and to_version integer query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from_v_num = int(from_v_str)
        to_v_num = int(to_v_str)

        from_version = prompt.versions.filter(version_number=from_v_num).first()
        to_version = prompt.versions.filter(version_number=to_v_num).first()

        if not from_version or not to_version:
            return Response(
                {"detail": "One or both of the specified versions were not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        lines_from = from_version.template_text.splitlines()
        lines_to = to_version.template_text.splitlines()
        diff_items = []
        line_number = 1

        for line in difflib.ndiff(lines_from, lines_to):
            code = line[:2]
            content = line[2:]
            if code == "  ":
                diff_items.append({"line": line_number, "op": "equal", "text": content})
                line_number += 1
            elif code == "- ":
                diff_items.append({"line": line_number, "op": "deleted", "text": content})
                line_number += 1
            elif code == "+ ":
                diff_items.append({"line": line_number, "op": "added", "text": content})
                line_number += 1

        response_serializer = VersionDiffResponseSerializer(
            {
                "prompt_id": prompt.id,
                "from_version": from_v_num,
                "to_version": to_v_num,
                "diff": diff_items,
            }
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)


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
