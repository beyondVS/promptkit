"""
Tests for Dashboard Session Auth and Prompt CUD views.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Label, Prompt, PromptCategory


class DashboardTestCase(TestCase):
    def setUp(self) -> None:
        self.category, _ = PromptCategory.objects.get_or_create(
            slug="general",
            defaults={"name": "General", "description": "General prompts"},
        )
        # Admin Staff User
        self.staff_user = User.objects.create_user(
            username="adminuser",
            password="adminpassword123",
            email="admin@example.com",
            is_staff=True,
        )
        # Normal User
        self.normal_user = User.objects.create_user(
            username="normaluser",
            password="normalpassword123",
            email="normal@example.com",
        )

    def test_dashboard_login_success(self) -> None:
        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "adminuser", "password": "adminpassword123"},
        )
        self.assertRedirects(response, reverse("dashboard-prompt-list"))
        self.assertTrue("_auth_user_id" in self.client.session)

    def test_dashboard_login_requires_staff(self) -> None:
        response = self.client.post(
            reverse("dashboard-login"),
            {"username": "normaluser", "password": "normalpassword123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only staff members can access the dashboard")

    def test_dashboard_prompt_list_requires_authentication(self) -> None:
        response = self.client.get(reverse("dashboard-prompt-list"))
        self.assertRedirects(response, reverse("dashboard-login"))

    def test_prompt_crud_flow_in_dashboard(self) -> None:
        self.client.login(username="adminuser", password="adminpassword123")

        # 1. Create Prompt
        create_response = self.client.post(
            reverse("dashboard-prompt-create"),
            {
                "name": "Customer Greeting",
                "slug": "customer-greeting",
                "category_id": self.category.id,
                "description": "Greeting prompt",
                "template_text": "Hello {name}!",
            },
        )
        self.assertRedirects(create_response, reverse("dashboard-prompt-list"))
        self.assertTrue(Prompt.objects.filter(slug="customer-greeting").exists())

        prompt = Prompt.objects.get(slug="customer-greeting")
        self.assertEqual(prompt.versions.count(), 1)
        self.assertTrue(Label.objects.filter(prompt=prompt, name="production").exists())

        # 2. Update Prompt & Add New Version
        update_response = self.client.post(
            reverse("dashboard-prompt-update", kwargs={"pk": prompt.pk}),
            {
                "name": "Customer Greeting Updated",
                "category_id": self.category.id,
                "description": "Updated description",
                "template_text": "Hello {name}, welcome to our service!",
                "create_new_version": "true",
            },
        )
        self.assertRedirects(update_response, reverse("dashboard-prompt-list"))
        prompt.refresh_from_db()
        self.assertEqual(prompt.name, "Customer Greeting Updated")
        self.assertEqual(prompt.versions.count(), 2)
        prod_label = Label.objects.get(prompt=prompt, name="production")
        self.assertEqual(prod_label.version.version_number, 2)

        # 3. Delete Prompt
        delete_response = self.client.post(
            reverse("dashboard-prompt-delete", kwargs={"pk": prompt.pk}),
        )
        self.assertRedirects(delete_response, reverse("dashboard-prompt-list"))
        self.assertFalse(Prompt.objects.filter(pk=prompt.pk).exists())
