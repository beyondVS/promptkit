"""
Tests for category dashboard CUD and attached-prompt deletion protection (US4).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import PromptCategory
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft


class CategoryDashboardTests(TestCase):
    staff_user: User

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(
            username="admin_catdash", password="password"
        )
        self.client.login(username="admin_catdash", password="password")

    def test_category_crud_operations(self) -> None:
        # Create category
        res = self.client.post(
            reverse("dashboard-category-list"),
            {"name": "Billing", "slug": "billing", "description": "Billing prompts"},
        )
        self.assertEqual(res.status_code, 302)
        cat = PromptCategory.objects.get(slug="billing")
        self.assertEqual(cat.name, "Billing")

    def test_category_deletion_blocked_when_prompts_attached(self) -> None:
        cat = PromptCategory.objects.create(name="Support", slug="support")
        create_prompt_with_initial_draft(category=cat, name="Support P1", slug="support-p1")

        res = self.client.post(reverse("dashboard-category-delete", kwargs={"pk": cat.pk}))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(PromptCategory.objects.filter(pk=cat.pk).exists())
