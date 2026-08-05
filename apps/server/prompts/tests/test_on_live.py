"""
Tests for on-live single deployment target lifecycle management (US3).
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, Section, VariableDefinition
from apps.server.prompts.services.lifecycle import (
    clone_version,
    create_prompt_with_initial_draft,
    publish_version,
)


class OnLiveLifecycleTests(TestCase):
    staff_user: User
    prompt: Prompt

    def setUp(self) -> None:
        self.staff_user = User.objects.create_superuser(
            username="admin_onlive", password="password"
        )
        self.client.login(username="admin_onlive", password="password")
        cat = PromptCategory.objects.create(name="OnLiveCat", slug="onlive-cat")
        self.prompt, self.v1 = create_prompt_with_initial_draft(
            category=cat, name="OnLive Prompt", slug="onlive-prompt"
        )
        Section.objects.create(version=self.v1, role="user", order=0, content="v1 {{ x }}")
        VariableDefinition.objects.create(version=self.v1, name="x", var_type="string")
        self.pub_v1 = publish_version(self.v1.id)
        self.v2 = clone_version(self.pub_v1.id)
        self.pub_v2 = publish_version(self.v2.id)

    def test_set_and_switch_on_live(self) -> None:
        # Set v1 on-live
        self.client.post(
            reverse("dashboard-on-live-set", kwargs={"pk": self.prompt.pk}),
            {"version_number": "1"},
        )
        self.pub_v1.refresh_from_db()
        self.assertTrue(self.pub_v1.is_on_live)
        self.assertFalse(self.pub_v2.is_on_live)

        # Switch to v2
        self.client.post(
            reverse("dashboard-on-live-set", kwargs={"pk": self.prompt.pk}),
            {"version_number": "2"},
        )
        self.pub_v1.refresh_from_db()
        self.pub_v2.refresh_from_db()
        self.assertFalse(self.pub_v1.is_on_live)
        self.assertTrue(self.pub_v2.is_on_live)

    def test_clear_on_live(self) -> None:
        self.client.post(
            reverse("dashboard-on-live-set", kwargs={"pk": self.prompt.pk}),
            {"version_number": "1"},
        )
        self.client.post(reverse("dashboard-on-live-clear", kwargs={"pk": self.prompt.pk}))
        self.pub_v1.refresh_from_db()
        self.assertFalse(self.pub_v1.is_on_live)
