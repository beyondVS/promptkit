"""
Tests for publish immutability and template validation in dashboard (US1).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import (
    Label,
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft


class DashboardPublishTests(TestCase):
    staff_user: User
    prompt: Prompt
    draft: Version

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_pub", password="password")
        self.client.login(username="admin_pub", password="password")
        cat = PromptCategory.objects.create(name="PublishCat", slug="pub-cat")
        self.prompt, self.draft = create_prompt_with_initial_draft(
            category=cat, name="Publish Prompt", slug="pub-prompt"
        )

    def test_publish_fails_when_undeclared_variable_referenced(self) -> None:
        # Add section referencing undeclared {{ missing_var }}
        Section.objects.create(
            version=self.draft, role="user", order=0, content="Hello {{ missing_var }}"
        )
        res = self.client.post(
            reverse("dashboard-version-publish", kwargs={"version_id": self.draft.id}),
            {"expected_revision": self.draft.revision},
        )
        self.assertEqual(res.status_code, 302)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Version.Status.DRAFT)

    def test_publish_success_updates_status_and_latest_label(self) -> None:
        Section.objects.create(version=self.draft, role="user", order=0, content="Hello {{ name }}")
        VariableDefinition.objects.create(version=self.draft, name="name", var_type="string")
        res = self.client.post(
            reverse("dashboard-version-publish", kwargs={"version_id": self.draft.id}),
            {"expected_revision": self.draft.revision},
        )
        self.assertEqual(res.status_code, 302)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Version.Status.PUBLISHED)
        self.assertTrue(
            Label.objects.filter(prompt=self.prompt, name="latest", version=self.draft).exists()
        )
