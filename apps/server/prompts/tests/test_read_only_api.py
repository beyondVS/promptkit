"""
Tests for SDK Read-only Prompt Fetch API and X-PromptKit-Api-Key Header Authentication.
Strictly follows contract specification (contracts/sdk-read-api.md).
"""

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import (
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
)
from apps.server.prompts.services.lifecycle import (
    create_prompt_with_initial_draft,
    publish_version,
    set_custom_label,
    set_on_live_version,
)


class SDKReadOnlyAPITestCase(TestCase):
    prompt: Prompt

    def setUp(self) -> None:
        self.category, _ = PromptCategory.objects.get_or_create(
            slug="general",
            defaults={"name": "General", "description": "General prompts"},
        )
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=self.category,
            name="Greeting Prompt",
            slug="greeting-prompt",
        )
        Section.objects.create(
            version=self.v1, role="user", order=0, content="Hello {{ user_name }}!"
        )
        VariableDefinition.objects.create(version=self.v1, name="user_name", var_type="string")
        self.pub_v1 = publish_version(self.v1.id)
        self.valid_api_key = settings.PROMPTKIT_API_KEY

    def test_omitted_label_with_no_on_live_version_returns_404_no_deployable_version(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})
        res = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key)
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertEqual(data["error"], "no_deployable_version")

    def test_omitted_label_returns_on_live_version(self) -> None:
        set_on_live_version(self.prompt, self.pub_v1.version_number)
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})
        res = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["slug"], "greeting-prompt")
        self.assertEqual(data["version"], 1)
        self.assertIsNone(data["label"])

    def test_explicit_label_latest(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"}) + "?label=latest"
        res = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["version"], 1)
        self.assertEqual(data["label"], "latest")

    def test_explicit_custom_label(self) -> None:
        set_custom_label(self.prompt, "staging", self.pub_v1.version_number)
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"}) + "?label=staging"
        res = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["label"], "staging")

    def test_production_label_rejected(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"}) + "?label=production"
        res = self.client.get(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key)
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertEqual(data["error"], "invalid_label")

    def test_sdk_fetch_unauthorized_with_missing_or_invalid_header(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})
        self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(
            self.client.get(url, HTTP_X_PROMPTKIT_API_KEY="invalid-key").status_code, 401
        )

    def test_sdk_disallowed_cud_methods(self) -> None:
        url = reverse("sdk-prompt-fetch", kwargs={"slug": "greeting-prompt"})
        self.assertEqual(
            self.client.post(url, {}, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key).status_code, 405
        )
        self.assertEqual(
            self.client.delete(url, HTTP_X_PROMPTKIT_API_KEY=self.valid_api_key).status_code, 405
        )
