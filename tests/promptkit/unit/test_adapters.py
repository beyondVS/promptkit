"""Public unit tests for provider-specific prompt argument adapters."""

import builtins
import time
import unittest
import warnings
from collections.abc import Callable
from unittest.mock import patch

from promptkit import AdapterConversionError, GeminiAdapter, OpenAIAdapter
from promptkit.models import CompiledPrompt, CompiledPromptSection

Conversion = Callable[[CompiledPrompt], object]


def section(role: str, order: int, content: str) -> CompiledPromptSection:
    """Create one immutable compiled section for adapter tests."""
    return CompiledPromptSection(role=role, order=order, content=content)


def compiled_prompt(
    *sections: CompiledPromptSection,
    content: str = "Aggregate content",
    slug: str = "support-reply",
    version: int = 4,
    label: str | None = "latest",
) -> CompiledPrompt:
    """Create one immutable compiled prompt without registry or provider I/O."""
    return CompiledPrompt(
        slug=slug,
        version=version,
        label=label,
        content=content,
        sections=sections,
    )


def conversions() -> tuple[Conversion, ...]:
    """Return every public conversion operation under the shared policy."""
    return (
        GeminiAdapter.to_generate_content_args,
        OpenAIAdapter.to_chat_completions_args,
        OpenAIAdapter.to_responses_args,
    )


class TestGeminiAdapter(unittest.TestCase):
    """Validate the public Gemini conversion contract without provider dependencies."""

    def test_maps_ordered_roles_parts_and_joined_system_instruction(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 3, "Prior answer"),
            section("system", 2, "Second policy"),
            section("user", 1, "Question"),
            section("system", 0, "First policy"),
        )

        result = GeminiAdapter.to_generate_content_args(prompt)

        self.assertEqual(
            result,
            {
                "contents": [
                    {"role": "user", "parts": [{"text": "Question"}]},
                    {"role": "model", "parts": [{"text": "Prior answer"}]},
                ],
                "config": {"system_instruction": "First policy\n\nSecond policy"},
            },
        )

    def test_omits_config_and_preserves_consecutive_sections(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 2, "Third"),
            section("user", 0, "First"),
            section("user", 1, "Second"),
        )

        result = GeminiAdapter.to_generate_content_args(prompt)

        self.assertEqual(
            result,
            {
                "contents": [
                    {"role": "user", "parts": [{"text": "First"}]},
                    {"role": "user", "parts": [{"text": "Second"}]},
                    {"role": "model", "parts": [{"text": "Third"}]},
                ]
            },
        )
        self.assertNotIn("config", result)


class TestOpenAIAdapter(unittest.TestCase):
    """Validate both public OpenAI conversion contracts without an SDK client."""

    def test_chat_completions_preserves_order_roles_and_distinct_messages(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 3, "Prior answer"),
            section("user", 1, "First question"),
            section("system", 0, "Policy"),
            section("user", 2, "Follow-up"),
        )

        result = OpenAIAdapter.to_chat_completions_args(prompt)

        self.assertEqual(
            result,
            {
                "messages": [
                    {"role": "system", "content": "Policy"},
                    {"role": "user", "content": "First question"},
                    {"role": "user", "content": "Follow-up"},
                    {"role": "assistant", "content": "Prior answer"},
                ]
            },
        )

    def test_responses_separates_joined_instructions_and_ordered_input(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 4, "Prior answer"),
            section("system", 2, "Second policy"),
            section("user", 1, "Question"),
            section("system", 0, "First policy"),
            section("user", 3, "Follow-up"),
        )

        result = OpenAIAdapter.to_responses_args(prompt)

        self.assertEqual(
            result,
            {
                "instructions": "First policy\n\nSecond policy",
                "input": [
                    {"role": "user", "content": "Question"},
                    {"role": "user", "content": "Follow-up"},
                    {"role": "assistant", "content": "Prior answer"},
                ],
            },
        )

    def test_responses_omits_instructions_without_system_sections(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 1, "Answer"),
            section("user", 0, "Question"),
        )

        result = OpenAIAdapter.to_responses_args(prompt)

        self.assertEqual(
            result,
            {
                "input": [
                    {"role": "user", "content": "Question"},
                    {"role": "assistant", "content": "Answer"},
                ]
            },
        )
        self.assertNotIn("instructions", result)


class TestAdapterSafetyPolicy(unittest.TestCase):
    """Validate shared failures, fallback, logging, and local-only behavior."""

    def test_rejects_duplicate_orders_without_disclosing_content(self) -> None:
        secret = "duplicate-secret-text"
        prompt = compiled_prompt(
            section("user", 0, secret),
            section("assistant", 0, "answer"),
        )

        for convert in conversions():
            with self.subTest(convert=convert.__qualname__):
                with self.assertRaisesRegex(
                    AdapterConversionError, "Duplicate section order: 0"
                ) as raised:
                    convert(prompt)
                self.assertNotIn(secret, str(raised.exception))

    def test_rejects_blank_cased_and_unknown_roles_without_disclosing_content(self) -> None:
        secret = "unsupported-role-secret"
        for role in ("", "User", "tool"):
            prompt = compiled_prompt(section(role, 0, secret))
            for convert in conversions():
                with self.subTest(role=role, convert=convert.__qualname__):
                    with self.assertRaisesRegex(
                        AdapterConversionError, "Unsupported section role"
                    ) as raised:
                        convert(prompt)
                    self.assertIn(repr(role), str(raised.exception))
                    self.assertNotIn(secret, str(raised.exception))

    def test_uses_aggregate_content_as_one_user_item_without_sections(self) -> None:
        prompt = compiled_prompt(content="Aggregate {{ stays_literal }}")

        self.assertEqual(
            GeminiAdapter.to_generate_content_args(prompt),
            {"contents": [{"role": "user", "parts": [{"text": prompt.content}]}]},
        )
        self.assertEqual(
            OpenAIAdapter.to_chat_completions_args(prompt),
            {"messages": [{"role": "user", "content": prompt.content}]},
        )
        self.assertEqual(
            OpenAIAdapter.to_responses_args(prompt),
            {"input": [{"role": "user", "content": prompt.content}]},
        )

    def test_system_only_results_emit_one_safe_log_and_no_runtime_warning(self) -> None:
        first = "first-system-secret"
        second = "second-system-secret"
        prompt = compiled_prompt(
            section("system", 2, second),
            section("system", 0, first),
            content="aggregate-secret",
            slug="policy-prompt",
            version=7,
            label="canary",
        )
        cases: tuple[tuple[Conversion, object], ...] = (
            (
                GeminiAdapter.to_generate_content_args,
                {"config": {"system_instruction": f"{first}\n\n{second}"}},
            ),
            (
                OpenAIAdapter.to_chat_completions_args,
                {
                    "messages": [
                        {"role": "system", "content": first},
                        {"role": "system", "content": second},
                    ]
                },
            ),
            (
                OpenAIAdapter.to_responses_args,
                {"instructions": f"{first}\n\n{second}"},
            ),
        )

        for convert, expected in cases:
            with self.subTest(convert=convert.__qualname__):
                with warnings.catch_warnings(record=True) as runtime_warnings:
                    with self.assertLogs("promptkit.adapters", level="WARNING") as captured:
                        result = convert(prompt)

                self.assertEqual(result, expected)
                self.assertEqual(runtime_warnings, [])
                self.assertEqual(len(captured.records), 1)
                record = captured.records[0]
                self.assertEqual(record.levelname, "WARNING")
                self.assertIn("policy-prompt", record.getMessage())
                self.assertIn("7", record.getMessage())
                self.assertIn("canary", record.getMessage())
                self.assertNotIn(first, record.getMessage())
                self.assertNotIn(second, record.getMessage())
                self.assertNotIn(prompt.content, record.getMessage())

    def test_preserves_literal_and_unicode_text_without_mutation_or_metadata(self) -> None:
        prompt = compiled_prompt(
            section("assistant", 2, "  \n한글 🚀  "),
            section("system", 0, ""),
            section("user", 1, "{{ untouched_variable }}"),
            content="aggregate-not-used",
            slug="internal-source-slug",
            version=987,
            label="private-label",
        )
        before = prompt.model_dump(mode="python")

        results = (
            GeminiAdapter.to_generate_content_args(prompt),
            OpenAIAdapter.to_chat_completions_args(prompt),
            OpenAIAdapter.to_responses_args(prompt),
        )

        self.assertEqual(
            results[0],
            {
                "contents": [
                    {"role": "user", "parts": [{"text": "{{ untouched_variable }}"}]},
                    {"role": "model", "parts": [{"text": "  \n한글 🚀  "}]},
                ],
                "config": {"system_instruction": ""},
            },
        )
        self.assertEqual(
            results[1],
            {
                "messages": [
                    {"role": "system", "content": ""},
                    {"role": "user", "content": "{{ untouched_variable }}"},
                    {"role": "assistant", "content": "  \n한글 🚀  "},
                ]
            },
        )
        self.assertEqual(
            results[2],
            {
                "instructions": "",
                "input": [
                    {"role": "user", "content": "{{ untouched_variable }}"},
                    {"role": "assistant", "content": "  \n한글 🚀  "},
                ],
            },
        )
        self.assertEqual(prompt.model_dump(mode="python"), before)
        for result in results:
            rendered = repr(result)
            self.assertNotIn("internal-source-slug", rendered)
            self.assertNotIn("private-label", rendered)

    def test_conversion_does_not_import_provider_sdks(self) -> None:
        prompt = compiled_prompt(section("user", 0, "Question"))

        with patch("builtins.__import__", wraps=builtins.__import__) as import_mock:
            for convert in conversions():
                convert(prompt)

        imported_names = [str(call.args[0]) for call in import_mock.call_args_list if call.args]
        self.assertFalse(
            any(name == "openai" or name.startswith("google") for name in imported_names)
        )

    def test_each_conversion_handles_200_sections_in_under_one_second(self) -> None:
        prompt = compiled_prompt(
            *(
                section("user" if index % 2 == 0 else "assistant", index, str(index))
                for index in range(200)
            )
        )

        for convert in conversions():
            with self.subTest(convert=convert.__qualname__):
                started = time.perf_counter()
                convert(prompt)
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 1.0)
