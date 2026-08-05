"""
Tests for draft-only section and variable CUD handlers in the dashboard (US1).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Section, VariableDefinition, Version
from apps.server.prompts.services.lifecycle import create_prompt_with_initial_draft, publish_version


class SectionVariableCUDTests(TestCase):
    staff_user: User
    prompt: Prompt
    draft_version: Version

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_sec", password="password")
        self.client.login(username="admin_sec", password="password")
        cat = PromptCategory.objects.create(name="CatSec", slug="cat-sec")
        self.prompt, self.draft_version = create_prompt_with_initial_draft(
            category=cat, name="SecVar Prompt", slug="secvar-prompt"
        )

    def test_section_crud_on_draft(self) -> None:
        # Add section
        res = self.client.post(
            reverse("dashboard-section-create", kwargs={"version_id": self.draft_version.id}),
            {"role": "system", "order": "0", "content": "System message {{ user_name }}"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.draft_version.sections.count(), 1)

        # Delete section
        sec = self.draft_version.sections.first()
        self.assertIsNotNone(sec)
        if sec:
            res_del = self.client.post(reverse("dashboard-section-delete", kwargs={"pk": sec.pk}))
            self.assertEqual(res_del.status_code, 302)
            self.assertEqual(self.draft_version.sections.count(), 0)

    def test_section_cud_rejected_on_published_version(self) -> None:
        VariableDefinition.objects.create(version=self.draft_version, name="var", var_type="string")
        Section.objects.create(
            version=self.draft_version, role="user", order=0, content="Hello {{ var }}"
        )
        published = publish_version(self.draft_version.id)

        # Attempt to add section to published version
        res = self.client.post(
            reverse("dashboard-section-create", kwargs={"version_id": published.id}),
            {"role": "user", "order": "1", "content": "New content"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertEqual(published.sections.count(), 1)

    def test_variable_rename_propagation_and_delete_protection(self) -> None:
        # Add variable
        self.client.post(
            reverse("dashboard-variable-create", kwargs={"version_id": self.draft_version.id}),
            {"name": "old_name", "var_type": "string", "required": "on"},
        )
        # Add section referencing old_name
        self.client.post(
            reverse("dashboard-section-create", kwargs={"version_id": self.draft_version.id}),
            {"role": "user", "order": "0", "content": "Hello {{ old_name }}!"},
        )

        var = self.draft_version.variables.get(name="old_name")

        # Attempt to delete variable referenced in section -> rejected
        res_del = self.client.post(reverse("dashboard-variable-delete", kwargs={"pk": var.pk}))
        self.assertEqual(res_del.status_code, 302)
        self.assertTrue(self.draft_version.variables.filter(name="old_name").exists())

        # Update variable name -> propagates reference to section content
        res_upd = self.client.post(
            reverse("dashboard-variable-update", kwargs={"pk": var.pk}),
            {"name": "new_name", "var_type": "string", "required": "on"},
        )
        self.assertEqual(res_upd.status_code, 302)
        sec = self.draft_version.sections.first()
        self.assertIsNotNone(sec)
        if sec:
            self.assertIn("{{ new_name }}", sec.content)
