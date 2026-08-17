# Research: Cache and ETag Consistency

## Django cache ownership

**Decision**: The integration uses `django.core.cache.cache`, which is the host application's configured `CACHES["default"]` backend. It does not introduce a cache backend setting, alias, package dependency, or fallback cache.

**Rationale**: The host application owns deployment-specific cache selection and credentials. Django's cache API supplies the portable `get`, `set`, and `delete` operations needed by this feature, so the integration works with the application's existing cache backend.

**Alternatives considered**:

- A PromptKit-specific backend or alias: rejected because it duplicates host configuration and adds an unnecessary deployment dependency.
- Core SDK local cache: rejected because it violates the framework-independent core boundary and the clarified opt-in Django-only scope.

## TTL and revalidation retention

**Decision**: Add `CACHE_TTL` to the strict `PROMPTKIT` mapping, defaulting to 60 seconds. AppConfig validates and retains the value during startup. A value of zero disables cache storage and reuse; negative, boolean, non-finite, non-numeric, and unknown values fail startup without exposing the API key. For a positive TTL, one cache record is stored for `2 * CACHE_TTL`: it is fresh for the first TTL and is revalidation-only for the second TTL.

**Rationale**: A cache backend removes an entry when its storage timeout ends. Keeping one additional bounded window preserves the ETag required for the first post-freshness conditional request while adding no second public configuration setting. A stale record is never returned until the registry confirms it with 304.

**Alternatives considered**:

- Store only for `CACHE_TTL`: rejected because the ETag is gone when revalidation is required.
- Add a configurable retention setting: rejected as unnecessary configuration for the initial feature.
- Retain indefinitely: rejected because it leaves cache-space growth unbounded.

## Cache identity and invalidation

**Decision**: Create non-secret keys from a canonical registry base URL, globally unique prompt slug, and an omitted-versus-explicit label discriminator. Hash that canonical identity and prefix it with a versioned PromptKit namespace. Use global and per-prompt generation tokens in derived keys for logical all-entry and prompt-entry invalidation; never call `cache.clear()` or require backend-specific key scanning.

**Rationale**: The identity prevents shared-backend collisions between registries and label resolutions without placing API keys in storage. Generation tokens make backend-agnostic invalidation possible while preserving unrelated application cache keys and all label variants for a selected prompt.

**Alternatives considered**:

- `slug + label` only: rejected because two registries sharing a backend can collide.
- Include category: rejected because prompt slugs are globally unique and category is not a read API input.
- Pattern deletion or `cache.clear()`: rejected because Django cache backends do not share a portable pattern-delete API and `clear()` harms unrelated cache users.

## Conditional HTTP contract

**Decision**: The registry serializes the selected successful response, builds a canonical representation digest, and returns it as a quoted opaque ETag. It applies HTTP `If-None-Match` comparison only after successful authentication, lookup, and label/on-live resolution. Matching GET requests receive 304 with the ETag and no body; non-matches receive 200 with the same representation and ETag. The core SDK adds `PromptKitClient.fetch_conditional(slug, *, label=None, etag=None) -> ConditionalFetchResult` to distinguish 304 from redirects; the existing `fetch()` behavior remains unchanged.

**Rationale**: Building the ETag from the actual serialized payload makes every client-observable change invalidate it, including metadata, category, selected label, version, variables, and sections. A core transport operation avoids the Django helper reaching into private HTTPX client state and preserves existing public behavior.

**Alternatives considered**:

- Global conditional-GET middleware: rejected because it can affect unrelated views and may derive tags from response bytes after view execution rather than the selected prompt representation.
- Django helper access to `PromptKitClient._client`: rejected because it bypasses SDK error mapping and relies on a private implementation detail.
- Treat 304 as an existing redirect: rejected because cached revalidation requires a typed not-modified outcome.

## Concurrency and failure policy

**Decision**: Cache entries are serialized as one validated record and written with one cache operation. The helper treats malformed data and cache exceptions as cache misses, preserves registry results and exceptions, and verifies generation tokens again before a write so an in-flight request cannot revive a logically invalidated entry.

**Rationale**: A single record prevents prompt/ETag mismatch. Cache availability must not change prompt resolution, authentication, or no-fallback semantics.

**Alternatives considered**:

- Cache errors as application failures: rejected because cache is an optimization.
- Stale-on-error: rejected by the feature specification's explicit consistency rule.
