"""
Tests for Prompt search result ordering via ORM.
Retires obsolete REST ordering endpoint per T061 and architecture rules.
"""

from django.test import TestCase

from apps.server.prompts.models import Prompt, PromptCategory


class PromptOrderingTestCase(TestCase):
    def setUp(self) -> None:
        self.category = PromptCategory.objects.create(name="support", slug="support")
        self.p1 = Prompt.objects.create(slug="alpha", name="Alpha Prompt", category=self.category)
        self.p2 = Prompt.objects.create(slug="beta", name="Beta Prompt", category=self.category)
        self.p3 = Prompt.objects.create(slug="gamma", name="Gamma Prompt", category=self.category)

    def test_ordering_by_name_asc(self) -> None:
        prompts = list(Prompt.objects.all().order_by("name"))
        names = [p.name for p in prompts]
        self.assertEqual(names, ["Alpha Prompt", "Beta Prompt", "Gamma Prompt"])

    def test_ordering_by_name_desc(self) -> None:
        prompts = list(Prompt.objects.all().order_by("-name"))
        names = [p.name for p in prompts]
        self.assertEqual(names, ["Gamma Prompt", "Beta Prompt", "Alpha Prompt"])
