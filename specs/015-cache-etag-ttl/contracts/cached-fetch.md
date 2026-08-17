# Cached Fetch and Conditional Retrieval Contract

## Django integration public operations

### `fetch_cached(slug, *, label=None)`

Returns the same `RetrievedPrompt` shape and raises the same registry/domain errors as an uncached lookup. It is the only cache-aware public entry point.

- It reads and writes only the host Django default cache backend.
- Fresh valid entries return without a registry request.
- Stale retained entries revalidate using their ETag.
- A matching 304 returns the cached prompt and refreshes both windows.
- A changed 200 replaces the entry atomically.
- Missing, malformed, cache-failing, expired-retention, and ETag-less entries cause a full registry lookup.
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

The core SDK adds a public validator-aware operation for the Django integration. It sends `If-None-Match` only when given a valid stored ETag, exposes a typed 304 not-modified outcome without JSON parsing, and validates an ETag on a full 200 response. It uses the same path construction, authentication, timeout, and error mapping as the existing client. `PromptKitClient.fetch()` is not redefined or made cache-aware.
