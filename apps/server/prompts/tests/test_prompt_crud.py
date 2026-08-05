"""
Tests for Prompt CUD operations via Staff Dashboard.
Retires obsolete REST-CUD endpoints per T061 and architecture rules.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft


class PromptCRUDTestCase(TestCase):
    staff_user: User
    category: PromptCategory

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_crud", password="password")
        self.client.login(username="admin_crud", password="password")
        self.category = PromptCategory.objects.create(name="Support", slug="support")

    def test_create_prompt_via_dashboard(self) -> None:
        res = self.client.post(
            reverse("dashboard-prompt-create"),
            {
                "name": "Customer Support Greeting",
                "slug": "customer-support-v1",
                "category_id": self.category.id,
                "description": "Greeting prompt",
            },
        )
        self.assertEqual(res.status_code, 302)
        prompt = Prompt.objects.get(slug="customer-support-v1")
        self.assertEqual(prompt.name, "Customer Support Greeting")
        self.assertEqual(prompt.category, self.category)

    def test_update_and_delete_prompt_via_dashboard(self) -> None:
        prompt, _ = create_prompt_with_initial_draft(
            category=self.category, name="Pre-Update", slug="pre-update"
        )
        res_upd = self.client.post(
            reverse("dashboard-prompt-update", kwargs={"pk": prompt.pk}),
            {"name": "Post-Update", "category_id": self.category.id, "description": "Updated"},
        )
        self.assertEqual(res_upd.status_code, 302)
        prompt.refresh_from_db()
        self.assertEqual(prompt.name, "Post-Update")

        res_del = self.client.post(reverse("dashboard-prompt-delete", kwargs={"pk": prompt.pk}))
        self.assertEqual(res_del.status_code, 302)
        self.assertFalse(Prompt.objects.filter(pk=prompt.pk).exists())
