"""Public unit tests for local PromptKit compilation."""

import time
import traceback
import unittest
from typing import Any

from promptkit import (
    InvalidVariableTypeError,
    MissingVariableError,
    TemplateValidationError,
    UnexpectedVariableError,
)
from promptkit.models import RetrievedPrompt


def make_prompt(
    *,
    template_text: str = "Hello {{ customer_name }}!",
    variables: list[dict[str, Any]] | None = None,
    sections: list[dict[str, Any]] | None = None,
) -> RetrievedPrompt:
    """Create one retrieved prompt without a registry or network request."""
    return RetrievedPrompt.model_validate(
        {
            "slug": "support-reply",
            "name": "Support reply",
            "description": "A customer support response.",
            "category": {"name": "Support", "slug": "support"},
            "version": 4,
            "version_status": "published",
            "is_on_live": True,
            "label": "latest",
            "template_text": template_text,
            "variables": variables
            if variables is not None
            else [variable("customer_name", "string")],
            "sections": sections
            if sections is not None
            else [{"role": "user", "order": 0, "content": template_text}],
            "created_at": "2026-08-07T00:00:00Z",
        }
    )


def variable(
    name: str,
    var_type: str,
    *,
    required: bool = True,
    default_value: object | None = None,
) -> dict[str, Any]:
    """Create one declared variable payload."""
    return {
        "name": name,
        "var_type": var_type,
        "required": required,
        "default_value": default_value,
        "description": "",
    }


class TestRetrievedPromptCompile(unittest.TestCase):
    """Validate the public compile contract without external dependencies."""

    def test_renders_repeated_placeholders_and_preserves_metadata(self) -> None:
        prompt = make_prompt(
            template_text="Hello {{ customer_name }}. Bye {{ customer_name }}.",
            sections=[
                {"role": "system", "order": 0, "content": "Serve {{ customer_name }}."},
                {"role": "user", "order": 1, "content": "Hello {{ customer_name }}."},
            ],
        )

        compiled = prompt.compile({"customer_name": "Ada"})

        self.assertEqual(compiled.content, "Hello Ada. Bye Ada.")
        self.assertEqual(compiled.slug, "support-reply")
        self.assertEqual(compiled.version, 4)
        self.assertEqual(compiled.label, "latest")
        self.assertEqual(
            [(section.role, section.order, section.content) for section in compiled.sections],
            [("system", 0, "Serve Ada."), ("user", 1, "Hello Ada.")],
        )

    def test_renders_all_declared_types_and_json(self) -> None:
        prompt = make_prompt(
            template_text="{{ text }}|{{ number }}|{{ enabled }}|{{ payload }}",
            variables=[
                variable("text", "string"),
                variable("number", "number"),
                variable("enabled", "boolean"),
                variable("payload", "json"),
            ],
        )

        compiled = prompt.compile(
            {"text": "hello", "number": 2.5, "enabled": True, "payload": {"id": 7}}
        )

        self.assertEqual(compiled.content, 'hello|2.5|True|{"id":7}')

    def test_compiles_prompt_without_variables_unchanged(self) -> None:
        prompt = make_prompt(template_text="No substitutions.", variables=[], sections=[])

        compiled = prompt.compile()

        self.assertEqual(compiled.content, "No substitutions.")
        self.assertEqual(compiled.sections, ())

    def test_uses_normalized_defaults_and_caller_values_take_precedence(self) -> None:
        prompt = make_prompt(
            template_text="{{ name }}|{{ count }}|{{ enabled }}|{{ payload }}",
            variables=[
                variable("name", "string", default_value="default"),
                variable("count", "number", default_value="2"),
                variable("enabled", "boolean", default_value="true"),
                variable("payload", "json", default_value='["a"]'),
            ],
        )

        self.assertEqual(prompt.compile().content, 'default|2|True|["a"]')
        self.assertEqual(
            prompt.compile({"name": "caller", "count": 3, "enabled": False, "payload": []}).content,
            "caller|3|False|[]",
        )

    def test_rejects_missing_required_or_referenced_values(self) -> None:
        with self.assertRaisesRegex(MissingVariableError, "customer_name"):
            make_prompt().compile()

        optional = make_prompt(variables=[variable("customer_name", "string", required=False)])
        with self.assertRaisesRegex(MissingVariableError, "customer_name"):
            optional.compile()

    def test_rejects_unexpected_and_wrong_type_values_without_disclosure(self) -> None:
        secret = "do-not-expose-this-value"
        with self.assertRaisesRegex(UnexpectedVariableError, "other") as unexpected:
            make_prompt().compile({"customer_name": "Ada", "other": secret})
        self.assertNotIn(secret, str(unexpected.exception))

        typed = make_prompt(template_text="{{ count }}", variables=[variable("count", "number")])
        with self.assertRaisesRegex(InvalidVariableTypeError, "count") as invalid:
            typed.compile({"count": secret})
        self.assertNotIn(secret, str(invalid.exception))
        self.assertIsNone(invalid.exception.__cause__)
        self.assertIsNone(invalid.exception.__context__)
        self.assertNotIn(secret, "".join(traceback.format_exception(invalid.exception)))

    def test_rejects_invalid_defaults_and_strict_values(self) -> None:
        invalid_default = make_prompt(
            template_text="{{ count }}",
            variables=[variable("count", "number", default_value="bad")],
        )
        with self.assertRaisesRegex(InvalidVariableTypeError, "count"):
            invalid_default.compile()

        boolean_prompt = make_prompt(
            template_text="{{ enabled }}", variables=[variable("enabled", "boolean")]
        )
        with self.assertRaisesRegex(InvalidVariableTypeError, "enabled"):
            boolean_prompt.compile({"enabled": "true"})

        json_prompt = make_prompt(
            template_text="{{ payload }}", variables=[variable("payload", "json")]
        )
        with self.assertRaisesRegex(InvalidVariableTypeError, "payload"):
            json_prompt.compile({"payload": "[]"})

    def test_rejects_malformed_or_inconsistent_templates(self) -> None:
        cases = [
            ("Hello {{ customer_name", [variable("customer_name", "string")]),
            ("Hello customer_name }}", [variable("customer_name", "string")]),
            ("Hello {{ customer.name }}", [variable("customer", "string")]),
            ("Hello {{ other }}", [variable("customer_name", "string")]),
            ("No placeholders", [variable("customer_name", "string")]),
        ]
        for template_text, variables in cases:
            with self.subTest(template_text=template_text):
                with self.assertRaises(TemplateValidationError):
                    make_prompt(template_text=template_text, variables=variables).compile(
                        {"customer_name": "Ada"}
                    )

    def test_renders_values_only_once(self) -> None:
        prompt = make_prompt()

        compiled = prompt.compile({"customer_name": "{{ another_name }}"})

        self.assertEqual(compiled.content, "Hello {{ another_name }}!")

    def test_compiles_performance_boundary_within_one_second(self) -> None:
        variables = [variable(f"value_{index}", "string") for index in range(50)]
        template_text = " ".join(f"{{{{ value_{index % 50} }}}}" for index in range(200))
        prompt = make_prompt(template_text=template_text, variables=variables)
        params = {f"value_{index}": str(index) for index in range(50)}

        started = time.perf_counter()
        compiled = prompt.compile(params)
        elapsed = time.perf_counter() - started

        self.assertNotIn("{{", compiled.content)
        self.assertLess(elapsed, 1.0)
