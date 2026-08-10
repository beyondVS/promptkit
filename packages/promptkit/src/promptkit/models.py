"""Typed representations of successful PromptKit registry responses."""

from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field


class _RegistryModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class PromptCategory(_RegistryModel):
    name: str
    slug: str


class PromptVariable(_RegistryModel):
    name: str
    var_type: str
    required: bool
    default_value: Any | None
    description: str


class PromptSection(_RegistryModel):
    role: str
    order: int = Field(ge=0)
    content: str


class CompiledPromptSection(BaseModel):
    """One rendered prompt section with its original provider-neutral role."""

    model_config = ConfigDict(frozen=True)

    role: str
    order: int = Field(ge=0)
    content: str


class CompiledPrompt(BaseModel):
    """A locally rendered prompt with source version traceability."""

    model_config = ConfigDict(frozen=True)

    slug: str = Field(min_length=1)
    version: int = Field(gt=0)
    label: str | None
    content: str
    sections: tuple[CompiledPromptSection, ...]


class RetrievedPrompt(_RegistryModel):
    slug: str = Field(min_length=1)
    name: str
    description: str
    category: PromptCategory
    version: int = Field(gt=0)
    version_status: str
    is_on_live: bool
    label: str | None
    template_text: str
    variables: list[PromptVariable]
    sections: list[PromptSection]
    created_at: datetime

    def compile(self, params: Mapping[str, object] | None = None) -> "CompiledPrompt":
        """Validate and render this retrieved prompt locally."""
        from promptkit.compiler import compile_prompt

        return cast(CompiledPrompt, compile_prompt(self, params))
