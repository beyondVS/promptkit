# Data Model: Cache and ETag Consistency

## Configuration

### `PROMPTKIT.CACHE_TTL`

| Field | Type | Default | Validation | Meaning |
|-------|------|---------|------------|---------|
| `CACHE_TTL` | finite numeric seconds | `60.0` | Must be zero or greater; booleans, negative values, non-finite values, non-numbers, and unknown keys are rejected at AppConfig startup | Freshness duration for `fetch_cached()` |

`CACHE_TTL=0` disables PromptKit cache reads and writes. The existing `BASE_URL`, `API_KEY`, and `TIMEOUT` fields retain their current validation and semantics.

## AppConfig lifecycle state

| Field | Type | Lifecycle | Purpose |
|-------|------|-----------|---------|
| `client` | `PromptKitClient` | Set once by `ready()` | Existing registered uncached core client |
| `client_settings` | validated PromptKit settings | Set with `client` by `ready()` | Supplies canonical non-secret base URL and cache TTL to the Django-only helper |

AppConfig is the sole lifecycle owner. `get_client()` continues to expose only `client`; it does not construct clients or enable caching.

## Cached prompt entry

| Field | Type | Validation / purpose |
|-------|------|----------------------|
| `prompt` | serialized `RetrievedPrompt` payload | Must validate as the current SDK response model before use |
| `etag` | non-empty quoted opaque string | Stored only when supplied on a successful registry response |
| `fresh_until` | UTC epoch timestamp | Entry may be returned without registry contact only before this value |
| `identity_version` | integer/string namespace version | Reject incompatible record formats as cache misses |

For a positive TTL, storage timeout is twice `CACHE_TTL`; the second half is a revalidation-only state. A cached record is never served during that state unless a matching registry 304 refreshes it.

## Cache identity and generation markers

| Entity | Inputs | Stored data | Scope |
|--------|--------|-------------|-------|
| Cache identity | canonical base URL, slug, label state/value | one-way digest only | One resolved registry prompt |
| Global generation | PromptKit namespace | opaque token | Invalidates every PromptKit entry logically |
| Prompt generation | base URL + slug digest | opaque token | Invalidates every cached label for one prompt logically |

Credentials, authorization headers, category, raw base URL, and prompt contents are not included in cache keys. Generation changes create new derived cache keys; prior physical entries expire naturally after their storage timeout.

## Conditional retrieval result

| Field | Type | Meaning |
|-------|------|---------|
| `not_modified` | boolean | Whether the registry confirmed a supplied validator with HTTP 304 |
| `prompt` | `RetrievedPrompt` or absent | Present only for a full successful 200 response |
| `etag` | non-empty quoted opaque string | Validator received from the registry |

The result is produced only by the new core SDK conditional operation. Existing `PromptKitClient.fetch()` continues to return `RetrievedPrompt` for 2xx results and keeps its present error behavior for all redirects.
