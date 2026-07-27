"""
Django Admin registration for prompts app models.
"""

from django.contrib import admin

from apps.server.prompts.models import (
    Label,
    Prompt,
    Section,
    VariableDefinition,
    Version,
)


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "created_at", "updated_at")
    search_fields = ("slug", "name", "description")
    ordering = ("-updated_at",)


@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ("prompt", "version_number", "created_at")
    list_filter = ("prompt",)
    search_fields = ("prompt__slug", "prompt__name", "template_text", "changelog")
    ordering = ("prompt", "-version_number")


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("prompt", "name", "version", "updated_at")
    list_filter = ("name", "prompt")
    search_fields = ("prompt__slug", "name", "version__version_number")


@admin.register(VariableDefinition)
class VariableDefinitionAdmin(admin.ModelAdmin):
    list_display = ("version", "name", "var_type", "required", "default_value")
    list_filter = ("var_type", "required")
    search_fields = ("version__prompt__slug", "name", "description")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("version", "order", "role")
    list_filter = ("role",)
    search_fields = ("version__prompt__slug", "content")
    ordering = ("version", "order")
