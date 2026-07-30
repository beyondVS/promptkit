"""
Django ORM Models for Prompt Registry.
Includes Prompt, Version, Label, VariableDefinition, and Section entities.
"""

from typing import ClassVar

from django.db import models
from django.utils import timezone


class PromptCategory(models.Model):
    """
    Normalized domain/task category entity for Prompt assets.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Human-readable category name",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="URL-friendly unique slug for API filtering",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed category description",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active status of the category",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class Prompt(models.Model):
    """
    Top-level container for a prompt asset in the registry.
    """

    slug = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Canonical string identifier (e.g. customer-support)",
    )
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Human-readable name for the prompt",
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of prompt purpose",
    )
    category = models.ForeignKey(
        PromptCategory,
        on_delete=models.RESTRICT,
        related_name="prompts",
        help_text="Mandatory domain category for the prompt asset",
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of tag keywords",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-updated_at"]

    def get_or_create_default_version(self) -> "Version":
        """Get or create default version (v1) for this prompt."""
        version, _ = self.versions.get_or_create(version_number=1)
        return version

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"


class Version(models.Model):
    """
    Immutable snapshot of a prompt template and configuration.
    """

    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()
    template_text = models.TextField(blank=True)
    changelog = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["prompt", "-version_number"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["prompt", "version_number"],
                name="unique_prompt_version_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.prompt.slug} v{self.version_number}"


class Label(models.Model):
    """
    Environment / release tag pointing to a specific Version of a Prompt.
    """

    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name="labels",
    )
    version = models.ForeignKey(
        Version,
        on_delete=models.CASCADE,
        related_name="labels",
    )
    name = models.CharField(
        max_length=50,
        help_text="Tag identifier (e.g. production, draft, dev)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["prompt", "name"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["prompt", "name"],
                name="unique_label_per_prompt",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.prompt.slug}:{self.name} -> v{self.version.version_number}"


class VariableDefinition(models.Model):
    """
    Dynamic parameter placeholder specification for a Version.
    """

    class VarType(models.TextChoices):
        STRING = "string", "String"
        INTEGER = "integer", "Integer"
        FLOAT = "float", "Float"
        BOOLEAN = "boolean", "Boolean"
        JSON = "json", "JSON"

    version = models.ForeignKey(
        Version,
        on_delete=models.CASCADE,
        related_name="variables",
    )
    name = models.CharField(max_length=100)
    var_type = models.CharField(
        max_length=20,
        choices=VarType.choices,
        default=VarType.STRING,
    )
    required = models.BooleanField(default=True)
    default_value = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["version", "name"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["version", "name"],
                name="unique_variable_per_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.version} - ${self.name} ({self.var_type})"


class Section(models.Model):
    """
    Modular message segment within a Version.
    """

    class Role(models.TextChoices):
        SYSTEM = "system", "System"
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        TOOL = "tool", "Tool"

    version = models.ForeignKey(
        Version,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    order = models.PositiveIntegerField(default=0)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["version", "order"]
        constraints: ClassVar[list[models.BaseConstraint]] = [
            models.UniqueConstraint(
                fields=["version", "order"],
                name="unique_section_order_per_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.version} - Section {self.order} ({self.role})"
