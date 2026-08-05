"""
Tests for transactional lifecycle services.
"""

from django.test import TestCase

from apps.server.prompts.models import (
    Label,
    Prompt,
    PromptCategory,
    Section,
    VariableDefinition,
    Version,
)
from apps.server.prompts.services.lifecycle import (
    StaleRevisionError,
    clear_on_live_version,
    clone_version,
    create_prompt_with_initial_draft,
    delete_draft_version,
    delete_prompt,
    publish_version,
    remove_custom_label,
    set_custom_label,
    set_on_live_version,
)


class LifecycleServicesTests(TestCase):
    category: PromptCategory

    def setUp(self) -> None:
        self.category = PromptCategory.objects.create(
            name="Lifecycle Services", slug="lifecycle-services"
        )

    def test_create_prompt_with_initial_draft(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="New Prompt",
            slug="new-prompt",
        )
        self.assertEqual(prompt.versions.count(), 1)
        self.assertEqual(draft.version_number, 1)
        self.assertEqual(draft.status, Version.Status.DRAFT)
        self.assertFalse(draft.is_on_live)

    def test_publish_version_and_stale_revision(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="Publish Test",
            slug="publish-test",
        )
        # Attempt publish with wrong revision
        with self.assertRaises(StaleRevisionError):
            publish_version(draft.id, expected_revision=999)

        # Publish successfully
        pub = publish_version(draft.id, expected_revision=1)
        self.assertEqual(pub.status, Version.Status.PUBLISHED)
        self.assertEqual(pub.revision, 2)
        # Verify 'latest' label was automatically assigned
        self.assertTrue(Label.objects.filter(prompt=prompt, name="latest", version=pub).exists())

    def test_clone_version_deep_copy(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="Clone Test",
            slug="clone-test",
        )
        Section.objects.create(
            version=draft, role=Section.Role.SYSTEM, order=0, content="System prompt {{ name }}"
        )
        VariableDefinition.objects.create(
            version=draft, name="name", var_type=VariableDefinition.VarType.STRING
        )
        published = publish_version(draft.id)

        # Clone from published version
        cloned = clone_version(published.id)
        self.assertEqual(cloned.version_number, 2)
        self.assertEqual(cloned.status, Version.Status.DRAFT)
        self.assertEqual(cloned.sections.count(), 1)
        self.assertEqual(cloned.variables.count(), 1)
        self.assertEqual(cloned.sections.first().content, "System prompt {{ name }}")

    def test_delete_draft_and_published_rejection(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="Delete Version Test",
            slug="delete-ver-test",
        )
        pub = publish_version(draft.id)
        # Rejects deleting published version
        with self.assertRaises(ValueError):
            delete_draft_version(pub.id)

        # Clone a draft and delete it
        draft2 = clone_version(pub.id)
        self.assertEqual(prompt.versions.count(), 2)
        delete_draft_version(draft2.id)
        self.assertEqual(prompt.versions.count(), 1)

    def test_on_live_workflow_and_delete_prompt_guard(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="On Live Test",
            slug="on-live-test",
        )
        pub = publish_version(draft.id)
        # Cannot set draft to on-live
        draft2 = clone_version(pub.id)
        with self.assertRaises(ValueError):
            set_on_live_version(prompt, version_number=draft2.version_number)

        # Set pub on-live
        set_on_live_version(prompt, version_number=pub.version_number)
        pub.refresh_from_db()
        self.assertTrue(pub.is_on_live)

        # Attempting to delete prompt with on-live version fails
        with self.assertRaises(ValueError):
            delete_prompt(prompt)

        # Clear on-live and delete prompt succeeds
        clear_on_live_version(prompt)
        delete_prompt(prompt)
        self.assertFalse(Prompt.objects.filter(id=prompt.id).exists())

    def test_custom_label_rules(self) -> None:
        prompt, draft = create_prompt_with_initial_draft(
            category=self.category,
            name="Label Test",
            slug="label-test",
        )
        pub = publish_version(draft.id)

        # Prohibit 'production'
        with self.assertRaises(ValueError):
            set_custom_label(prompt, "production", version_number=pub.version_number)

        # Set valid label
        lbl = set_custom_label(prompt, "staging", version_number=pub.version_number)
        self.assertEqual(lbl.name, "staging")

        # Remove label
        remove_custom_label(prompt, "staging")
        self.assertFalse(Label.objects.filter(prompt=prompt, name="staging").exists())
