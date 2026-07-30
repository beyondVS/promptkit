"""
Unit tests for Prompt and Section CRUD API endpoints.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory, Section


class PromptCRUDTestCase(TestCase):
    """
    Test suite for Prompt & Section CRUD endpoints.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"
        self.category = PromptCategory.objects.create(
            name="기본 카테고리",
            slug="default-cat",
        )

    def test_create_prompt_success(self) -> None:
        """Test creating a valid Prompt."""
        payload = {
            "slug": "customer-support-v1",
            "name": "고객 상담 프롬프트",
            "description": "고객 문의 응답용 프롬프트",
            "category": self.category.id,
            "tags": ["v1", "support"],
        }
        response = self.client.post("/api/v1/prompts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "고객 상담 프롬프트")
        self.assertEqual(response.data["category"], self.category.id)
        self.assertEqual(response.data["tags"], ["v1", "support"])
        self.assertTrue(Prompt.objects.filter(slug="customer-support-v1").exists())

    def test_create_prompt_duplicate_name_error(self) -> None:
        """Test that creating a prompt with a duplicate name raises validation error."""
        Prompt.objects.create(
            slug="existing-prompt",
            name="동일한 이름",
            description="기존 프롬프트",
            category=self.category,
        )
        payload = {
            "slug": "new-prompt-slug",
            "name": "동일한 이름",
            "description": "중복 이름 시도",
            "category": self.category.id,
        }
        response = self.client.post("/api/v1/prompts/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_retrieve_prompt_detail_with_sections(self) -> None:
        """Test retrieving prompt details including nested sections."""
        prompt = Prompt.objects.create(
            slug="test-prompt",
            name="테스트 프롬프트",
            description="설명",
            category=self.category,
        )
        version = prompt.get_or_create_default_version()
        Section.objects.create(
            version=version,
            role=Section.Role.SYSTEM,
            order=1,
            content="시스템 지침입니다.",
        )
        Section.objects.create(
            version=version,
            role=Section.Role.USER,
            order=2,
            content="유저 질문입니다.",
        )

        response = self.client.get(f"/api/v1/prompts/{prompt.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["sections"]), 2)
        self.assertEqual(response.data["sections"][0]["role"], "system")
        self.assertEqual(response.data["sections"][1]["role"], "user")

    def test_update_and_delete_prompt(self) -> None:
        """Test updating and deleting a Prompt."""
        prompt = Prompt.objects.create(
            slug="update-prompt",
            name="수정 전 이름",
            category=self.category,
        )
        # Update
        update_payload = {
            "slug": "update-prompt",
            "name": "수정 후 이름",
            "description": "업데이트된 설명",
            "category": self.category.id,
        }
        response = self.client.put(f"/api/v1/prompts/{prompt.id}/", update_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "수정 후 이름")

        # Delete
        del_response = self.client.delete(f"/api/v1/prompts/{prompt.id}/")
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Prompt.objects.filter(pk=prompt.id).exists())

    def test_section_crud_operations(self) -> None:
        """Test creating, updating, and deleting a Section."""
        prompt = Prompt.objects.create(
            slug="section-test-prompt",
            name="섹션 테스트 프롬프트",
            category=self.category,
        )
        # Create section
        section_payload = {
            "role": "system",
            "order": 1,
            "content": "초기 지침 내용",
        }
        sec_response = self.client.post(
            f"/api/v1/prompts/{prompt.id}/sections/",
            section_payload,
            format="json",
        )
        self.assertEqual(sec_response.status_code, status.HTTP_201_CREATED)
        section_id = sec_response.data["id"]

        # Update section
        update_sec_payload = {
            "role": "system",
            "order": 1,
            "content": "수정된 지침 내용",
        }
        put_sec_res = self.client.put(
            f"/api/v1/sections/{section_id}/",
            update_sec_payload,
            format="json",
        )
        self.assertEqual(put_sec_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_sec_res.data["content"], "수정된 지침 내용")

        # Delete section
        del_sec_res = self.client.delete(f"/api/v1/sections/{section_id}/")
        self.assertEqual(del_sec_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Section.objects.filter(pk=section_id).exists())

    def test_nested_section_list_filtering_and_404(self) -> None:
        """
        Test nested section list endpoint filters by prompt_id and returns 404.
        """
        p1 = Prompt.objects.create(slug="p1-sections", name="프롬프트 1", category=self.category)
        p2 = Prompt.objects.create(slug="p2-sections", name="프롬프트 2", category=self.category)

        v1 = p1.get_or_create_default_version()
        v2 = p2.get_or_create_default_version()

        Section.objects.create(version=v1, role="system", order=1, content="P1 시스템 지침")
        Section.objects.create(version=v2, role="user", order=1, content="P2 유저 지침")

        # Test GET /api/v1/prompts/p1.id/sections/ returns only p1 sections
        res1 = self.client.get(f"/api/v1/prompts/{p1.id}/sections/")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data), 1)
        self.assertEqual(res1.data[0]["content"], "P1 시스템 지침")

        # Test GET /api/v1/prompts/9999/sections/ returns 404 Not Found
        res_404 = self.client.get("/api/v1/prompts/9999/sections/")
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)
