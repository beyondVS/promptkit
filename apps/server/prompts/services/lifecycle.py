"""
Transactional lifecycle operations for Prompt, Version, Label, VariableDefinition, and Section.
"""

from django.db import transaction
from django.db.models import Max

from apps.server.prompts.models import (
    Label,
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)
from apps.server.prompts.services.templates import (
    validate_variable_default_value,
    validate_version_template_references,
)


class StaleRevisionError(Exception):
    """Raised when an operation attempts to modify a version with an outdated revision."""

    pass


def create_prompt_with_initial_draft(
    category: PromptCategory,
    name: str,
    slug: str,
    description: str = "",
    tags: list[str] | None = None,
) -> tuple[Prompt, Version]:
    """
    Create a new Prompt and its initial empty draft Version (v1) within an atomic transaction.
    """
    with transaction.atomic():
        prompt = Prompt.objects.create(
            category=category,
            name=name,
            slug=slug,
            description=description,
            tags=tags or [],
        )
        initial_version = Version.objects.create(
            prompt=prompt,
            version_number=1,
            status=Version.Status.DRAFT,
            is_on_live=False,
            template_text="",
            changelog="Initial draft version",
            revision=1,
        )
        return prompt, initial_version


def delete_prompt(prompt: Prompt) -> None:
    """
    Safely delete a prompt only if it has no active on-live version.
    """
    with transaction.atomic():
        if Version.objects.filter(prompt=prompt, is_on_live=True).exists():
            raise ValueError("Cannot delete prompt with an active on-live version.")
        prompt.delete()


def publish_version(version_id: int, expected_revision: int | None = None) -> Version:
    """
    Publish a draft version immutably, validating references and updating system labels.
    """
    with transaction.atomic():
        version = Version.objects.select_for_update().get(id=version_id)

        if expected_revision is not None and version.revision != expected_revision:
            raise StaleRevisionError(
                f"Version revision mismatch: expected {expected_revision}, got {version.revision}."
            )

        if version.status == Version.Status.PUBLISHED:
            return version

        # Validate template contents & variables
        sections = list(version.sections.all().order_by("order"))
        section_contents = [s.content for s in sections]
        declared_vars = set(version.variables.values_list("name", flat=True))

        valid, errors = validate_version_template_references(section_contents, declared_vars)
        if not valid:
            raise ValueError(f"Template validation failed: {'; '.join(errors)}")

        for var in version.variables.all():
            val_ok, val_err = validate_variable_default_value(var.var_type, var.default_value)
            if not val_ok:
                raise ValueError(f"Variable '{var.name}' invalid default value: {val_err}")

        version.status = Version.Status.PUBLISHED
        version.revision += 1
        version.save()

        # Update latest label
        Label.objects.update_or_create(
            prompt=version.prompt,
            name="latest",
            defaults={"version": version},
        )

        return version


def clone_version(source_version_id: int, expected_revision: int | None = None) -> Version:
    """
    Clone a draft or published version into a new independent draft version.
    """
    with transaction.atomic():
        source_version = Version.objects.select_for_update().get(id=source_version_id)

        if expected_revision is not None and source_version.revision != expected_revision:
            raise StaleRevisionError(
                f"Revision mismatch: expected {expected_revision}, got {source_version.revision}."
            )

        max_v = (
            Version.objects.filter(prompt=source_version.prompt).aggregate(Max("version_number"))[
                "version_number__max"
            ]
            or 0
        )
        new_version_number = max_v + 1

        new_version = Version.objects.create(
            prompt=source_version.prompt,
            version_number=new_version_number,
            status=Version.Status.DRAFT,
            is_on_live=False,
            template_text=source_version.template_text,
            changelog=f"Cloned from v{source_version.version_number}",
            revision=1,
        )

        # Deep copy sections
        for sec in source_version.sections.all().order_by("order"):
            Section.objects.create(
                version=new_version,
                role=sec.role,
                order=sec.order,
                content=sec.content,
            )

        # Deep copy variables
        for var in source_version.variables.all():
            VariableDefinition.objects.create(
                version=new_version,
                name=var.name,
                var_type=var.var_type,
                required=var.required,
                default_value=var.default_value,
                description=var.description,
            )

        return new_version


def delete_draft_version(version_id: int) -> None:
    """
    Delete a draft version. Published versions cannot be deleted.
    """
    with transaction.atomic():
        version = Version.objects.select_for_update().get(id=version_id)

        if version.status != Version.Status.DRAFT:
            raise ValueError("Cannot delete a published version.")

        if version.is_on_live:
            raise ValueError("Cannot delete an on-live version.")

        version.delete()


def set_on_live_version(prompt: Prompt, version_number: int) -> Version:
    """
    Set a published version as the single on-live version for a prompt.
    """
    with transaction.atomic():
        version = Version.objects.select_for_update().get(
            prompt=prompt, version_number=version_number
        )

        if version.status != Version.Status.PUBLISHED:
            raise ValueError("Only a published version can be set to on-live.")

        # Clear existing on-live versions for this prompt
        Version.objects.filter(prompt=prompt, is_on_live=True).update(is_on_live=False)

        version.is_on_live = True
        version.save(update_fields=["is_on_live"])
        return version


def clear_on_live_version(prompt: Prompt) -> None:
    """
    Clear the on-live status from all versions of a prompt.
    """
    with transaction.atomic():
        Version.objects.filter(prompt=prompt, is_on_live=True).update(is_on_live=False)


def set_custom_label(prompt: Prompt, name: str, version_number: int) -> Label:
    """
    Assign or move a custom label to point to a published version of a prompt.
    """
    if name.strip().lower() in ("production", "on-live"):
        raise ValueError(f"'{name}' is not a permitted custom label name.")

    if name == "latest":
        raise ValueError("'latest' is a system label managed automatically on publication.")

    with transaction.atomic():
        version = Version.objects.select_for_update().get(
            prompt=prompt, version_number=version_number
        )

        if version.status != Version.Status.PUBLISHED:
            raise ValueError("Custom labels can only point to published versions.")

        label, _ = Label.objects.update_or_create(
            prompt=prompt,
            name=name,
            defaults={"version": version},
        )
        return label


def remove_custom_label(prompt: Prompt, name: str) -> None:
    """
    Remove a custom label from a prompt.
    """
    if name == "latest":
        raise ValueError("System label 'latest' cannot be removed directly.")

    with transaction.atomic():
        Label.objects.filter(prompt=prompt, name=name).delete()
