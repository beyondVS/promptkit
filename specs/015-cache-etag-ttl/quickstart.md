# Quickstart: Cache and ETag Consistency Validation

## Prerequisites

- Activate the repository environment with `uv sync`.
- Configure a Django `CACHES["default"]` backend. A LocMem backend is sufficient for local verification; production keeps the host application's existing backend.
- Configure the registered PromptKit integration with `BASE_URL`, `API_KEY`, and an optional `CACHE_TTL` value. Keep credentials in environment-backed settings.
- Start a registry with a published on-live prompt and the integration installed in `INSTALLED_APPS`.

## Configuration check

Set `CACHE_TTL` to `60` and start Django. Verify that startup succeeds and that the integration uses the host default cache backend. Then verify each invalid value fails startup by name without revealing the API key: `True`, `-1`, `NaN`, a string, and an unknown key. Set `CACHE_TTL` to `0` and verify cached helper calls make normal full registry requests without storing entries.

## Cached lookup check

1. Call the cache-aware helper for one prompt with an omitted label. Confirm a 200 response includes an ETag and a cache entry is created.
2. Repeat the call before 60 seconds. Confirm the helper returns the same prompt without a registry request.
3. Advance past the fresh window but remain inside the second retention window. Confirm the helper sends `If-None-Match`; an unchanged prompt yields 304 with no body and returns the retained prompt as fresh.
4. Change a serialized prompt field, move the on-live version, or reassign a label. Repeat step 3 and confirm a full 200 response with a different ETag atomically replaces the entry.
5. Advance beyond both windows. Confirm the next call performs a full lookup without relying on a removed ETag.
6. Return a successful conditional response without a usable ETag. Confirm the helper raises `InvalidResponseError` and does not cache the response, while the existing uncached `fetch()` behavior remains unchanged.

## Invalidation and safety check

1. Cache two labels for one prompt and one label for another prompt.
2. Clear the first prompt and verify both of its labels are refreshed on their next lookup while the unrelated prompt remains a fresh cache hit.
3. Clear all PromptKit cache entries and verify every PromptKit lookup is refreshed without disturbing a non-PromptKit key in the same Django cache backend.
4. Simulate malformed records and backend exceptions. Verify each case falls back to normal registry behavior and never returns stale data on a registry failure.
5. Reassign a label, remove on-live publication, delete a prompt, and deny access after freshness expires. Verify the first stale lookup returns the registry's current representation or error without stale or cross-label fallback.

## Automated verification

Run the focused tests during implementation:

```text
uv run pytest tests/promptkit/unit/test_client.py
uv run pytest tests/promptkit_django/unit/test_configuration.py tests/promptkit_django/unit/test_cache.py
uv run pytest tests/promptkit_django/integration/test_django_lifecycle.py
uv run pytest apps/server/prompts/tests/test_read_only_api.py
```

Then run the repository quality gates:

```text
uv run ruff check
uv run ruff format --check
uv run mypy .
uv run pytest
```
