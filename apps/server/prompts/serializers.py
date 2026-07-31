"""
DRF Serializer for SDK Read-only Prompt Fetch API responses.
Strictly follows contract specification (contracts/sdk-server-api.md).
"""

from typing import Any

from rest_framework import serializers


class SDKPromptFetchResponseSerializer(serializers.Serializer):
    """
    Read-only Serializer for SDK Prompt Fetch API responses.
    """

    slug = serializers.CharField()
    name = serializers.CharField()
    category = serializers.SerializerMethodField()
    version = serializers.IntegerField(source="version_number")
    label = serializers.CharField()
    template_text = serializers.CharField()
    variables = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField()

    def get_category(self, obj: dict[str, Any]) -> dict[str, str]:
        cat = obj["prompt"].category
        return {"name": cat.name, "slug": cat.slug}

    def get_variables(self, obj: dict[str, Any]) -> list[dict[str, Any]]:
        version = obj["version"]
        return [
            {
                "name": v.name,
                "var_type": v.var_type,
                "required": v.required,
                "default_value": v.default_value,
                "description": v.description,
            }
            for v in version.variables.all()
        ]

    def get_sections(self, obj: dict[str, Any]) -> list[dict[str, Any]]:
        version = obj["version"]
        return [
            {
                "role": s.role,
                "order": s.order,
                "content": s.content,
            }
            for s in version.sections.all()
        ]
