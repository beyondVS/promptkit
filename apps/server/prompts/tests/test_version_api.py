"""
Unit tests for Prompt Version management, Rollback, and Diff comparison API endpoints.
Uses django.test.TestCase per Constitution hybrid test architecture rules.
"""

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.server.prompts.models import Prompt, PromptCategory, Version


class PromptVersionAPITestCase(TestCase):
    """
    Test suite for Prompt Version history, immutability, rollback, and line diff endpoints.
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.defaults["HTTP_X_API_KEY"] = "dev-secret-key"
        self.category = PromptCategory.objects.create(
            name="버전 테스트 카테고리",
            slug="version-test-cat",
        )
        self.prompt = Prompt.objects.create(
            slug="version-test-prompt",
            name="버전 테스트 프롬프트",
            description="버전 관리 테스트용",
            category=self.category,
        )

    def test_version_auto_creation_and_list(self) -> None:
        """
        Test automatic Version creation on Prompt creation/update and list retrieval.
        """
        # Create prompt via API with initial template_text
        payload = {
            "slug": "auto-version-prompt",
            "name": "자동 버전 생성 프롬프트",
            "category": self.category.id,
            "template_text": "Hello {user}, initial template",
            "changelog": "Initial creation",
        }
        res = self.client.post("/api/v1/prompts/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        prompt_id = res.data["id"]

        # Verify initial version 1 created
        prompt = Prompt.objects.get(pk=prompt_id)
        self.assertEqual(prompt.versions.count(), 1)
        v1 = prompt.versions.first()
        self.assertIsNotNone(v1)

        # Update prompt with new template_text
        update_payload = {
            "slug": "auto-version-prompt",
            "name": "자동 버전 생성 프롬프트",
            "category": self.category.id,
            "template_text": "Hello {user}, updated template text v2",
            "changelog": "Updated to v2",
        }
        res_update = self.client.put(f"/api/v1/prompts/{prompt_id}/", update_payload, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)

        # Verify new version 2 created
        self.assertEqual(prompt.versions.count(), 2)

        # Retrieve version list API
        list_res = self.client.get(f"/api/v1/prompts/{prompt_id}/versions/")
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 2)
        # Should be ordered descending (v2 first, then v1)
        self.assertEqual(list_res.data[0]["version_number"], 2)
        self.assertEqual(list_res.data[1]["version_number"], 1)

    def test_skip_version_creation_for_identical_template_text(self) -> None:
        """
        Test 'Skip Creation' policy when updating prompt with identical template text.
        """
        # Create prompt with v1
        Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Static prompt text",
            changelog="Initial v1",
        )

        update_payload = {
            "slug": self.prompt.slug,
            "name": self.prompt.name,
            "category": self.category.id,
            "template_text": "Static prompt text",  # Identical text
            "changelog": "Should be skipped",
        }
        res = self.client.put(f"/api/v1/prompts/{self.prompt.id}/", update_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Version count remains 1
        self.assertEqual(self.prompt.versions.count(), 1)

    def test_version_detail_and_immutability_protection(self) -> None:
        """
        Test retrieving version detail and verifying 405 Method Not Allowed on direct modification.
        """
        Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Immutable text v1",
            changelog="v1",
        )

        # Retrieve version 1 detail
        detail_res = self.client.get(f"/api/v1/prompts/{self.prompt.id}/versions/1/")
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["template_text"], "Immutable text v1")

        # Test direct PUT modification -> 405
        put_res = self.client.put(
            f"/api/v1/prompts/{self.prompt.id}/versions/1/",
            {"template_text": "Illegal update"},
            format="json",
        )
        self.assertEqual(put_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test direct DELETE -> 405
        del_res = self.client.delete(f"/api/v1/prompts/{self.prompt.id}/versions/1/")
        self.assertEqual(del_res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_rollback_action_success_and_append_only(self) -> None:
        """
        Test rolling back to a past version creates a new version record without destroying history.
        """
        v1 = Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Version 1 text",
            changelog="v1",
        )
        Version.objects.create(
            prompt=self.prompt,
            version_number=2,
            template_text="Version 2 text with bugs",
            changelog="v2",
        )

        # Call rollback to v1
        rollback_payload = {
            "target_version": 1,
            "changelog": "Emergency rollback to v1",
        }
        res = self.client.post(
            f"/api/v1/prompts/{self.prompt.id}/versions/rollback/",
            rollback_payload,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["version_number"], 3)
        self.assertEqual(res.data["template_text"], v1.template_text)
        self.assertEqual(res.data["changelog"], "Emergency rollback to v1")

        # Total versions is now 3 (Append-Only)
        self.assertEqual(self.prompt.versions.count(), 3)

    def test_rollback_target_version_not_found_returns_404(self) -> None:
        """
        Test rollback to a non-existent version returns 404 Not Found.
        """
        Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="v1",
        )

        rollback_payload = {"target_version": 99}
        res = self.client.post(
            f"/api/v1/prompts/{self.prompt.id}/versions/rollback/",
            rollback_payload,
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_version_diff_comparison_success(self) -> None:
        """
        Test Structured Line Diff comparison between two versions.
        """
        Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="Line 1: System prompt\nLine 2: Old instruction",
            changelog="v1",
        )
        Version.objects.create(
            prompt=self.prompt,
            version_number=2,
            template_text="Line 1: System prompt\nLine 2: New instruction\nLine 3: Added line",
            changelog="v2",
        )

        res = self.client.get(
            f"/api/v1/prompts/{self.prompt.id}/versions/diff/?from_version=1&to_version=2"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["prompt_id"], self.prompt.id)
        self.assertEqual(res.data["from_version"], 1)
        self.assertEqual(res.data["to_version"], 2)

        diff_list = res.data["diff"]
        self.assertGreater(len(diff_list), 0)

        # Check line ops
        ops = [item["op"] for item in diff_list]
        self.assertIn("equal", ops)
        self.assertIn("added", ops)
        self.assertIn("deleted", ops)

    def test_version_diff_missing_or_invalid_params_returns_error(self) -> None:
        """
        Test missing or invalid version parameters for diff action return 400 or 404.
        """
        Version.objects.create(
            prompt=self.prompt,
            version_number=1,
            template_text="v1",
        )

        # Missing params -> 400
        res_400 = self.client.get(f"/api/v1/prompts/{self.prompt.id}/versions/diff/")
        self.assertEqual(res_400.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid non-existent version -> 404
        res_404 = self.client.get(
            f"/api/v1/prompts/{self.prompt.id}/versions/diff/?from_version=1&to_version=99"
        )
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)
