"""
Tests for latest and custom label lifecycle management (US3).
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
)
from apps.server.prompts.services.lifecycle import (
    clone_version,
    create_prompt_with_initial_draft,
    publish_version,
)


class LabelLifecycleTests(TestCase):
    staff_user: User
    prompt: Prompt

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(username="admin_label", password="password")
        self.client.login(username="admin_label", password="password")
        cat = PromptCategory.objects.create(name="LabelCat", slug="label-cat")
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=cat, name="Label Prompt", slug="label-prompt"
        )
        Section.objects.create(version=self.v1, role="user", order=0, content="v1 {{ x }}")
        VariableDefinition.objects.create(version=self.v1, name="x", var_type="string")
        self.pub_v1 = publish_version(self.v1.id)

    def test_latest_label_moves_automatically_on_publish(self) -> None:
        lbl = Label.objects.get(prompt=self.prompt, name="latest")
        self.assertEqual(lbl.version, self.pub_v1)

        v2 = clone_version(self.pub_v1.id)
        pub_v2 = publish_version(v2.id)

        lbl.refresh_from_db()
        self.assertEqual(lbl.version, pub_v2)

    def test_custom_label_set_and_remove(self) -> None:
        # Set custom label 'staging'
        res = self.client.post(
            reverse("dashboard-label-set", kwargs={"pk": self.prompt.pk}),
            {"name": "staging", "version_number": "1"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            Label.objects.filter(prompt=self.prompt, name="staging", version=self.pub_v1).exists()
        )

        # Disallow 'production'
        res_prod = self.client.post(
            reverse("dashboard-label-set", kwargs={"pk": self.prompt.pk}),
            {"name": "production", "version_number": "1"},
        )
        self.assertEqual(res_prod.status_code, 302)
        self.assertFalse(Label.objects.filter(prompt=self.prompt, name="production").exists())

        # Remove 'staging'
        self.client.post(
            reverse("dashboard-label-remove", kwargs={"pk": self.prompt.pk}),
            {"name": "staging"},
        )
        self.assertFalse(Label.objects.filter(prompt=self.prompt, name="staging").exists())
