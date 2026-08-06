"""Tests for the staff-only Playground and variable schema interface."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from apps.server.prompts.models import Prompt, PromptCategory, VariableDefinition, Version
from apps.server.prompts.services.lifecycle import (
    clone_version,
    create_prompt_with_initial_draft,
    publish_version,
)


class DashboardPlaygroundTests(TestCase):
    """Protect and validate transient variable-input preparation flows."""

    staff_user: User
    regular_user: User
    prompt: Prompt
    published_version: Version
    draft_version: Version
    empty_version: Version

    @classmethod
    def setUpTestData(cls) -> None:
        cls.staff_user = User.objects.create_superuser(
            username="playground-admin", password="password"
        )
        cls.regular_user = User.objects.create_user(username="playground-user", password="password")
        category = PromptCategory.objects.create(name="Playground", slug="playground")
        cls.prompt, initial_draft = create_prompt_with_initial_draft(
            category=category,
            name="Greeting",
            slug="greeting",
        )
        VariableDefinition.objects.create(
            version=initial_draft,
            name="count",
            var_type=VariableDefinition.VarType.NUMBER,
            required=True,
            default_value="3",
            description="Number of greetings",
        )
        VariableDefinition.objects.create(
            version=initial_draft,
            name="enabled",
            var_type=VariableDefinition.VarType.BOOLEAN,
            required=False,
            default_value=None,
            description="Enable the greeting",
        )
        VariableDefinition.objects.create(
            version=initial_draft,
            name="metadata",
            var_type=VariableDefinition.VarType.JSON,
            required=False,
            default_value='{"locale":"ko"}',
            description="Optional metadata",
        )
        VariableDefinition.objects.create(
            version=initial_draft,
            name="name",
            var_type=VariableDefinition.VarType.STRING,
            required=True,
            default_value="Visitor",
            description="Greeting recipient",
        )
        cls.published_version = publish_version(initial_draft.id)
        cls.draft_version = clone_version(cls.published_version.id)
        _, cls.empty_version = create_prompt_with_initial_draft(
            category=category,
            name="No Variables",
            slug="no-variables",
        )

    def setUp(self) -> None:
        self.client.login(username="playground-admin", password="password")

    def test_schema_returns_only_selected_version_metadata(self) -> None:
        response = self.client.get(
            reverse("dashboard-variable-schema", kwargs={"version_id": self.published_version.id})
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["prompt"]["id"], self.prompt.id)
        self.assertEqual(payload["version"]["id"], self.published_version.id)
        self.assertEqual(payload["version"]["status"], Version.Status.PUBLISHED)
        self.assertEqual(
            [item["name"] for item in payload["variables"]],
            [
                "count",
                "enabled",
                "metadata",
                "name",
            ],
        )
        self.assertNotIn("template_text", payload)
        self.assertNotIn("sections", payload)

    def test_schema_supports_draft_and_preserves_nullable_default(self) -> None:
        response = self.client.get(
            reverse("dashboard-variable-schema", kwargs={"version_id": self.draft_version.id})
        )

        self.assertEqual(response.status_code, 200)
        variables = {item["name"]: item for item in response.json()["variables"]}
        self.assertEqual(variables["enabled"]["default_value"], None)
        self.assertEqual(variables["metadata"]["var_type"], VariableDefinition.VarType.JSON)

    def test_playground_page_contains_selected_version_and_variable_schema(self) -> None:
        response = self.client.get(
            reverse("dashboard-playground", kwargs={"version_id": self.draft_version.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Greeting")
        self.assertContains(response, f"Version {self.draft_version.version_number}")
        self.assertContains(response, "data-schema-url")
        self.assertContains(response, "metadata")

    def test_page_and_schema_protect_access(self) -> None:
        self.client.logout()
        schema_response = self.client.get(
            reverse("dashboard-variable-schema", kwargs={"version_id": self.draft_version.id})
        )
        page_response = self.client.get(
            reverse("dashboard-playground", kwargs={"version_id": self.draft_version.id})
        )
        self.assertEqual(schema_response.status_code, 302)
        self.assertEqual(page_response.status_code, 302)

        self.client.login(username="playground-user", password="password")
        denied_response = self.client.get(
            reverse("dashboard-variable-schema", kwargs={"version_id": self.draft_version.id})
        )
        self.assertIn(denied_response.status_code, [302, 403])

    def test_empty_unknown_and_non_get_states(self) -> None:
        empty_response = self.client.get(
            reverse("dashboard-playground", kwargs={"version_id": self.empty_version.id})
        )
        unknown_response = self.client.get(
            reverse("dashboard-variable-schema", kwargs={"version_id": 999999})
        )
        post_response = self.client.post(
            reverse("dashboard-variable-schema", kwargs={"version_id": self.draft_version.id})
        )

        self.assertEqual(empty_response.status_code, 200)
        self.assertContains(empty_response, "No variables")
        self.assertEqual(unknown_response.status_code, 404)
        self.assertEqual(post_response.status_code, 405)
