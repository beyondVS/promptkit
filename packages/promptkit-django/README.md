# PromptKit Django Integration

`promptkit-django` configures and registers one read-only `PromptKitClient` for a
Django application lifecycle. It does not call LLMs, create or modify prompts, cache
responses, retry requests, or contact the registry at startup.

## Install

Install from this repository's package subdirectory:

```bash
uv pip install "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
```

The distribution resolves a compatible released `promptkit` package. It does not use
a sibling checkout or editable workspace dependency.

## Configure Django

Add the integration to `INSTALLED_APPS` and keep the API key in your host project's
secret store or environment variable:

```python
import os

INSTALLED_APPS = [
    # ...
    "promptkit_django",
]

PROMPTKIT = {
    "BASE_URL": "https://registry.example.com",
    "API_KEY": os.environ["PROMPTKIT_API_KEY"],
    "TIMEOUT": 10.0,
}
```

`BASE_URL` and `API_KEY` are required. `TIMEOUT` is optional and defaults to `10.0`.
Only these uppercase keys are accepted. Missing, blank, wrongly typed, unsafe, or
unknown settings fail application startup and report setting names without exposing
the API-key value.

## Access the registered client

```python
from promptkit_django import get_client

prompt = get_client().fetch("support-reply")
```

`get_client()` returns the single client registered during Django startup. It never
constructs a client lazily and raises `PromptKitDjangoNotInitializedError` when the
integration is absent or initialization has not completed.
