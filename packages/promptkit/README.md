# PromptKit Python SDK

`promptkit` is a framework-agnostic, synchronous Python client for retrieving
published prompts from a PromptKit registry. It is read-only: it does not call
LLM providers, create or change prompts, cache responses, retry requests, or
follow redirects. It has no Django or Django REST Framework dependency.

## Install

Install the package from the repository subdirectory:

```bash
pip install "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
```

## Retrieve a prompt

Supply the registry URL and API key explicitly. Keep the API key in a secret
store or environment variable; do not place it in source code.

```python
import os

from promptkit import PromptKitClient

client = PromptKitClient(
    base_url="https://registry.example.com",
    api_key=os.environ["PROMPTKIT_API_KEY"],
)
prompt = client.fetch("support-reply", label="latest")

print(prompt.template_text)
```

Omit `label` to retrieve the prompt version currently on live. The SDK rejects
the `production` label, does not follow redirects, and accepts registry URLs
only over HTTPS (or loopback HTTP for local development).

## Compile a prompt locally

`RetrievedPrompt.compile()` validates and renders declared `{{ variable_name }}`
placeholders in your application process. It never sends supplied values to the
registry, calls an LLM provider, or evaluates values as another template.

```python
from promptkit import (
    InvalidVariableTypeError,
    MissingVariableError,
    TemplateValidationError,
    UnexpectedVariableError,
)

try:
    compiled = prompt.compile({"customer_name": "Ada"})
except MissingVariableError:
    # A referenced required value has neither a caller value nor a valid default.
    raise
except InvalidVariableTypeError:
    # A value or registry default does not match its declared type.
    raise
except UnexpectedVariableError:
    # The caller supplied a name not declared by the prompt.
    raise
except TemplateValidationError:
    # The retrieved template is malformed or inconsistent with its declarations.
    raise

print(compiled.content)
print(compiled.version)
```

Supported declared types are `string`, `number`, `boolean`, and JSON object or
array. A successful `CompiledPrompt` retains the source prompt slug, version,
label, and rendered ordered sections for later provider-specific formatting.

## Convert a compiled prompt for an LLM provider

PromptKit adapters only reshape an immutable `CompiledPrompt` into plain Python
dictionaries. They do not import provider SDKs, select a model, read credentials,
apply generation settings, or make an LLM request. Supply those caller-owned
arguments separately when invoking your provider client.

```python
from promptkit import GeminiAdapter, LiteLLMAdapter, OpenAIAdapter

gemini_args = GeminiAdapter.to_generate_content_args(compiled)
chat_args = OpenAIAdapter.to_chat_completions_args(compiled)
responses_args = OpenAIAdapter.to_responses_args(compiled)
litellm_args = LiteLLMAdapter.to_completion_args(compiled)
```

Gemini arguments contain ordered `contents` items using `user` or `model` roles
and one text `part` per compiled conversation section. Ordered system sections
are joined with `\n\n` under `config.system_instruction`; `config` is omitted
when no system section exists.

Chat Completions arguments contain one ordered `messages` item per compiled
section with its `system`, `user`, or `assistant` role. Responses arguments place
joined system text under `instructions` and ordered user/assistant items under
`input`. Repeated roles remain separate in every format.

All conversions reject duplicate section orders and roles other than exact
`system`, `user`, or `assistant` values with `AdapterConversionError`. A compiled
prompt without sections uses its aggregate content as one user item. Empty,
whitespace, multiline, Unicode, and placeholder-shaped text remain unchanged.

When a prompt contains only system sections, each method returns its target's
system-only arguments and logs exactly one `WARNING` containing only the source
slug, version, and label. The caller decides whether to add conversation content
or invoke the provider. Compiled prompt text is never written to that log.

LiteLLM arguments contain one ordered `{"role": "system"|"user"|"assistant",
"content": "..."}` item per compiled section under `messages`. PromptKit does
not install or import LiteLLM, select its required `model`, provide credentials,
set generation options, or call `litellm.completion`; the application supplies
those caller-owned values when it makes the request.
