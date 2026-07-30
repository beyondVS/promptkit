"""
Unit tests for Multidimensional Search API endpoint.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory


class MultidimensionalSearchTestCase(TestCase):
    """
    Test suite for Prompt multidimensional search API.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"

        self.cat_support = PromptCategory.objects.create(
            name="customer-support",
            slug="customer-support",
        )
        self.cat_codegen = PromptCategory.objects.create(
            name="code-gen",
            slug="code-gen",
        )

        # Create sample prompt data
        self.p1 = Prompt.objects.create(
            slug="p1",
            name="고객 상담 가이드라인",
            category=self.cat_support,
            tags=["v1", "support", "kr"],
        )
        self.p2 = Prompt.objects.create(
            slug="p2",
            name="코드 생성 도우미",
            category=self.cat_codegen,
            tags=["v1", "dev"],
        )
        self.p3 = Prompt.objects.create(
            slug="p3",
            name="고객 환불 처리 안내",
            category=self.cat_support,
            tags=["v2", "support", "refund"],
        )

    def test_search_by_name_icontains(self) -> None:
        """Test search by name partial match."""
        response = self.client.get("/api/v1/prompts/?name=고객")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data]
        self.assertIn("고객 상담 가이드라인", names)
        self.assertIn("고객 환불 처리 안내", names)
        self.assertNotIn("코드 생성 도우미", names)

    def test_search_by_task(self) -> None:
        """Test search by task category exact match."""
        response = self.client.get("/api/v1/prompts/?task=customer-support")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        res_code = self.client.get("/api/v1/prompts/?task=code-gen")
        self.assertEqual(len(res_code.data), 1)
        self.assertEqual(res_code.data[0]["name"], "코드 생성 도우미")

    def test_search_by_multiple_tags_and_matching(self) -> None:
        """Test search with multiple tags requiring AND matching."""
        # Search for tags v1 AND support (only p1 has both)
        response = self.client.get("/api/v1/prompts/?tags=v1&tags=support")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "고객 상담 가이드라인")

    def test_comma_separated_tags_search(self) -> None:
        """Test search with comma-separated tags string parameter."""
        response = self.client.get("/api/v1/prompts/?tags=v1,support")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "고객 상담 가이드라인")

    def test_multidimensional_combination_search(self) -> None:
        """Test search combining Name, Task, and Tags conditions simultaneously."""
        response = self.client.get("/api/v1/prompts/?name=고객&task=customer-support&tags=refund")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "고객 환불 처리 안내")

    def test_search_no_results(self) -> None:
        """Test search returning empty list when no matches exist."""
        response = self.client.get("/api/v1/prompts/?name=존재하지않음")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
