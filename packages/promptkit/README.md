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
