# Cached Fetch and Conditional Retrieval Contract

## Django integration public operations

### `fetch_cached(slug, *, label=None)`

Returns the same `RetrievedPrompt` shape and raises the same registry/domain errors as an uncached lookup. It is the only cache-aware public entry point.

- It reads and writes only the host Django default cache backend.
- Fresh valid entries return without a registry request.
- Stale retained entries revalidate using their ETag.
- A matching 304 returns the cached prompt and refreshes both windows.
- A changed 200 replaces the entry atomically.
- Missing, malformed, cache-failing, expired-retention, and ETag-less cached entries cause a full registry lookup; a successful conditional registry response without a usable ETag raises `InvalidResponseError` and is not cached.
- Registry errors and cache backend failures never return stale prompt data.

### `clear_prompt_cache(slug=None)`

- With a `slug`, logically invalidates every cached label resolution for that prompt and registry address.
- With no value, logically invalidates all PromptKit-owned cache entries.
- It must not clear unrelated application cache keys.

`get_client().fetch()` remains uncached and unchanged.

## Configuration contract

The strict startup configuration is extended as follows:

```text
PROMPTKIT = {
  BASE_URL: required non-empty safe URL,
  API_KEY: required non-empty secret,
  TIMEOUT: optional positive finite number (default 10.0),
  CACHE_TTL: optional finite number >= 0 (default 60.0),
}
```

Unknown keys fail startup. Validation errors name affected keys but never render the API key or another credential value.

## HTTP conditional GET contract

### Successful full response

```text
GET /api/v1/prompts/<slug>/?label=<label>
→ 200 OK
ETag: "<opaque-validator>"
Content-Type: application/json
<existing RetrievedPrompt JSON body>
```

### Matching conditional response

```text
GET /api/v1/prompts/<slug>/?label=<label>
If-None-Match: "<opaque-validator>"
→ 304 Not Modified
ETag: "<opaque-validator>"
<no body>
```

The server applies weak comparison for valid validator lists and wildcard values as defined by HTTP conditional retrieval. It ignores malformed conditional values rather than matching partial text. Authentication and ordinary 4xx/5xx outcomes remain non-conditional and never become 304.

## Core SDK conditional operation

```text
PromptKitClient.fetch_conditional(
  slug: str,
  *,
  label: str | None = None,
  etag: str | None = None,
) -> ConditionalFetchResult
```

`ConditionalFetchResult` has the following invariant:

- HTTP 200: `not_modified=False`, `prompt` contains a validated `RetrievedPrompt`, and `etag` contains the response validator.
- HTTP 304: `not_modified=True`, `prompt=None`, and `etag` contains the confirmed response validator.

The operation sends `If-None-Match` only when given a valid stored ETag, exposes a 304 outcome without JSON parsing, and raises `InvalidResponseError` when a successful 200 or 304 response lacks a usable ETag or violates the result invariant. It uses the same path construction, authentication, timeout, and error mapping as the existing client. `PromptKitClient.fetch()` is not redefined or made cache-aware.
