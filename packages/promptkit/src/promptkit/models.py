"""Typed representations of successful PromptKit registry responses."""

from datetime import datetime
from typing import Any

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
