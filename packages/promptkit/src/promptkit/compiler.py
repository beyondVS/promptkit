"""Safe local rendering for retrieved PromptKit templates."""

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    create_model,
)
from pydantic_core import PydanticUndefined

from promptkit.exceptions import (
    InvalidVariableTypeError,
    MissingVariableError,
    TemplateValidationError,
    UnexpectedVariableError,
)
from promptkit.models import CompiledPrompt, CompiledPromptSection, PromptVariable, RetrievedPrompt

_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def compile_prompt(
    prompt: RetrievedPrompt,
    params: Mapping[str, object] | None,
) -> CompiledPrompt:
    """Validate a retrieved prompt and render it once with caller values."""
    declarations = _declarations_by_name(prompt.variables)
    referenced_names = _validate_templates(
        [prompt.template_text, *(section.content for section in prompt.sections)], declarations
    )
    values = _validate_values(declarations, referenced_names, params)

    return CompiledPrompt(
        slug=prompt.slug,
        version=prompt.version,
        label=prompt.label,
        content=_render_template(prompt.template_text, values),
        sections=tuple(
            CompiledPromptSection(
                role=section.role,
                order=section.order,
                content=_render_template(section.content, values),
            )
            for section in prompt.sections
        ),
    )


def _declarations_by_name(variables: Sequence[PromptVariable]) -> dict[str, PromptVariable]:
    declarations: dict[str, PromptVariable] = {}
    for variable in variables:
        if _IDENTIFIER_PATTERN.fullmatch(variable.name) is None:
            raise TemplateValidationError(f"Invalid declared variable name: {variable.name}")
        if variable.name in declarations:
            raise TemplateValidationError(f"Duplicate variable declaration: {variable.name}")
        declarations[variable.name] = variable
    return declarations


def _validate_templates(
    templates: Sequence[str],
    declarations: Mapping[str, PromptVariable],
) -> set[str]:
    referenced_names: set[str] = set()
    for template in templates:
        referenced_names.update(_extract_placeholders(template))

    undeclared = referenced_names.difference(declarations)
    if undeclared:
        raise TemplateValidationError(f"Template references undeclared variable: {min(undeclared)}")

    for variable in declarations.values():
        if variable.required and variable.name not in referenced_names:
            raise TemplateValidationError(f"Required variable is not referenced: {variable.name}")
    return referenced_names


def _extract_placeholders(template: str) -> set[str]:
    names: set[str] = set()
    position = 0
    while position < len(template):
        opening = template.find("{{", position)
        closing = template.find("}}", position)

        if closing != -1 and (opening == -1 or closing < opening):
            raise TemplateValidationError("Template contains an orphaned closing delimiter")
        if opening == -1:
            break

        closing = template.find("}}", opening + 2)
        if closing == -1:
            raise TemplateValidationError("Template contains an unclosed placeholder")

        name = template[opening + 2 : closing].strip()
        if _IDENTIFIER_PATTERN.fullmatch(name) is None:
            raise TemplateValidationError("Template contains unsupported placeholder syntax")
        names.add(name)
        position = closing + 2
    return names


def _validate_values(
    declarations: Mapping[str, PromptVariable],
    referenced_names: set[str],
    params: Mapping[str, object] | None,
) -> dict[str, object]:
    supplied_values = dict(params or {})
    for name in supplied_values:
        if name not in declarations:
            raise UnexpectedVariableError(f"Unexpected variable: {name}")

    candidate_values: dict[str, object] = {}
    for name, declaration in declarations.items():
        if name in supplied_values:
            candidate_values[name] = supplied_values[name]
        elif declaration.default_value is not None:
            candidate_values[name] = _normalize_default(declaration)
        elif name in referenced_names:
            raise MissingVariableError(f"Missing variable: {name}")

    model = _create_validation_model(declarations)
    validation_error: Exception | None = None
    try:
        validated = model.model_validate(candidate_values)
    except Exception as error:
        validation_error = error
        validated = None
    if validation_error is not None:
        _raise_validation_error(validation_error)
        raise AssertionError("unreachable")

    if validated is None:
        raise AssertionError("unreachable")

    return {
        name: value
        for name, value in validated.model_dump().items()
        if value is not None or name in candidate_values
    }


def _create_validation_model(declarations: Mapping[str, PromptVariable]) -> type[BaseModel]:
    fields: dict[str, Any] = {}
    for name, declaration in declarations.items():
        annotation = _annotation_for(declaration)
        default: object = PydanticUndefined if declaration.required else None
        if not declaration.required:
            annotation = annotation | None  # type: ignore[operator]
        fields[name] = (annotation, default)
    return cast(
        type[BaseModel],
        create_model("PromptCompileParams", __config__=ConfigDict(extra="forbid"), **fields),
    )


def _annotation_for(declaration: PromptVariable) -> object:
    if declaration.var_type == "string":
        return StrictStr
    if declaration.var_type == "number":
        return StrictInt | StrictFloat
    if declaration.var_type == "boolean":
        return StrictBool
    if declaration.var_type == "json":
        return dict[str, Any] | list[Any]
    raise InvalidVariableTypeError(f"Unsupported variable type for: {declaration.name}")


def _normalize_default(declaration: PromptVariable) -> object:
    default = declaration.default_value
    if declaration.var_type == "string":
        if isinstance(default, str):
            return default
    elif declaration.var_type == "number":
        if isinstance(default, int | float) and not isinstance(default, bool):
            return default
        if isinstance(default, str):
            try:
                parsed = (
                    float(default) if any(marker in default for marker in ".eE") else int(default)
                )
            except ValueError:
                parsed = None
            if parsed is not None:
                return parsed
    elif declaration.var_type == "boolean":
        if isinstance(default, bool):
            return default
        if default == "true":
            return True
        if default == "false":
            return False
    elif declaration.var_type == "json":
        if isinstance(default, dict | list):
            return default
        if isinstance(default, str):
            try:
                parsed_json = json.loads(default)
            except json.JSONDecodeError:
                parsed_json = None
            if isinstance(parsed_json, dict | list):
                return parsed_json

    raise InvalidVariableTypeError(f"Invalid default value for variable: {declaration.name}")


def _raise_validation_error(error: Exception) -> None:
    errors = getattr(error, "errors", None)
    if not callable(errors):
        raise InvalidVariableTypeError("Invalid variable value")

    details = errors()
    if not details:
        raise InvalidVariableTypeError("Invalid variable value")
    detail = details[0]
    location = detail.get("loc", ())
    name = str(location[0]) if location else "unknown"
    error_type = str(detail.get("type", ""))
    if error_type == "missing":
        raise MissingVariableError(f"Missing variable: {name}")
    if error_type == "extra_forbidden":
        raise UnexpectedVariableError(f"Unexpected variable: {name}")
    raise InvalidVariableTypeError(f"Invalid value for variable: {name}")


def _render_template(template: str, values: Mapping[str, object]) -> str:
    rendered: list[str] = []
    position = 0
    while position < len(template):
        opening = template.find("{{", position)
        if opening == -1:
            rendered.append(template[position:])
            break
        closing = template.find("}}", opening + 2)
        rendered.append(template[position:opening])
        name = template[opening + 2 : closing].strip()
        rendered.append(_stringify_value(values[name]))
        position = closing + 2
    return "".join(rendered)


def _stringify_value(value: object) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)
