"""
Tests for Prompt search and category filtering in Prompt Registry ORM & Dashboard.
Retires obsolete REST search endpoints per T061 and architecture rules.
"""

from django.test import TestCase

from apps.server.prompts.models import Prompt, PromptCategory


class MultidimensionalSearchTestCase(TestCase):
    def setUp(self) -> None:
        self.cat_support = PromptCategory.objects.create(
            name="customer-support", slug="customer-support"
        )
        self.cat_codegen = PromptCategory.objects.create(name="code-gen", slug="code-gen")

        self.p1 = Prompt.objects.create(
            slug="p1",
            name="고객 상담 가이드라인",
            category=self.cat_support,
            tags=["v1", "support"],
        )
        self.p2 = Prompt.objects.create(
            slug="p2", name="코드 생성 도우미", category=self.cat_codegen, tags=["v1", "dev"]
        )

    def test_filter_prompts_by_category(self) -> None:
        support_prompts = Prompt.objects.filter(category__slug="customer-support")
        self.assertEqual(support_prompts.count(), 1)
        self.assertEqual(support_prompts.first().slug, "p1")

    def test_filter_prompts_by_name_icontains(self) -> None:
        matched = Prompt.objects.filter(name__icontains="고객")
        self.assertEqual(matched.count(), 1)
        self.assertEqual(matched.first().slug, "p1")
