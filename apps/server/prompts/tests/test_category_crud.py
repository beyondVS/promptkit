"""
Unit tests for PromptCategory CRUD API endpoints and ON DELETE Restrict protection.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory


class PromptCategoryCRUDTestCase(TestCase):
    """
    Test suite for PromptCategory CRUD and prompt_count aggregation.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"

    def test_create_category_success(self) -> None:
        """Test creating a valid PromptCategory."""
        payload = {
            "name": "고객지원",
            "slug": "customer-support",
            "description": "고객 문의 응답용 범주",
        }
        response = self.client.post("/api/v1/categories/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "고객지원")
        self.assertEqual(response.data["slug"], "customer-support")
        self.assertTrue(PromptCategory.objects.filter(slug="customer-support").exists())

    def test_create_category_duplicate_name_or_slug_error(self) -> None:
        """Test creating a category with duplicate name or slug fails."""
        PromptCategory.objects.create(
            name="기존 범주",
            slug="existing-slug",
        )
        # Duplicate name
        payload1 = {"name": "기존 범주", "slug": "new-slug"}
        res1 = self.client.post("/api/v1/categories/", payload1, format="json")
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Duplicate slug
        payload2 = {"name": "새로운 범주", "slug": "existing-slug"}
        res2 = self.client.post("/api/v1/categories/", payload2, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_category_list_with_prompt_count(self) -> None:
        """Test category list endpoint returns prompt_count metadata."""
        cat1 = PromptCategory.objects.create(name="범주1", slug="cat1")
        cat2 = PromptCategory.objects.create(name="범주2", slug="cat2")

        # Create linked prompts for cat1
        Prompt.objects.create(slug="p1", name="프롬프트 1", category=cat1)
        Prompt.objects.create(slug="p2", name="프롬프트 2", category=cat1)

        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertGreaterEqual(len(data), 2)

        cat1_data = next(item for item in data if item["id"] == cat1.id)
        cat2_data = next(item for item in data if item["id"] == cat2.id)

        self.assertEqual(cat1_data["prompt_count"], 2)
        self.assertEqual(cat2_data["prompt_count"], 0)

    def test_update_category(self) -> None:
        """Test updating a PromptCategory."""
        cat = PromptCategory.objects.create(name="원래 이름", slug="orig-slug")
        payload = {"name": "변경 이름", "slug": "orig-slug", "description": "설명 변경"}
        response = self.client.put(f"/api/v1/categories/{cat.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "변경 이름")

    def test_delete_category_unlinked_success(self) -> None:
        """Test deleting an unlinked category succeeds."""
        cat = PromptCategory.objects.create(name="삭제 대상", slug="delete-me")
        response = self.client.delete(f"/api/v1/categories/{cat.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PromptCategory.objects.filter(pk=cat.id).exists())

    def test_delete_category_linked_conflict_error(self) -> None:
        """Test deleting a category with linked prompts returns 409 Conflict."""
        cat = PromptCategory.objects.create(name="보호 대상", slug="protected")
        Prompt.objects.create(slug="linked-prompt", name="연결된 프롬프트", category=cat)

        response = self.client.delete(f"/api/v1/categories/{cat.id}/")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(PromptCategory.objects.filter(pk=cat.id).exists())
