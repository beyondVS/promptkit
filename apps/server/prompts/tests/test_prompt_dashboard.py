"""
Tests for Prompt Dashboard CUD, initial empty draft creation, category move, and deletion guards.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Version
from apps.server.prompts.services.lifecycle import set_on_live_version


class PromptDashboardTests(TestCase):
    staff_user: User
    category: PromptCategory

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(
            username="staff_admin", password="password123"
        )
        self.client.login(username="staff_admin", password="password123")
        self.category, _ = PromptCategory.objects.get_or_create(
            name="General Dash", slug="general-dash"
        )

    def test_create_prompt_with_initial_empty_draft(self) -> None:
        res = self.client.post(
            reverse("dashboard-prompt-create"),
            {
                "name": "Dashboard Prompt",
                "slug": "dash-prompt",
                "category_id": self.category.id,
                "description": "Created via dashboard",
            },
        )
        self.assertEqual(res.status_code, 302)
        prompt = Prompt.objects.get(slug="dash-prompt")
        self.assertEqual(prompt.versions.count(), 1)
        v1 = prompt.versions.first()
        self.assertIsNotNone(v1)
        if v1:
            self.assertEqual(v1.status, Version.Status.DRAFT)
            self.assertFalse(v1.is_on_live)

    def test_update_prompt_metadata_and_category_move(self) -> None:
        cat2 = PromptCategory.objects.create(name="Support Dash", slug="support-dash")
        prompt = Prompt.objects.create(
            name="Original Name", slug="orig-slug", category=self.category
        )
        res = self.client.post(
            reverse("dashboard-prompt-update", kwargs={"pk": prompt.pk}),
            {
                "name": "Updated Name",
                "category_id": cat2.id,
                "description": "Updated desc",
            },
        )
        self.assertEqual(res.status_code, 302)
        prompt.refresh_from_db()
        self.assertEqual(prompt.name, "Updated Name")
        self.assertEqual(prompt.category, cat2)

    def test_delete_prompt_guarded_when_on_live(self) -> None:
        prompt = Prompt.objects.create(
            name="Live Prompt", slug="live-prompt", category=self.category
        )
        Version.objects.create(prompt=prompt, version_number=1, status=Version.Status.PUBLISHED)
        set_on_live_version(prompt, 1)

        res = self.client.post(reverse("dashboard-prompt-delete", kwargs={"pk": prompt.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Prompt.objects.filter(pk=prompt.pk).exists())
