"""
Django REST Framework Serializers for Prompt & Section Registry.
"""

from typing import Any

from rest_framework import serializers

from apps.server.prompts.models import Prompt, PromptCategory, Section


class PromptCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for PromptCategory entity (includes prompt_count metadata).
    """

    prompt_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = PromptCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "prompt_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PromptCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating PromptCategory.
    """

    class Meta:
        model = PromptCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        """Validate category name uniqueness."""
        instance = getattr(self, "instance", None)
        query = PromptCategory.objects.filter(name=value)
        if instance is not None:
            query = query.exclude(pk=instance.pk)
        if query.exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return value

    def validate_slug(self, value: str) -> str:
        """Validate category slug uniqueness."""
        instance = getattr(self, "instance", None)
        query = PromptCategory.objects.filter(slug=value)
        if instance is not None:
            query = query.exclude(pk=instance.pk)
        if query.exists():
            raise serializers.ValidationError("A category with this slug already exists.")
        return value


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for Section entity.
    """

    class Meta:
        model = Section
        fields = [
            "id",
            "version",
            "role",
            "order",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SectionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating a Section attached to a Prompt.
    """

    class Meta:
        model = Section
        fields = [
            "id",
            "role",
            "order",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PromptSerializer(serializers.ModelSerializer):
    """
    Serializer for Prompt summary list and creation.
    """

    category_detail = PromptCategorySerializer(source="category", read_only=True)

    class Meta:
        model = Prompt
        fields = [
            "id",
            "slug",
            "name",
            "description",
            "category",
            "category_detail",
            "tags",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "category_detail", "created_at", "updated_at"]

    def validate_name(self, value: str) -> str:
        """
        Validate prompt name uniqueness on create and update.
        """
        instance = getattr(self, "instance", None)
        query = Prompt.objects.filter(name=value)
        if instance is not None:
            query = query.exclude(pk=instance.pk)
        if query.exists():
            raise serializers.ValidationError("A prompt with this name already exists.")
        return value

    def validate_tags(self, value: list[str]) -> list[str]:
        """
        Validate that tags is a list of strings.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list of strings.")
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Each tag item must be a string.")
        return value


class PromptDetailSerializer(PromptSerializer):
    """
    Detailed Serializer for Prompt including nested Sections from default Version.
    """

    sections = serializers.SerializerMethodField()

    class Meta(PromptSerializer.Meta):
        fields = PromptSerializer.Meta.fields + ["sections"]

    def get_sections(self, obj: Prompt) -> list[dict[str, Any]]:
        """
        Retrieve sections from the default version (v1) of the prompt.
        """
        version = obj.versions.filter(version_number=1).first()
        if not version:
            return []
        return SectionSerializer(version.sections.all(), many=True).data
