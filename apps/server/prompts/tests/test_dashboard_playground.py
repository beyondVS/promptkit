"""Tests for the staff-only Playground and variable schema interface."""

from time import perf_counter
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.html import escape
from promptkit import RetrievedPrompt

from apps.server.prompts.models import (
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)
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
        initial_draft.template_text = "Hello {{ name }} {{ count }} {{ enabled }} {{ metadata }}"
        initial_draft.save(update_fields=["template_text"])
        Section.objects.create(
            version=initial_draft,
            role=Section.Role.SYSTEM,
            order=0,
            content="System for {{ name }}",
        )
        Section.objects.create(
            version=initial_draft,
            role=Section.Role.USER,
            order=1,
            content="User says {{ name }} twice: {{ name }}",
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

    def compile_url(self, version: Version | None = None) -> str:
        """Return the selected version's existing Playground URL."""
        target = version or self.draft_version
        return reverse("dashboard-playground", kwargs={"version_id": target.id})

    @staticmethod
    def valid_payload(**overrides: str) -> dict[str, str]:
        """Return browser-form values for every declared variable."""
        payload = {
            "variable__count": "2",
            "variable__enabled": "true",
            "variable__metadata": '{"locale":"ko"}',
            "variable__name": "Ada",
        }
        payload.update(overrides)
        return payload

    def test_post_compiles_typed_values_once_without_persistence(self) -> None:
        before = {
            "prompts": Prompt.objects.count(),
            "versions": Version.objects.count(),
            "variables": VariableDefinition.objects.count(),
            "sections": Section.objects.count(),
        }
        started = perf_counter()

        original_compile = RetrievedPrompt.compile
        with patch.object(
            RetrievedPrompt,
            "compile",
            autospec=True,
            side_effect=original_compile,
        ) as compile_mock:
            response = self.client.post(self.compile_url(), self.valid_payload())

        self.assertLess(perf_counter() - started, 2.0)
        self.assertEqual(compile_mock.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "greeting")
        self.assertContains(response, f"Version {self.draft_version.version_number}")
        self.assertContains(response, "Hello Ada 2 True")
        self.assertContains(response, "System for Ada")
        self.assertContains(response, "User says Ada twice: Ada")
        self.assertContains(response, "No LLM request was made")
        self.assertEqual(
            before,
            {
                "prompts": Prompt.objects.count(),
                "versions": Version.objects.count(),
                "variables": VariableDefinition.objects.count(),
                "sections": Section.objects.count(),
            },
        )

    def test_post_preserves_unicode_whitespace_html_and_single_pass_values(self) -> None:
        value = "  안녕 <script>alert(1)</script> {{ count }}  "

        response = self.client.post(self.compile_url(), self.valid_payload(variable__name=value))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, escape(value), html=False)
        self.assertNotContains(response, "<script>alert(1)</script>", html=False)
        self.assertContains(response, "{{ count }}", html=False)

    def test_post_without_variables_compiles_original_empty_content(self) -> None:
        response = self.client.post(self.compile_url(self.empty_version), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Compilation succeeded")
        self.assertContains(response, "Compiled content is empty")

    def test_post_rejects_missing_invalid_and_undeclared_values(self) -> None:
        cases = (
            ({**self.valid_payload(), "variable__name": ""}, "name"),
            ({**self.valid_payload(), "variable__count": "nan"}, "count"),
            ({**self.valid_payload(), "variable__enabled": "yes"}, "enabled"),
            ({**self.valid_payload(), "variable__metadata": '"scalar"'}, "metadata"),
            ({**self.valid_payload(), "variable__unknown": "secret-value"}, "unknown"),
        )

        for payload, expected_name in cases:
            with self.subTest(expected_name=expected_name):
                response = self.client.post(self.compile_url(), payload)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_name)
                self.assertNotContains(response, "Compiled preview")

    def test_compile_failure_is_redacted_and_has_no_partial_preview(self) -> None:
        secret = "private-customer-value"
        Version.objects.filter(pk=self.draft_version.pk).update(
            template_text="Broken {{ undeclared }}"
        )

        with self.assertLogs("apps.server.prompts", level="ERROR") as captured:
            response = self.client.post(
                self.compile_url(), self.valid_payload(variable__name=secret)
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "template")
        self.assertNotContains(response, "Compiled preview")
        self.assertEqual(response.context["form"]["variable__name"].value(), secret)
        self.assertNotIn(secret, str(response.context["form"].errors))
        self.assertNotIn(secret, "\n".join(captured.output))
        self.assertNotIn("Broken {{ undeclared }}", "\n".join(captured.output))

    def test_repeated_posts_are_stateless(self) -> None:
        first = self.client.post(self.compile_url(), self.valid_payload(variable__name="First"))
        second = self.client.post(self.compile_url(), self.valid_payload(variable__name="Second"))

        self.assertContains(first, "First")
        self.assertNotContains(second, "First")
        self.assertContains(second, "Second")

    def test_post_access_csrf_and_unknown_version_are_protected(self) -> None:
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff_user)
        self.assertEqual(
            csrf_client.post(self.compile_url(), self.valid_payload()).status_code,
            403,
        )

        self.client.logout()
        self.assertEqual(
            self.client.post(self.compile_url(), self.valid_payload()).status_code, 302
        )
        self.client.login(username="playground-user", password="password")
        self.assertEqual(
            self.client.post(self.compile_url(), self.valid_payload()).status_code, 302
        )
        self.client.force_login(self.staff_user)
        unknown = reverse("dashboard-playground", kwargs={"version_id": 999999})
        self.assertEqual(self.client.post(unknown, self.valid_payload()).status_code, 404)

    def test_post_does_not_fallback_after_selected_version_is_deleted(self) -> None:
        url = self.compile_url()
        Version.objects.filter(pk=self.draft_version.pk).delete()

        response = self.client.post(url, self.valid_payload())

        self.assertEqual(response.status_code, 404)
