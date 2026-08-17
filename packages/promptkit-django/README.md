# PromptKit Django Integration

`promptkit-django` configures and registers one read-only `PromptKitClient` for a
Django application lifecycle. It does not call LLMs, create or modify prompts, retry
requests, or contact the registry at startup. Cache reuse is available only through an
explicit helper and uses the host application's Django default cache backend.

## Install

The core SDK is not published to a package index. Install both packages from the
repository's default branch in one command:

```bash
uv pip install \
  "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit" \
  "promptkit-django @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
```

Installing only `promptkit-django` makes the dependency resolver search its configured
package indexes for `promptkit`, where it is not currently available. Supplying both
Git subdirectories lets the explicitly installed core SDK satisfy the
`promptkit>=0.1,<0.2` dependency. Because these URLs track the default branch, install
or upgrade both packages together to keep their versions compatible.

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
    "CACHE_TTL": 60.0,
}
```

`BASE_URL` and `API_KEY` are required. `TIMEOUT` is optional and defaults to `10.0`.
`CACHE_TTL` is optional, defaults to `60.0` seconds, and must be a finite non-negative
number. A positive TTL keeps a prompt fresh for that duration and retains it for an
equal validator-revalidation window; `0` disables PromptKit cache reads and writes.
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

## Opt-in cached lookup

Configure the host application's standard `CACHES["default"]` backend, then import the
cache-aware helper explicitly:

```python
from promptkit_django import clear_prompt_cache, fetch_cached

prompt = fetch_cached("support-reply", label="latest")
clear_prompt_cache("support-reply")  # invalidates every cached label for this prompt
clear_prompt_cache()  # invalidates PromptKit-owned entries only
```

`fetch_cached()` returns the same `RetrievedPrompt` as an uncached lookup. It uses an
ETag to revalidate once freshness expires and never serves stale data after a registry
error. `get_client().fetch()` remains uncached. Cache keys never include API keys or
authorization headers, and cache failures fall back to the registry whenever possible.
