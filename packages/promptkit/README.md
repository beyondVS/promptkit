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
