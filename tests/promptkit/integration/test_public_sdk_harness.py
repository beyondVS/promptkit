"""Public API integration harness for the independently installable PromptKit SDK."""

from typing import Any

import httpx
import promptkit
import pytest
from pydantic import ValidationError

PUBLIC_CONTRACTS = {
    "AdapterConversionError": "test_public_exception_hierarchy_and_failure_paths",
    "AuthenticationError": "test_public_exception_hierarchy_and_failure_paths",
    "CommunicationError": "test_public_exception_hierarchy_and_failure_paths",
    "CompiledPrompt": "test_public_model_contracts",
    "CompiledPromptSection": "test_public_model_contracts",
    "GeminiAdapter": "test_retrieval_compilation_and_provider_conversion_journey",
    "GeminiConfig": "test_public_typed_argument_contracts",
    "GeminiContent": "test_public_typed_argument_contracts",
    "GeminiGenerateContentArgs": "test_public_typed_argument_contracts",
    "GeminiTextPart": "test_public_typed_argument_contracts",
    "InvalidConfigurationError": "test_public_exception_hierarchy_and_failure_paths",
    "InvalidLabelError": "test_public_exception_hierarchy_and_failure_paths",
    "InvalidRequestError": "test_public_exception_hierarchy_and_failure_paths",
    "InvalidResponseError": "test_public_exception_hierarchy_and_failure_paths",
    "InvalidVariableTypeError": "test_public_exception_hierarchy_and_failure_paths",
    "LabelNotFoundError": "test_public_exception_hierarchy_and_failure_paths",
    "LiteLLMAdapter": "test_retrieval_compilation_and_provider_conversion_journey",
    "LiteLLMChatMessage": "test_public_typed_argument_contracts",
    "LiteLLMCompletionArgs": "test_public_typed_argument_contracts",
    "MissingVariableError": "test_public_exception_hierarchy_and_failure_paths",
    "NoDeployableVersionError": "test_public_exception_hierarchy_and_failure_paths",
    "OpenAIAdapter": "test_retrieval_compilation_and_provider_conversion_journey",
    "OpenAIChatCompletionsArgs": "test_public_typed_argument_contracts",
    "OpenAIChatMessage": "test_public_typed_argument_contracts",
    "OpenAIResponsesArgs": "test_public_typed_argument_contracts",
    "OpenAIResponsesInputItem": "test_public_typed_argument_contracts",
    "PromptCategory": "test_public_model_contracts",
    "PromptKitClient": "test_retrieval_compilation_and_provider_conversion_journey",
    "PromptKitError": "test_public_exception_hierarchy_and_failure_paths",
    "PromptNotFoundError": "test_public_exception_hierarchy_and_failure_paths",
    "PromptSection": "test_public_model_contracts",
    "PromptVariable": "test_public_model_contracts",
    "RateLimitError": "test_public_exception_hierarchy_and_failure_paths",
    "RedirectError": "test_public_exception_hierarchy_and_failure_paths",
    "RetrievedPrompt": "test_public_model_contracts",
    "TemplateValidationError": "test_public_exception_hierarchy_and_failure_paths",
    "UnexpectedVariableError": "test_public_exception_hierarchy_and_failure_paths",
}


def prompt_payload(**overrides: object) -> dict[str, Any]:
    """Return a valid registry response fixture without external state."""
    payload: dict[str, Any] = {
        "slug": "support-reply",
        "name": "Support reply",
        "description": "A customer support response.",
        "category": {"name": "Support", "slug": "support"},
        "version": 4,
        "version_status": "published",
        "is_on_live": True,
        "label": "latest",
        "template_text": "Hello {{ customer_name }}!",
        "variables": [
            {
                "name": "customer_name",
                "var_type": "string",
                "required": True,
                "default_value": None,
                "description": "Customer name",
            }
        ],
        "sections": [
            {"role": "system", "order": 0, "content": "Be helpful to {{ customer_name }}."},
            {"role": "user", "order": 1, "content": "Hello {{ customer_name }}!"},
        ],
        "created_at": "2026-08-07T00:00:00Z",
    }
    payload.update(overrides)
    return payload


def mock_client(handler: Any) -> promptkit.PromptKitClient:
    """Build a public client that uses a local in-memory HTTP transport."""
    return promptkit.PromptKitClient(
        "https://registry.example.com",
        "test-api-key",
        transport=httpx.MockTransport(handler),
    )


def assert_public_coverage(exported: set[str], covered: set[str]) -> None:
    """Fail with both directions of a public-inventory coverage mismatch."""
    missing = sorted(exported - covered)
    stale = sorted(covered - exported)
    if missing or stale:
        raise AssertionError(
            f"public export coverage mismatch: missing={missing!r}, stale={stale!r}"
        )


def test_public_inventory_has_complete_two_way_coverage_map() -> None:
    """Prevent declared public exports and explicit contract coverage from drifting."""
    exported = set(promptkit.__all__)
    covered = set(PUBLIC_CONTRACTS)

    assert_public_coverage(exported, covered)
    for export in sorted(exported):
        assert hasattr(promptkit, export), f"package-root export is missing: {export}"


def test_public_typed_argument_contracts() -> None:
    """Keep all typed-dictionary argument contracts importable from the package root."""
    typed_contracts = (
        promptkit.GeminiTextPart,
        promptkit.GeminiContent,
        promptkit.GeminiConfig,
        promptkit.GeminiGenerateContentArgs,
        promptkit.OpenAIChatMessage,
        promptkit.OpenAIChatCompletionsArgs,
        promptkit.OpenAIResponsesInputItem,
        promptkit.OpenAIResponsesArgs,
        promptkit.LiteLLMChatMessage,
        promptkit.LiteLLMCompletionArgs,
    )

    for contract in typed_contracts:
        assert "__annotations__" in vars(contract)

    compiled = promptkit.CompiledPrompt(
        slug="typed-contracts",
        version=1,
        label=None,
        content="hello",
        sections=(promptkit.CompiledPromptSection(role="user", order=0, content="hello"),),
    )
    assert promptkit.LiteLLMAdapter.to_completion_args(compiled) == {
        "messages": [{"role": "user", "content": "hello"}]
    }


def test_public_model_contracts() -> None:
    """Validate public model boundaries, mutability, and source metadata preservation."""
    with pytest.raises(ValidationError):
        promptkit.CompiledPrompt(
            slug="",
            version=1,
            label=None,
            content="hello",
            sections=(),
        )
    section = promptkit.CompiledPromptSection(role="user", order=0, content="hello")
    compiled = promptkit.CompiledPrompt(
        slug="support-reply",
        version=4,
        label="latest",
        content="hello",
        sections=(section,),
    )
    with pytest.raises(ValidationError):
        compiled.slug = "changed"
    with pytest.raises(ValidationError):
        section.content = "changed"

    category = promptkit.PromptCategory(name="Support", slug="support")
    category.name = "Customer support"
    variable = promptkit.PromptVariable(
        name="customer_name",
        var_type="string",
        required=True,
        default_value=None,
        description="Customer name",
    )
    source_section = promptkit.PromptSection(role="user", order=0, content="Hello")
    retrieved = promptkit.RetrievedPrompt.model_validate(prompt_payload())

    assert category.name == "Customer support"
    assert variable.name == "customer_name"
    assert source_section.content == "Hello"
    assert (retrieved.slug, retrieved.version, retrieved.label) == (
        "support-reply",
        4,
        "latest",
    )
    assert retrieved.category.slug == "support"
    assert retrieved.sections[0].order == 0


def test_retrieval_compilation_and_provider_conversion_journey() -> None:
    """Exercise each public journey stage with explicit failure diagnostics."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=prompt_payload())

    retrieved = mock_client(handler).fetch("support-reply")
    assert len(requests) == 1, "retrieval journey did not issue exactly one local request"
    assert requests[0].headers["X-PromptKit-Api-Key"] == "test-api-key", (
        "retrieval journey did not authenticate with the configured API key"
    )

    compiled = retrieved.compile({"customer_name": "Ada"})
    assert compiled.sections[0].content == "Be helpful to Ada.", (
        "compilation journey did not render the system section"
    )
    assert compiled.sections[1].content == "Hello Ada!", (
        "compilation journey did not render the user section"
    )
    assert promptkit.GeminiAdapter.to_generate_content_args(compiled) == {
        "contents": [{"role": "user", "parts": [{"text": "Hello Ada!"}]}],
        "config": {"system_instruction": "Be helpful to Ada."},
    }, "Gemini adapter journey did not preserve compiled content"
    assert promptkit.OpenAIAdapter.to_chat_completions_args(compiled) == {
        "messages": [
            {"role": "system", "content": "Be helpful to Ada."},
            {"role": "user", "content": "Hello Ada!"},
        ]
    }, "OpenAI Chat Completions journey did not preserve compiled content"
    assert promptkit.OpenAIAdapter.to_responses_args(compiled) == {
        "instructions": "Be helpful to Ada.",
        "input": [{"role": "user", "content": "Hello Ada!"}],
    }, "OpenAI Responses journey did not preserve compiled content"
    assert promptkit.LiteLLMAdapter.to_completion_args(compiled) == {
        "messages": [
            {"role": "system", "content": "Be helpful to Ada."},
            {"role": "user", "content": "Hello Ada!"},
        ]
    }, "LiteLLM adapter journey did not preserve compiled content"


@pytest.mark.parametrize(
    ("status_code", "body", "error_type"),
    [
        (401, {}, promptkit.AuthenticationError),
        (429, {}, promptkit.RateLimitError),
        (302, {}, promptkit.RedirectError),
        (404, {}, promptkit.PromptNotFoundError),
        (404, {"error": "label_not_found"}, promptkit.LabelNotFoundError),
        (404, {"error": "no_deployable_version"}, promptkit.NoDeployableVersionError),
    ],
    ids=[
        "authentication",
        "rate-limit",
        "redirect",
        "prompt-not-found",
        "label-not-found",
        "no-deployable-version",
    ],
)
def test_public_http_failure_journey(
    status_code: int, body: dict[str, str], error_type: type[promptkit.PromptKitError]
) -> None:
    """Expose the documented public HTTP failure mapping without external I/O."""
    with pytest.raises(error_type):
        mock_client(lambda request: httpx.Response(status_code, json=body)).fetch("support-reply")


@pytest.mark.parametrize(
    ("journey", "action", "error_type"),
    [
        (
            "client-configuration",
            lambda: promptkit.PromptKitClient("http://registry.example.com", "test-api-key"),
            promptkit.InvalidConfigurationError,
        ),
        (
            "invalid-request",
            lambda: mock_client(lambda request: httpx.Response(200, json={})).fetch(""),
            promptkit.InvalidRequestError,
        ),
        (
            "invalid-label",
            lambda: mock_client(lambda request: httpx.Response(200, json={})).fetch(
                "support-reply", label="production"
            ),
            promptkit.InvalidLabelError,
        ),
        (
            "communication",
            lambda: mock_client(
                lambda request: (_ for _ in ()).throw(
                    httpx.ConnectError("offline", request=request)
                )
            ).fetch("support-reply"),
            promptkit.CommunicationError,
        ),
        (
            "invalid-response",
            lambda: mock_client(lambda request: httpx.Response(200, content=b"not-json")).fetch(
                "support-reply"
            ),
            promptkit.InvalidResponseError,
        ),
        (
            "missing-variable",
            lambda: promptkit.RetrievedPrompt.model_validate(prompt_payload()).compile(),
            promptkit.MissingVariableError,
        ),
        (
            "invalid-variable-type",
            lambda: promptkit.RetrievedPrompt.model_validate(prompt_payload()).compile(
                {"customer_name": 7}
            ),
            promptkit.InvalidVariableTypeError,
        ),
        (
            "unexpected-variable",
            lambda: promptkit.RetrievedPrompt.model_validate(prompt_payload()).compile(
                {"customer_name": "Ada", "extra": "secret-value"}
            ),
            promptkit.UnexpectedVariableError,
        ),
        (
            "template-validation",
            lambda: promptkit.RetrievedPrompt.model_validate(
                prompt_payload(template_text="Hello {{ customer_name")
            ).compile({"customer_name": "Ada"}),
            promptkit.TemplateValidationError,
        ),
        (
            "adapter-conversion",
            lambda: promptkit.LiteLLMAdapter.to_completion_args(
                promptkit.CompiledPrompt(
                    slug="support-reply",
                    version=1,
                    label=None,
                    content="secret-prompt-text",
                    sections=(
                        promptkit.CompiledPromptSection(
                            role="tool", order=0, content="secret-prompt-text"
                        ),
                    ),
                )
            ),
            promptkit.AdapterConversionError,
        ),
    ],
    ids=lambda case: str(case),
)
def test_public_local_failure_journey(
    journey: str, action: Any, error_type: type[promptkit.PromptKitError]
) -> None:
    """Expose each documented local failure while keeping confidential values out of errors."""
    api_key = "test-api-key"
    secret = "secret-value"
    prohibited_prompt_text = "secret-prompt-text"

    with pytest.raises(error_type) as raised:
        action()

    message = str(raised.value)
    assert journey, "failure journey must have a diagnostic identifier"
    assert api_key not in message
    assert secret not in message
    assert prohibited_prompt_text not in message


def test_public_exception_hierarchy_and_failure_paths() -> None:
    """Keep every public exception rooted in PromptKitError and explicitly covered."""
    errors = (
        promptkit.AdapterConversionError,
        promptkit.AuthenticationError,
        promptkit.CommunicationError,
        promptkit.InvalidConfigurationError,
        promptkit.InvalidLabelError,
        promptkit.InvalidRequestError,
        promptkit.InvalidResponseError,
        promptkit.InvalidVariableTypeError,
        promptkit.LabelNotFoundError,
        promptkit.MissingVariableError,
        promptkit.NoDeployableVersionError,
        promptkit.PromptNotFoundError,
        promptkit.RateLimitError,
        promptkit.RedirectError,
        promptkit.TemplateValidationError,
        promptkit.UnexpectedVariableError,
    )

    assert issubclass(promptkit.InvalidLabelError, promptkit.InvalidRequestError)
    assert all(issubclass(error, promptkit.PromptKitError) for error in errors)


def test_public_export_drift_diagnostics_name_missing_and_stale_symbols() -> None:
    """Ensure both directions of the coverage-map comparison name the mismatch."""
    exported = {"PromptKitClient", "LiteLLMAdapter"}
    covered = {"PromptKitClient", "StaleExport"}

    with pytest.raises(AssertionError) as raised:
        assert_public_coverage(exported, covered)

    assert "LiteLLMAdapter" in str(raised.value)
    assert "StaleExport" in str(raised.value)
