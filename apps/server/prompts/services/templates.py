"""
Template parsing, variable reference extraction, validation, and rename propagation.
"""

import json
import re

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def extract_template_variables(content: str) -> set[str]:
    """
    Extract all variable names referenced as {{ variable_name }} in content.
    """
    return set(VARIABLE_PATTERN.findall(content or ""))


def validate_variable_default_value(
    var_type: str, default_value: str | None
) -> tuple[bool, str | None]:
    """
    Validate that default_value is compatible with var_type.
    Returns (is_valid, error_message).
    """
    if default_value is None or default_value == "":
        return True, None

    if var_type == "string":
        return True, None

    if var_type == "number":
        try:
            float(default_value)
            return True, None
        except ValueError:
            return False, f"Default value '{default_value}' is not a valid number."

    if var_type == "boolean":
        val = default_value.strip().lower()
        if val in ("true", "false", "1", "0", "yes", "no"):
            return True, None
        return False, f"Default value '{default_value}' is not a valid boolean."

    if var_type == "json":
        try:
            json.loads(default_value)
            return True, None
        except json.JSONDecodeError as exc:
            return False, f"Default value is not valid JSON: {exc}"

    return True, None


def validate_version_template_references(
    section_contents: list[str],
    declared_variables: set[str],
) -> tuple[bool, list[str]]:
    """
    Validate that all variables referenced in sections are declared.
    Returns (is_valid, list_of_errors).
    """
    errors: list[str] = []
    referenced_vars: set[str] = set()

    for content in section_contents:
        referenced_vars.update(extract_template_variables(content))

    undeclared = referenced_vars - declared_variables
    if undeclared:
        for var in sorted(undeclared):
            errors.append(f"Variable '{var}' is referenced in sections but not defined.")

    return len(errors) == 0, errors


def rename_variable_in_content(content: str, old_name: str, new_name: str) -> str:
    """
    Atomically replace {{ old_name }} with {{ new_name }} in content string.
    """
    pattern = re.compile(r"\{\{\s*" + re.escape(old_name) + r"\s*\}\}")
    return pattern.sub(f"{{{{ {new_name} }}}}", content)


def is_variable_referenced(section_contents: list[str], var_name: str) -> bool:
    """
    Check if var_name is referenced in any of the section contents.
    """
    for content in section_contents:
        if var_name in extract_template_variables(content):
            return True
    return False
