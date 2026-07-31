"""
Tests for SDK Read-only Prompt Fetch API and X-PromptKit-Api-Key Header Authentication.
"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Label, Prompt, PromptCategory, Version


class SDKReadOnlyAPITestCase(TestCase):
    def setUp(self) -> None:
        self.category, _ = PromptCategory.objects.get_or_create(
            slug="general",
            defaults={"name": "General", "description": "General prompts"},
        )
        self.prompt = Prompt.objects.create(
            name="Greeting Prompt",
            slug="greeting-prompt",
            category=self.category,
            description="SDK fetch test prompt",
        )
        self.version = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Hello {user_name}!",
            changelog="Initial version",
        )
        self.label = Label.objects.create(
            prompt=self.prompt,
            version=self.version,
            name="production",
        )
        self.valid_api_key = settings.PROMPTKIT_API_KEY

    def test_sdk_fetch_success_with_valid_header(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})
        response = self.client.get(
            url,
            HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["slug"], "greeting-prompt")
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["label"], "production")
        self.assertEqual(data["template_text"], "Hello {user_name}!")
        self.assertEqual(data["category"]["slug"], "general")

    def test_sdk_fetch_unauthorized_with_missing_or_invalid_header(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})

        # 1. Missing header
        res1 = self.client.get(url)
        self.assertEqual(res1.status_code, 401)

        # 2. Invalid header
        res2 = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY="invalid-key")
        self.assertEqual(res2.status_code, 401)

    def test_sdk_fetch_not_found(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "non-existent-prompt"})
        response = self.client.get(
            url,
            HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key,
        )
        self.assertEqual(response.status_code, 404)

    def test_sdk_disallowed_cud_methods(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})

        # POST disallow
        res_post = self.client.post(
            url,
            {"name": "Attempt CUD"},
            HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key,
        )
        self.assertEqual(res_post.status_code, 405)

        # DELETE disallow
        res_delete = self.client.delete(
            url,
            HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key,
        )
        self.assertEqual(res_delete.status_code, 405)
