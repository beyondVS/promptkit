# Generated manually for T009: Prompt Dashboard Lifecycle Migration

from typing import Any
from django.db import migrations, models


def migrate_existing_prompt_data(apps: Any, schema_editor: Any) -> None:
    Prompt = apps.get_model("prompts", "Prompt")
    Version = apps.get_model("prompts", "Version")
    Label = apps.get_model("prompts", "Label")
    VariableDefinition = apps.get_model("prompts", "VariableDefinition")
    Section = apps.get_model("prompts", "Section")

    # 1. Transform VariableDefinition types: integer/float -> number
    for var_def in VariableDefinition.objects.all():
        if var_def.var_type in ["integer", "float"]:
            var_def.var_type = "number"
            var_def.save(update_fields=["var_type"])

    # 2. Transform Section roles: unsupported roles check
    for section in Section.objects.all():
        if section.role not in ["system", "user", "assistant"]:
            section.role = "user"
            section.save(update_fields=["role"])

    # 3. Classify versions & process labels
    Version.objects.all().update(status="published")

    # Handle production labels -> set on-live version and remove production label
    production_labels = Label.objects.filter(name="production")
    for label in production_labels:
        version = label.version
        version.status = "published"
        version.is_on_live = True
        version.save(update_fields=["status", "is_on_live"])

    # Delete all 'production' labels as they are prohibited
    production_labels.delete()


def rollback_existing_prompt_data(apps: Any, schema_editor: Any) -> None:
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("prompts", "0004_promptcategory_and_prompt_category_fk"),
    ]

    operations = [
        migrations.AlterField(
            model_name="prompt",
            name="name",
            field=models.CharField(
                help_text="Human-readable name for the prompt", max_length=255
            ),
        ),
        migrations.AddField(
            model_name="version",
            name="is_on_live",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Single active deployment target per prompt",
            ),
        ),
        migrations.AddField(
            model_name="version",
            name="revision",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Monotonically increasing revision counter for optimistic concurrency",
            ),
        ),
        migrations.AddField(
            model_name="version",
            name="status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("published", "Published")],
                db_index=True,
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="version",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="variabledefinition",
            name="var_type",
            field=models.CharField(
                choices=[
                    ("string", "String"),
                    ("number", "Number"),
                    ("boolean", "Boolean"),
                    ("json", "JSON"),
                ],
                default="string",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="section",
            name="role",
            field=models.CharField(
                choices=[
                    ("system", "System"),
                    ("user", "User"),
                    ("assistant", "Assistant"),
                ],
                default="user",
                max_length=20,
            ),
        ),
        migrations.RunPython(
            migrate_existing_prompt_data, reverse_code=rollback_existing_prompt_data
        ),
        migrations.AddConstraint(
            model_name="prompt",
            constraint=models.UniqueConstraint(
                fields=("category", "name"), name="unique_prompt_name_per_category"
            ),
        ),
        migrations.AddConstraint(
            model_name="version",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_on_live", True)),
                fields=("prompt",),
                name="unique_on_live_version_per_prompt",
            ),
        ),
        migrations.AddConstraint(
            model_name="version",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("is_on_live", True), ("status", "draft"), _negated=True
                ),
                name="on_live_must_be_published",
            ),
        ),
        migrations.AddConstraint(
            model_name="label",
            constraint=models.CheckConstraint(
                condition=models.Q(("name", "production"), _negated=True),
                name="prohibit_production_label",
            ),
        ),
    ]
