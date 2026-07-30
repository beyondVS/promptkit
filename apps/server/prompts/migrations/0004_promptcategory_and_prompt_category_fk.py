# Generated migration for PromptCategory and Prompt.category FK

from typing import Any

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def migrate_task_to_category(apps: Any, schema_editor: Any) -> None:
    PromptCategory = apps.get_model("prompts", "PromptCategory")
    Prompt = apps.get_model("prompts", "Prompt")

    default_category, _ = PromptCategory.objects.get_or_create(
        slug="general",
        defaults={
            "name": "General",
            "description": "Default category for unclassified prompts",
        },
    )

    for prompt in Prompt.objects.all():
        task_str = getattr(prompt, "task", "").strip()
        if task_str:
            slug_val = slugify(task_str) or "general"
            name_val = task_str.title()
            cat, _ = PromptCategory.objects.get_or_create(
                slug=slug_val,
                defaults={"name": name_val, "description": f"{name_val} category"},
            )
            prompt.category = cat
        else:
            prompt.category = default_category
        prompt.save()


class Migration(migrations.Migration):

    dependencies = [
        ("prompts", "0003_section_created_at_section_updated_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromptCategory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="Human-readable category name",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="URL-friendly unique slug for API filtering",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text="Detailed category description",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        db_index=True,
                        default=True,
                        help_text="Active status of the category",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="prompt",
            name="category",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="prompts",
                to="prompts.promptcategory",
                help_text="Mandatory domain category for the prompt asset",
            ),
        ),
        migrations.RunPython(migrate_task_to_category, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="prompt",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="prompts",
                to="prompts.promptcategory",
                help_text="Mandatory domain category for the prompt asset",
            ),
        ),
        migrations.RemoveField(
            model_name="prompt",
            name="task",
        ),
    ]
