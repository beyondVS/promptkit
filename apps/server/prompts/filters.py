"""
Pure Django ORM Filter for Prompt Multidimensional Search.
Supports Name icontains, Category/Category-Slug/Legacy Task filtering, and Tags AND matching.
"""

from typing import Any

from django.db import connection
from django.db.models import Q, QuerySet

from apps.server.prompts.models import Prompt


class PromptFilter:
    """
    Multidimensional Filter for Prompt queryset.
    """

    @staticmethod
    def filter_queryset(queryset: QuerySet[Prompt], query_params: Any) -> QuerySet[Prompt]:
        """
        Apply multidimensional filters to the Prompt queryset.
        """
        name = query_params.get("name")
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Filter by Category ID
        category_id = query_params.get("category")
        if category_id:
            if str(category_id).isdigit():
                queryset = queryset.filter(category_id=int(category_id))

        # Filter by Category Slug
        category_slug = query_params.get("category_slug")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # Backward compatibility for legacy 'task' query param
        task = query_params.get("task")
        if task:
            if str(task).isdigit():
                queryset = queryset.filter(category_id=int(task))
            else:
                queryset = queryset.filter(
                    Q(category__slug=task) | Q(category__name__icontains=task)
                )

        # Handle multiple tag parameters and comma-separated tags
        raw_tags = query_params.getlist("tags")
        parsed_tags: list[str] = []
        for item in raw_tags:
            for tag in item.split(","):
                cleaned = tag.strip()
                if cleaned:
                    parsed_tags.append(cleaned)

        for tag in parsed_tags:
            if connection.vendor == "sqlite":
                queryset = queryset.filter(tags__icontains=f'"{tag}"')
            else:
                queryset = queryset.filter(tags__contains=[tag])

        return queryset
