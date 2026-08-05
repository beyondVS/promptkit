"""
Tests for draft deletion and published deletion rejection (US2).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Section, VariableDefinition, Version
from apps.server.prompts.services.lifecycle import (
    clone_version,
    create_prompt_with_initial_draft,
    publish_version,
)


class VersionDeleteTests(TestCase):
    staff_user: User
    prompt: Prompt

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(
            username="admin_verdel", password="password"
        )
        self.client.login(username="admin_verdel", password="password")
        cat = PromptCategory.objects.create(name="VerDelCat", slug="verdel-cat")
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=cat, name="VerDel Prompt", slug="verdel-prompt"
        )
        Section.objects.create(version=self.v1, role="user", order=0, content="v1 {{ x }}")
        VariableDefinition.objects.create(version=self.v1, name="x", var_type="string")
        self.pub_v1 = publish_version(self.v1.id)

    def test_published_version_delete_rejected(self) -> None:
        res = self.client.post(
            reverse("dashboard-version-delete", kwargs={"version_id": self.pub_v1.id})
        )
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Version.objects.filter(id=self.pub_v1.id).exists())

    def test_draft_version_delete_success(self) -> None:
        draft_v2 = clone_version(self.pub_v1.id)
        self.assertEqual(self.prompt.versions.count(), 2)

        res = self.client.post(
            reverse("dashboard-version-delete", kwargs={"version_id": draft_v2.id})
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.prompt.versions.count(), 1)
        self.assertFalse(Version.objects.filter(id=draft_v2.id).exists())
