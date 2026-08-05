"""
Routing and method/auth boundary regression tests.
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status

from apps.server.prompts.models import Prompt, PromptCategory
from apps.server.prompts.services.lifecycle import (
    create_prompt_with_initial_draft,
    publish_version,
    set_on_live_version,
)


class RoutingContractTests(TestCase):
    category: PromptCategory
    prompt: Prompt

    def setUp(self) -> None:
        self.category, _ = PromptCategory.objects.get_or_create(
            name="Routing Test", slug="routing-test"
        )
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=self.category,
            name="Routing Prompt",
            slug="routing-prompt",
        )
        pub = publish_version(self.v1.id)
        set_on_live_version(self.prompt, pub.version_number)
        self.api_key = settings.PROMPTKIT_API_KEY

    def test_sdk_api_key_authentication(self) -> None:
        # Without API Key -> 401
        res = self.client.get(f"/api/v1/prompts/{self.prompt.slug}/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # With API Key -> 200
        res = self.client.get(
            f"/api/v1/prompts/{self.prompt.slug}/",
            HTTP_X_PROMPTKIT_API_KEY=self.api_key,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_sdk_api_method_disallowed(self) -> None:
        # POST/PUT/DELETE to SDK route -> 405
        res = self.client.post(
            f"/api/v1/prompts/{self.prompt.slug}/",
            HTTP_X_PROMPTKIT_API_KEY=self.api_key,
        )
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_dashboard_unauthenticated_redirection(self) -> None:
        res = self.client.get("/dashboard/")
        self.assertEqual(res.status_code, status.HTTP_302_FOUND)
        self.assertIn("/dashboard/login/", res.url)

    def test_dashboard_non_staff_rejection(self) -> None:
        User.objects.create_user(username="regular", password="password")
        self.client.login(username="regular", password="password")
        res = self.client.get("/dashboard/")
        self.assertIn(res.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_302_FOUND])
