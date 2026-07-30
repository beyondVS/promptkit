"""
Django REST Framework Serializers for Prompt & Section Registry.
"""

from typing import Any

from rest_framework import serializers

from apps.server.prompts.models import Prompt, PromptCategory, Section, Version


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


class VersionSerializer(serializers.ModelSerializer):
    """
    Serializer for immutable Version snapshot entity.
    """

    class Meta:
        model = Version
        fields = [
            "id",
            "prompt",
            "version_number",
            "template_text",
            "changelog",
            "created_at",
        ]
        read_only_fields = ["id", "prompt", "version_number", "created_at"]


class RollbackRequestSerializer(serializers.Serializer):
    """
    Serializer for rollback action request payload.
    """

    target_version = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text="Target version number to roll back to",
    )
    changelog = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="Optional description for the rollback action",
    )


class DiffLineItemSerializer(serializers.Serializer):
    """
    Serializer for an individual line diff item.
    """

    line = serializers.IntegerField()
    op = serializers.ChoiceField(choices=["equal", "added", "deleted"])
    text = serializers.CharField(allow_blank=True)


class VersionDiffResponseSerializer(serializers.Serializer):
    """
    Serializer for structured line diff response payload.
    """

    prompt_id = serializers.IntegerField()
    from_version = serializers.IntegerField()
    to_version = serializers.IntegerField()
    diff = DiffLineItemSerializer(many=True)


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
    Serializer for Prompt summary list and creation/update.
    Supports optional template_text and changelog for automatic Version snapshot management.
    """

    category_detail = PromptCategorySerializer(source="category", read_only=True)
    template_text = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Template text for prompt version snapshot",
    )
    changelog = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Optional changelog note for new version snapshot",
    )

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
            "template_text",
            "changelog",
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

    def create(self, validated_data: dict[str, Any]) -> Prompt:
        """
        Create Prompt and initial Version (v1) snapshot.
        """
        template_text = validated_data.pop("template_text", "")
        changelog = validated_data.pop("changelog", "Initial version created")
        prompt = Prompt.objects.create(**validated_data)
        Version.objects.create(
            prompt=prompt,
            version_number=1,
            template_text=template_text,
            changelog=changelog or "Initial version created",
        )
        return prompt

    def update(self, instance: Prompt, validated_data: dict[str, Any]) -> Prompt:
        """
        Update Prompt fields and create new Version if template_text has changed.
        Implements 'Skip Creation' policy if template_text is identical to latest version.
        """
        has_template_text = "template_text" in validated_data
        template_text = validated_data.pop("template_text", "")
        changelog = validated_data.pop("changelog", "")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if has_template_text:
            latest_version = instance.versions.order_by("-version_number").first()
            if latest_version and latest_version.template_text == template_text:
                # Skip Creation: template text is identical to current latest version
                pass
            else:
                next_version_number = (latest_version.version_number + 1) if latest_version else 1
                Version.objects.create(
                    prompt=instance,
                    version_number=next_version_number,
                    template_text=template_text,
                    changelog=changelog or f"Version {next_version_number} updated",
                )

        return instance


class PromptDetailSerializer(PromptSerializer):
    """
    Detailed Serializer for Prompt including latest version snapshot and nested Sections.
    """

    sections = serializers.SerializerMethodField()
    latest_version = serializers.SerializerMethodField()

    class Meta(PromptSerializer.Meta):
        fields = PromptSerializer.Meta.fields + ["latest_version", "sections"]

    def get_latest_version(self, obj: Prompt) -> dict[str, Any] | None:
        """
        Retrieve the latest version snapshot metadata.
        """
        latest = obj.versions.order_by("-version_number").first()
        if not latest:
            return None
        return VersionSerializer(latest).data

    def get_sections(self, obj: Prompt) -> list[dict[str, Any]]:
        """
        Retrieve sections from the default version (v1) of the prompt.
        """
        version = obj.versions.filter(version_number=1).first()
        if not version:
            return []
        return SectionSerializer(version.sections.all(), many=True).data
