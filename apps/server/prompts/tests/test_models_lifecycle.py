"""
Tests for Prompt Registry lifecycle models, constraints, and data migrations.
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.server.prompts.models import (
    Label,
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)


class LifecycleModelTests(TestCase):
    category: PromptCategory
    prompt: Prompt

    def setUp(self) -> None:
        self.category, _ = PromptCategory.objects.get_or_create(
            name="General Life", slug="general-lifecycle"
        )
        self.prompt = Prompt.objects.create(
            name="Test Prompt", slug="test-prompt-lifecycle", category=self.category
        )

    def test_prompt_category_scoped_name_uniqueness(self) -> None:
        category2 = PromptCategory.objects.create(name="Other Life", slug="other-lifecycle")
        # Same name in different category should succeed
        p2 = Prompt.objects.create(name="Test Prompt", slug="test-prompt-2", category=category2)
        self.assertIsNotNone(p2.id)

        # Duplicate name in same category should fail
        with self.assertRaises(IntegrityError):
            Prompt.objects.create(name="Test Prompt", slug="test-prompt-3", category=self.category)

    def test_version_status_default_and_choices(self) -> None:
        v = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Hello",
        )
        self.assertEqual(v.status, Version.Status.DRAFT)
        self.assertFalse(v.is_on_live)

    def test_on_live_must_be_published_constraint(self) -> None:
        with self.assertRaises(IntegrityError):
            Version.objects.create(
                prompt=self.prompt,
                version_number=1,
                status=Version.Status.DRAFT,
                is_on_live=True,
            )

    def test_unique_on_live_version_per_prompt_constraint(self) -> None:
        v1 = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            status=Version.Status.PUBLISHED,
            is_on_live=True,
        )
        self.assertTrue(v1.is_on_live)

        with self.assertRaises(IntegrityError):
            Version.objects.create(
                prompt=self.prompt,
                version_number=2,
                status=Version.Status.PUBLISHED,
                is_on_live=True,
            )

    def test_prohibit_production_label_constraint(self) -> None:
        v1 = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            status=Version.Status.PUBLISHED,
        )
        with self.assertRaises(IntegrityError):
            Label.objects.create(
                prompt=self.prompt,
                version=v1,
                name="production",
            )

    def test_variable_type_choices(self) -> None:
        v1 = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
        )
        var = VariableDefinition.objects.create(
            version=v1,
            name="count",
            var_type=VariableDefinition.VarType.NUMBER,
        )
        self.assertEqual(var.var_type, "number")

    def test_section_role_choices(self) -> None:
        v1 = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
        )
        sec = Section.objects.create(
            version=v1,
            role=Section.Role.SYSTEM,
            order=0,
            content="System instruction",
        )
        self.assertEqual(sec.role, "system")
