import unittest
from typing import Any

import promptkit
from promptkit.models import RetrievedPrompt


def test_retrieved_prompt_parses_required_nested_fields_and_timestamp(
    prompt_payload: dict[str, Any],
) -> None:
    prompt = RetrievedPrompt.model_validate(prompt_payload)

    assert prompt.slug == "support-reply"
    assert prompt.category.slug == "support"
    assert prompt.variables[0].required is True
    assert prompt.sections[0].content == "Hello {{ customer_name }}!"
    assert prompt.created_at.isoformat() == "2026-08-07T00:00:00+00:00"


def test_retrieved_prompt_ignores_unknown_fields(prompt_payload: dict[str, Any]) -> None:
    prompt_payload["unknown_field"] = "ignored"

    prompt = RetrievedPrompt.model_validate(prompt_payload)

    assert not hasattr(prompt, "unknown_field")


class TestCompilePublicExports(unittest.TestCase):
    """Keep compilation types available from the package root."""

    def test_exports_compile_result_and_errors(self) -> None:
        self.assertTrue(hasattr(promptkit, "CompiledPrompt"))
        self.assertTrue(hasattr(promptkit, "MissingVariableError"))
        self.assertTrue(hasattr(promptkit, "InvalidVariableTypeError"))
        self.assertTrue(hasattr(promptkit, "UnexpectedVariableError"))
        self.assertTrue(hasattr(promptkit, "TemplateValidationError"))
