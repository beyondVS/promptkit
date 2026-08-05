"""
Tests for stale revision optimistic concurrency conflict protection (US1).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Section, VariableDefinition, Version
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft


class StaleRevisionConflictTests(TestCase):
    staff_user: User
    prompt: Prompt
    draft: Version

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_conf", password="password")
        self.client.login(username="admin_conf", password="password")
        cat = PromptCategory.objects.create(name="ConfCat", slug="conf-cat")
        self.prompt, self.draft = create_prompt_with_initial_draft(
            category=cat, name="Conflict Prompt", slug="conf-prompt"
        )
        Section.objects.create(version=self.draft, role="user", order=0, content="Hello {{ name }}")
        VariableDefinition.objects.create(version=self.draft, name="name", var_type="string")

    def test_stale_revision_publish_rejection(self) -> None:
        # Simulate another request updating revision counter
        self.draft.revision = 10
        self.draft.save(update_fields=["revision"])

        # Client submits expected_revision = 1 (stale)
        res = self.client.post(
            reverse("dashboard-version-publish", kwargs={"version_id": self.draft.id}),
            {"expected_revision": "1"},
        )
        self.assertEqual(res.status_code, 302)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Version.Status.DRAFT)
