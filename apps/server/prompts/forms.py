"""Request-local forms for typed Playground compilation inputs."""

import json
import math
import re
from collections.abc import Iterable
from typing import Any

from django import forms
from django.core.exceptions import ValidationError

from apps.server.prompts.models import VariableDefinition

VARIABLE_FIELD_PREFIX = "variable__"
_INTEGER_PATTERN = re.compile(r"[+-]?\d+")


class PlaygroundCompileForm(forms.Form):
    """Convert browser strings into the strict types accepted by PromptKit."""

    def __init__(
        self,
        variables: Iterable[VariableDefinition],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.variables = list(variables)
        super().__init__(*args, **kwargs)
        for variable in self.variables:
            field_name = self.field_name(variable.name)
            self.fields[field_name] = forms.CharField(
                required=False,
                strip=False,
                label=variable.name,
                help_text=variable.description,
                initial=variable.default_value,
                widget=self._widget_for(variable),
            )

    @staticmethod
    def field_name(variable_name: str) -> str:
        """Return the submitted field name for one declared variable."""
        return f"{VARIABLE_FIELD_PREFIX}{variable_name}"

    @property
    def compile_params(self) -> dict[str, object]:
        """Return validated SDK parameters without omitted optional values."""
        if not self.is_valid():
            raise ValueError("compile_params requires a valid form")
        return {
            variable.name: self.cleaned_data[self.field_name(variable.name)]
            for variable in self.variables
            if self.field_name(variable.name) in self.cleaned_data
        }

    def clean(self) -> dict[str, Any]:
        """Reject undeclared fields and parse each declared browser value."""
        cleaned_data = super().clean() or {}
        declared_fields = {self.field_name(variable.name) for variable in self.variables}
        submitted_fields = {
            key for key in self.data.keys() if key.startswith(VARIABLE_FIELD_PREFIX)
        }
        for field_name in sorted(submitted_fields - declared_fields):
            variable_name = field_name.removeprefix(VARIABLE_FIELD_PREFIX)
            self.add_error(None, f"Unexpected variable input: {variable_name}.")

        for variable in self.variables:
            field_name = self.field_name(variable.name)
            raw_value = cleaned_data.get(field_name, "")
            if raw_value == "":
                cleaned_data.pop(field_name, None)
                if variable.required:
                    self.add_error(field_name, "This value is required.")
                continue
            try:
                cleaned_data[field_name] = self._parse_value(variable, raw_value)
            except ValidationError as error:
                cleaned_data.pop(field_name, None)
                self.add_error(field_name, error)
        return cleaned_data

    @staticmethod
    def _widget_for(variable: VariableDefinition) -> forms.Widget:
        attrs = {
            "data-variable-type": variable.var_type,
            "aria-required": str(variable.required).lower(),
        }
        if variable.var_type == VariableDefinition.VarType.BOOLEAN:
            return forms.Select(
                choices=(("", "Choose a value"), ("true", "True"), ("false", "False")),
                attrs=attrs,
            )
        if variable.var_type == VariableDefinition.VarType.JSON:
            return forms.Textarea(attrs=attrs)
        if variable.var_type == VariableDefinition.VarType.NUMBER:
            attrs["inputmode"] = "decimal"
        return forms.TextInput(attrs=attrs)

    @staticmethod
    def _parse_value(variable: VariableDefinition, raw_value: str) -> object:
        if variable.var_type == VariableDefinition.VarType.STRING:
            return raw_value
        if variable.var_type == VariableDefinition.VarType.NUMBER:
            try:
                parsed_number: int | float = (
                    int(raw_value) if _INTEGER_PATTERN.fullmatch(raw_value) else float(raw_value)
                )
            except ValueError as error:
                raise ValidationError("Enter a valid number.", code="invalid_number") from error
            if isinstance(parsed_number, float) and not math.isfinite(parsed_number):
                raise ValidationError("Enter a finite number.", code="invalid_number")
            return parsed_number
        if variable.var_type == VariableDefinition.VarType.BOOLEAN:
            if raw_value == "true":
                return True
            if raw_value == "false":
                return False
            raise ValidationError("Choose true or false.", code="invalid_boolean")
        if variable.var_type == VariableDefinition.VarType.JSON:
            try:
                parsed_json = json.loads(raw_value)
            except json.JSONDecodeError as error:
                raise ValidationError("Enter valid JSON.", code="invalid_json") from error
            if not isinstance(parsed_json, dict | list):
                raise ValidationError("Enter a JSON object or array.", code="invalid_json")
            return parsed_json
        raise ValidationError("Unsupported variable type.", code="unsupported_type")
