"""
Unit tests for Prompt search result ordering.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory


class PromptOrderingTestCase(TestCase):
    """
    Test suite for Prompt ordering API query parameter.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"
        self.category = PromptCategory.objects.create(name="support", slug="support")

        # Create test prompts
        self.p1 = Prompt.objects.create(
            slug="alpha",
            name="Alpha Prompt",
            category=self.category,
        )
        self.p2 = Prompt.objects.create(
            slug="beta",
            name="Beta Prompt",
            category=self.category,
        )
        self.p3 = Prompt.objects.create(
            slug="gamma",
            name="Gamma Prompt",
            category=self.category,
        )

    def test_ordering_by_name_asc(self) -> None:
        """Test ordering by name ascending."""
        response = self.client.get("/api/v1/prompts/?ordering=name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["Alpha Prompt", "Beta Prompt", "Gamma Prompt"])

    def test_ordering_by_name_desc(self) -> None:
        """Test ordering by name descending."""
        response = self.client.get("/api/v1/prompts/?ordering=-name")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data]
        self.assertEqual(names, ["Gamma Prompt", "Beta Prompt", "Alpha Prompt"])
