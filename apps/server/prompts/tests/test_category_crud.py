"""
Unit tests for PromptCategory models, constraints, and REST API retirement.
"""

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.server.prompts.models import Prompt, PromptCategory


class PromptCategoryCRUDTestCase(TestCase):
    def test_create_category_success(self) -> None:
        cat = PromptCategory.objects.create(name="Support Cat", slug="support-cat")
        self.assertEqual(cat.name, "Support Cat")

    def test_create_category_duplicate_name_or_slug_error(self) -> None:
        PromptCategory.objects.create(name="Support Cat", slug="support-cat")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                PromptCategory.objects.create(name="Support Cat", slug="support-new")
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                PromptCategory.objects.create(name="Support New", slug="support-cat")

    def test_delete_category_linked_conflict_error(self) -> None:
        cat = PromptCategory.objects.create(name="Protected Cat", slug="protected-cat")
        Prompt.objects.create(slug="linked-prompt", name="Linked Prompt", category=cat)
        with self.assertRaises(Exception):
            cat.delete()
