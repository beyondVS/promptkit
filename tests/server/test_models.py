"""
ORM Model tests for Prompt Registry app (apps.server.prompts).
Follows PromptKit Constitution hybrid test architecture rules using django.test.TestCase.
"""

from django.db.utils import IntegrityError
from django.test import TestCase

from apps.server.prompts.models import (
    Label,
    Prompt,
    Section,
    VariableDefinition,
    Version,
)


class PromptRegistryModelTests(TestCase):
    """
    Comprehensive tests for Prompt, Version, Label, VariableDefinition, and Section models.
    """

    prompt: Prompt
    version1: Version
    version2: Version

    @classmethod
    def setUpTestData(cls) -> None:
        cls.prompt = Prompt.objects.create(
            slug="welcome-email",
            name="Welcome Email Prompt",
            description="Email sent to new users",
        )
        cls.version1 = Version.objects.create(
            prompt=cls.prompt,
            version_number=1,
            template_text="Hello {{ user_name }}, welcome to {{ app_name }}!",
            changelog="Initial v1 release",
        )
        cls.version2 = Version.objects.create(
            prompt=cls.prompt,
            version_number=2,
            template_text="Hi {{ user_name }}, welcome aboard to {{ app_name }}!",
            changelog="v2 updated greeting",
        )

    # --- User Story 1: Prompt & Version Core Entity Storage (T004) ---

    def test_prompt_creation_and_string_representation(self) -> None:
        self.assertEqual(str(self.prompt), "Welcome Email Prompt (welcome-email)")
        self.assertEqual(self.prompt.versions.count(), 2)

    def test_version_relationship_and_ordering(self) -> None:
        versions = list(self.prompt.versions.all())
        self.assertEqual(len(versions), 2)
        # Ordered by -version_number
        self.assertEqual(versions[0].version_number, 2)
        self.assertEqual(versions[1].version_number, 1)

    def test_version_unique_constraint_per_prompt(self) -> None:
        with self.assertRaises(IntegrityError):
            Version.objects.create(
                prompt=self.prompt,
                version_number=1,  # Duplicate version_number for same prompt
                template_text="Duplicate version test",
            )

    def test_cascade_delete_prompt_deletes_versions(self) -> None:
        temp_prompt = Prompt.objects.create(
            slug="temp-prompt",
            name="Temp Prompt",
        )
        temp_prompt_id = temp_prompt.id
        Version.objects.create(
            prompt=temp_prompt,
            version_number=1,
            template_text="Temp template",
        )
        self.assertEqual(Version.objects.filter(prompt_id=temp_prompt_id).count(), 1)
        temp_prompt.delete()
        self.assertEqual(Version.objects.filter(prompt_id=temp_prompt_id).count(), 0)

    # --- User Story 2: Label-Based Tagging & Resolution (T007) ---

    def test_label_creation_and_tagging(self) -> None:
        label_prod = Label.objects.create(
            prompt=self.prompt,
            version=self.version2,
            name="production",
        )
        label_draft = Label.objects.create(
            prompt=self.prompt,
            version=self.version1,
            name="draft",
        )

        self.assertEqual(self.prompt.labels.count(), 2)
        self.assertEqual(str(label_prod), "welcome-email:production -> v2")
        self.assertEqual(str(label_draft), "welcome-email:draft -> v1")
        self.assertEqual(self.prompt.labels.get(name="production").version, self.version2)
        self.assertEqual(self.prompt.labels.get(name="draft").version, self.version1)

    def test_unique_label_per_prompt_constraint(self) -> None:
        Label.objects.create(
            prompt=self.prompt,
            version=self.version1,
            name="production",
        )
        with self.assertRaises(IntegrityError):
            Label.objects.create(
                prompt=self.prompt,
                version=self.version2,
                name="production",  # Second production label for same prompt
            )

    # --- User Story 3: Variable Definitions & Prompt Sections (T009) ---

    def test_variable_definition_creation_and_type_choices(self) -> None:
        var_user = VariableDefinition.objects.create(
            version=self.version1,
            name="user_name",
            var_type=VariableDefinition.VarType.STRING,
            required=True,
            description="Name of recipient",
        )
        var_app = VariableDefinition.objects.create(
            version=self.version1,
            name="app_name",
            var_type=VariableDefinition.VarType.STRING,
            required=False,
            default_value="PromptKit",
        )

        self.assertEqual(self.version1.variables.count(), 2)
        self.assertEqual(str(var_user), "welcome-email v1 - $user_name (string)")
        self.assertTrue(var_user.required)
        self.assertEqual(var_app.default_value, "PromptKit")

    def test_unique_variable_per_version_constraint(self) -> None:
        VariableDefinition.objects.create(
            version=self.version1,
            name="user_name",
            var_type=VariableDefinition.VarType.STRING,
        )
        with self.assertRaises(IntegrityError):
            VariableDefinition.objects.create(
                version=self.version1,
                name="user_name",  # Duplicate variable name for same version
                var_type=VariableDefinition.VarType.INTEGER,
            )

    def test_section_creation_ordering_and_role_choices(self) -> None:
        sec_sys = Section.objects.create(
            version=self.version1,
            role=Section.Role.SYSTEM,
            order=0,
            content="You are a helpful customer support agent.",
        )
        sec_user = Section.objects.create(
            version=self.version1,
            role=Section.Role.USER,
            order=1,
            content="Help me with {{ query }}.",
        )

        self.assertEqual(self.version1.sections.count(), 2)
        sections = list(self.version1.sections.all())
        self.assertEqual(sections[0], sec_sys)
        self.assertEqual(sections[1], sec_user)
        self.assertEqual(str(sec_sys), "welcome-email v1 - Section 0 (system)")

    def test_unique_section_order_per_version_constraint(self) -> None:
        Section.objects.create(
            version=self.version1,
            role=Section.Role.SYSTEM,
            order=0,
            content="System prompt 1",
        )
        with self.assertRaises(IntegrityError):
            Section.objects.create(
                version=self.version1,
                role=Section.Role.USER,
                order=0,  # Duplicate order index for same version
                content="System prompt 2",
            )
