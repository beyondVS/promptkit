"""
Tests for cloning versions into independent new drafts (US2).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Section, VariableDefinition, Version
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft, publish_version


class VersionCloneTests(TestCase):
    staff_user: User
    prompt: Prompt
    v1: Version

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_clone", password="password")
        self.client.login(username="admin_clone", password="password")
        cat = PromptCategory.objects.create(name="CloneCat", slug="clone-cat")
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=cat, name="Clone Prompt", slug="clone-prompt"
        )
        Section.objects.create(version=self.v1, role="system", order=0, content="System {{ var }}")
        VariableDefinition.objects.create(version=self.v1, name="var", var_type="string")
        self.pub_v1 = publish_version(self.v1.id)

    def test_clone_published_version_creates_independent_draft(self) -> None:
        res = self.client.post(
            reverse("dashboard-version-clone", kwargs={"version_id": self.pub_v1.id})
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.prompt.versions.count(), 2)

        v2 = self.prompt.versions.get(version_number=2)
        self.assertEqual(v2.status, Version.Status.DRAFT)
        self.assertFalse(v2.is_on_live)
        self.assertEqual(v2.sections.count(), 1)
        self.assertEqual(v2.variables.count(), 1)

        # Confirm isolation: mutating v2 does not mutate v1
        v2_sec = v2.sections.first()
        self.assertIsNotNone(v2_sec)
        if v2_sec:
            v2_sec.content = "Modified in v2 {{ var }}"
            v2_sec.save()

        v1_sec = self.pub_v1.sections.first()
        self.assertIsNotNone(v1_sec)
        if v1_sec:
            self.assertEqual(v1_sec.content, "System {{ var }}")
