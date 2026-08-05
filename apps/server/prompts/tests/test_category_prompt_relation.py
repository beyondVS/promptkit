"""
Tests for Category and Prompt relationship constraints and filtering (US4).
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from apps.server.prompts.models import PromptCategory
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft


class PromptCategoryRelationTestCase(TestCase):
    cat_support: PromptCategory
    cat_codegen: PromptCategory

    def setUp(self) -> None:
        self.cat_support = PromptCategory.objects.create(name="Support", slug="customer-support")
        self.cat_codegen = PromptCategory.objects.create(name="CodeGen", slug="code-gen")

    def test_category_scoped_prompt_name_uniqueness(self) -> None:
        # Same prompt name in different categories is allowed
        create_prompt_with_initial_draft(
            category=self.cat_support, name="Greeting", slug="support-greeting"
        )
        p2, _ = create_prompt_with_initial_draft(
            category=self.cat_codegen, name="Greeting", slug="codegen-greeting"
        )
        self.assertIsNotNone(p2.id)

        # Same prompt name in same category raises IntegrityError
        with self.assertRaises(IntegrityError):
            create_prompt_with_initial_draft(
                category=self.cat_support, name="Greeting", slug="support-greeting-2"
            )

    def test_dashboard_prompt_list_category_filter(self) -> None:
        self.staff_user = User.objects.create_superuser(
            username="admin_catfilter", password="password"
        )
        self.client.login(username="admin_catfilter", password="password")

        create_prompt_with_initial_draft(category=self.cat_support, name="P1", slug="p1")
        create_prompt_with_initial_draft(category=self.cat_codegen, name="P2", slug="p2")

        res = self.client.get("/dashboard/?category=code-gen")
        self.assertEqual(res.status_code, 200)
        prompts = res.context["prompts"]
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0].slug, "p2")
