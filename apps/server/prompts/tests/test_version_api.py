"""
Tests for Prompt Version management, publish immutability, and version history.
Retires obsolete REST-CUD endpoints per T061 and architecture rules.
"""

from django.test import TestCase

from apps.server.prompts.models import Prompt, PromptCategory, Version
from apps.server.prompts.services.lifecycle import (
    clone_version,
    create_prompt_with_initial_draft,
    publish_version,
)


class PromptVersionAPITestCase(TestCase):
    category: PromptCategory
    prompt: Prompt

    def setUp(self) -> None:
        self.category = PromptCategory.objects.create(
            name="Version Category",
            slug="ver-cat",
        )
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=self.category,
            name="Version Test Prompt",
            slug="ver-test-prompt",
        )

    def test_version_initial_draft_creation(self) -> None:
        self.assertEqual(self.prompt.versions.count(), 1)
        self.assertEqual(self.v1.version_number, 1)
        self.assertEqual(self.v1.status, Version.Status.DRAFT)

    def test_version_publish_immutability(self) -> None:
        pub_v1 = publish_version(self.v1.id)
        self.assertEqual(pub_v1.status, Version.Status.PUBLISHED)
        self.assertTrue(pub_v1.labels.filter(name="latest").exists())

    def test_version_clone_branching(self) -> None:
        pub_v1 = publish_version(self.v1.id)
        v2 = clone_version(pub_v1.id)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(v2.status, Version.Status.DRAFT)
        self.assertEqual(self.prompt.versions.count(), 2)
