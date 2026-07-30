"""
Unit tests for Prompt-PromptCategory relationship mapping and filtered search APIs.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory


class PromptCategoryRelationTestCase(TestCase):
    """
    Test suite for Prompt mandatory category assignment and category filtered search.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"
        self.cat_support = PromptCategory.objects.create(
            name="고객지원",
            slug="customer-support",
        )
        self.cat_codegen = PromptCategory.objects.create(
            name="코드생성",
            slug="code-gen",
        )

    def test_create_prompt_without_category_fails(self) -> None:
        """Test creating a prompt without mandatory category raises 400 Bad Request."""
        payload = {
            "slug": "no-cat-prompt",
            "name": "카테고리 없는 프롬프트",
            "description": "카테고리 누락 시도",
        }
        response = self.client.post("/api/v1/prompts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)

    def test_create_prompt_with_valid_category(self) -> None:
        """Test creating a prompt with valid category ID succeeds."""
        payload = {
            "slug": "valid-cat-prompt",
            "name": "정상 카테고리 프롬프트",
            "category": self.cat_support.id,
            "tags": ["v1"],
        }
        response = self.client.post("/api/v1/prompts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["category"], self.cat_support.id)
        self.assertEqual(response.data["category_detail"]["slug"], "customer-support")

    def test_filter_prompts_by_category_id(self) -> None:
        """Test filtering prompts by category ID parameter."""
        Prompt.objects.create(slug="p1", name="프롬프트 1", category=self.cat_support)
        Prompt.objects.create(slug="p2", name="프롬프트 2", category=self.cat_codegen)

        response = self.client.get(f"/api/v1/prompts/?category={self.cat_support.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "p1")

    def test_filter_prompts_by_category_slug(self) -> None:
        """Test filtering prompts by category_slug parameter."""
        Prompt.objects.create(slug="p1", name="프롬프트 1", category=self.cat_support)
        Prompt.objects.create(slug="p2", name="프롬프트 2", category=self.cat_codegen)

        response = self.client.get("/api/v1/prompts/?category_slug=code-gen")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "p2")

    def test_filter_prompts_by_legacy_task_parameter(self) -> None:
        """Test backward compatibility filter using legacy 'task' query parameter."""
        Prompt.objects.create(slug="p1", name="프롬프트 1", category=self.cat_support)
        Prompt.objects.create(slug="p2", name="프롬프트 2", category=self.cat_codegen)

        # Match by category slug
        res1 = self.client.get("/api/v1/prompts/?task=customer-support")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data), 1)
        self.assertEqual(res1.data[0]["slug"], "p1")

        # Match by category name substring
        res2 = self.client.get("/api/v1/prompts/?task=고객")
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data), 1)
        self.assertEqual(res2.data[0]["slug"], "p1")
