"""Provider argument adapters for immutable compiled prompts."""

import logging
from typing import Literal, TypedDict

from promptkit.exceptions import AdapterConversionError
from promptkit.models import CompiledPrompt, CompiledPromptSection

logger = logging.getLogger(__name__)


class GeminiTextPart(TypedDict):
    """One plain-text Gemini content part."""

    text: str


class GeminiContent(TypedDict):
    """One Gemini conversation content item."""

    role: Literal["user", "model"]
    parts: list[GeminiTextPart]


class GeminiConfig(TypedDict):
    """Gemini configuration owned by prompt conversion."""

    system_instruction: str


class GeminiGenerateContentArgs(TypedDict, total=False):
    """Plain arguments for ``google-genai`` generate_content."""

    contents: list[GeminiContent]
    config: GeminiConfig


class OpenAIChatMessage(TypedDict):
    """One OpenAI Chat Completions message."""

    role: Literal["system", "user", "assistant"]
    content: str


class OpenAIChatCompletionsArgs(TypedDict):
    """Plain arguments for OpenAI Chat Completions."""

    messages: list[OpenAIChatMessage]


class OpenAIResponsesInputItem(TypedDict):
    """One OpenAI Responses conversation input item."""

    role: Literal["user", "assistant"]
    content: str


class OpenAIResponsesArgs(TypedDict, total=False):
    """Plain arguments for the OpenAI Responses API."""

    instructions: str
    input: list[OpenAIResponsesInputItem]


def _partition_sections(
    prompt: CompiledPrompt,
) -> tuple[list[CompiledPromptSection], list[str], list[CompiledPromptSection]]:
    ordered_sections = _resolve_sections(prompt)
    system_texts = [section.content for section in ordered_sections if section.role == "system"]
    conversation = [section for section in ordered_sections if section.role != "system"]
    if ordered_sections and not conversation:
        logger.warning(
            "System-only compiled prompt converted; caller owns provider-call viability "
            "(slug=%r, version=%d, label=%r)",
            prompt.slug,
            prompt.version,
            prompt.label,
        )
    return ordered_sections, system_texts, conversation


def _resolve_sections(prompt: CompiledPrompt) -> list[CompiledPromptSection]:
    sections = list(prompt.sections)
    if not sections:
        return [CompiledPromptSection(role="user", order=0, content=prompt.content)]

    seen_orders: set[int] = set()
    for section in sections:
        if section.role not in {"system", "user", "assistant"}:
            raise AdapterConversionError(f"Unsupported section role: {section.role!r}")
        if section.order in seen_orders:
            raise AdapterConversionError(f"Duplicate section order: {section.order}")
        seen_orders.add(section.order)
    return sorted(sections, key=lambda section: section.order)


class GeminiAdapter:
    """Convert compiled prompts to Google Gen AI generate-content arguments."""

    @staticmethod
    def to_generate_content_args(prompt: CompiledPrompt) -> GeminiGenerateContentArgs:
        """Return plain ``google-genai`` arguments without invoking a provider."""
        _, system_texts, conversation = _partition_sections(prompt)
        result = GeminiGenerateContentArgs()
        if conversation:
            result["contents"] = [
                {
                    "role": "user" if section.role == "user" else "model",
                    "parts": [{"text": section.content}],
                }
                for section in conversation
            ]
        if system_texts:
            result["config"] = {"system_instruction": "\n\n".join(system_texts)}
        return result


class OpenAIAdapter:
    """Convert compiled prompts to either supported OpenAI input contract."""

    @staticmethod
    def to_chat_completions_args(prompt: CompiledPrompt) -> OpenAIChatCompletionsArgs:
        """Return plain Chat Completions arguments without invoking OpenAI."""
        ordered_sections, _, _ = _partition_sections(prompt)
        messages: list[OpenAIChatMessage] = []
        for section in ordered_sections:
            if section.role == "system":
                role: Literal["system", "user", "assistant"] = "system"
            elif section.role == "user":
                role = "user"
            else:
                role = "assistant"
            messages.append({"role": role, "content": section.content})
        return {"messages": messages}

    @staticmethod
    def to_responses_args(prompt: CompiledPrompt) -> OpenAIResponsesArgs:
        """Return plain Responses API arguments without invoking OpenAI."""
        _, system_texts, conversation = _partition_sections(prompt)
        result = OpenAIResponsesArgs()
        if system_texts:
            result["instructions"] = "\n\n".join(system_texts)
        if conversation:
            result["input"] = [
                {
                    "role": "user" if section.role == "user" else "assistant",
                    "content": section.content,
                }
                for section in conversation
            ]
        return result
