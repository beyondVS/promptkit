"""
Tests for template parsing, variable extraction, and reference propagation.
"""

import unittest

from apps.server.prompts.services.templates import (
    extract_template_variables,
    is_variable_referenced,
    rename_variable_in_content,
    validate_variable_default_value,
    validate_version_template_references,
)


class TemplateValidationTests(unittest.TestCase):
    def test_extract_template_variables(self) -> None:
        content = "Hello {{ user_name }}, welcome to {{ app_name }}! {{ user_name }}"
        vars_found = extract_template_variables(content)
        self.assertEqual(vars_found, {"user_name", "app_name"})

    def test_validate_variable_default_value(self) -> None:
        # String
        ok, _ = validate_variable_default_value("string", "anything")
        self.assertTrue(ok)

        # Number
        ok, _ = validate_variable_default_value("number", "42.5")
        self.assertTrue(ok)
        ok, err = validate_variable_default_value("number", "not_a_number")
        self.assertFalse(ok)
        self.assertIn("not a valid number", err or "")

        # Boolean
        ok, _ = validate_variable_default_value("boolean", "true")
        self.assertTrue(ok)
        ok, err = validate_variable_default_value("boolean", "maybe")
        self.assertFalse(ok)

        # JSON
        ok, _ = validate_variable_default_value("json", '{"key": "val"}')
        self.assertTrue(ok)
        ok, err = validate_variable_default_value("json", "{invalid json}")
        self.assertFalse(ok)

    def test_validate_version_template_references(self) -> None:
        sections = [
            "System prompt for {{ role }}",
            "User message: {{ query }} and {{ role }}",
        ]
        # Declared has all
        ok, errors = validate_version_template_references(sections, {"role", "query"})
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

        # Declared missing 'role'
        ok, errors = validate_version_template_references(sections, {"query"})
        self.assertFalse(ok)
        self.assertEqual(len(errors), 1)
        self.assertIn("role", errors[0])

    def test_rename_variable_in_content(self) -> None:
        content = "Hello {{ old_var }}, {{ old_var}} and {{other}}"
        renamed = rename_variable_in_content(content, "old_var", "new_var")
        self.assertEqual(renamed, "Hello {{ new_var }}, {{ new_var }} and {{other}}")

    def test_is_variable_referenced(self) -> None:
        sections = ["Hello {{ user_name }}"]
        self.assertTrue(is_variable_referenced(sections, "user_name"))
        self.assertFalse(is_variable_referenced(sections, "other_var"))
