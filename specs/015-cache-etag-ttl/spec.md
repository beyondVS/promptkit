# Feature Specification: Cache and ETag Consistency

**Feature Branch**: `015-cache-etag-ttl`

**Created**: 2026-08-17

**Status**: Draft

**Input**: User description: "Day 15 (1h): Django Cache 기반 캐싱 및 ETag/TTL 정합성 메커니즘 — 조회 성능 향상 및 서버 부하 최소화를 위한 Django 내장 Cache API 연동 데코레이터/헬퍼 구현. HTTP ETag / If-None-Match 헤더 기반의 조건부 검증 및 짧은 TTL(Time-To-Live) 적용을 통한 캐시 정합성 전략 구현."

## Clarifications

### Session 2026-08-17

- Q: How should callers opt into cached prompt retrieval? → A: Provide a separate cache-aware helper; keep `get_client().fetch()` unchanged and uncached.
- Q: When should a valid cached prompt be revalidated with the registry? → A: Serve it without a registry request during its TTL, then revalidate on the first lookup after expiry.
- Q: Which opt-in cache entry point should the integration expose? → A: Expose a cache-aware helper only; a decorator is outside this feature's scope.
- Q: Should cache identity include category or expand this feature to category-scoped prompt slugs? → A: Preserve the current globally unique prompt slug contract; identify entries by non-secret registry address, global prompt slug, and label selection, without category.
- Q: What should happen to the cached prompt and ETag after the freshness TTL expires? → A: Mark the entry stale but retain its representation and ETag for a separate revalidation-retention period; use them only for conditional revalidation, never as stale fallback.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reuse a recently retrieved prompt (Priority: P1)

A Django application repeatedly requests the same published prompt and receives the previously retrieved representation during a short freshness window without downloading or rebuilding the unchanged representation again.

**Why this priority**: Reusing a recent result is the primary source of lower lookup latency and reduced registry load.

**Independent Test**: Request the same prompt identity twice within the freshness window and verify that the second lookup returns the same prompt while avoiding a second full representation transfer.

**Acceptance Scenarios**:

1. **Given** no cached entry exists for a requested prompt and label, **When** the application retrieves it successfully, **Then** the prompt and its validator are fresh for the configured freshness window and retained for the separate revalidation window.
2. **Given** a valid cached entry exists for the same prompt and label, **When** the application requests it again before expiry, **Then** the cached prompt is returned without a full registry response body.
3. **Given** cached entries exist for different prompt or label identities, **When** one identity is requested, **Then** only its matching entry can be returned.

---

### User Story 2 - Revalidate an expired prompt efficiently (Priority: P1)

A Django application revalidates an expired cached prompt with the registry and continues using the cached representation when the published prompt has not changed.

**Why this priority**: Conditional revalidation limits transferred data while ensuring that the cache does not remain fresh indefinitely without registry confirmation.

**Independent Test**: Expire a cached prompt, revalidate it against an unchanged registry representation, and verify that the registry reports no modification, transfers no representation body, and refreshes the local freshness window.

**Acceptance Scenarios**:

1. **Given** a stale retained prompt has a validator, **When** it is revalidated and the current registry validator matches, **Then** the registry returns a bodyless not-modified result and the application returns the cached prompt as fresh.
2. **Given** an expired cached prompt has a validator, **When** it is revalidated and the current representation has changed, **Then** the registry returns the current prompt and validator and the cached entry is replaced.
3. **Given** a caller presents a matching validator directly to the registry, **When** the prompt representation is unchanged, **Then** the registry returns a bodyless not-modified response.
4. **Given** a caller presents a missing, malformed, or non-matching validator, **When** the prompt is available, **Then** the registry returns the complete current representation and its current validator.

---

### User Story 3 - Bound or clear stale cached data (Priority: P2)

An application operator can rely on automatic expiry and can explicitly clear one prompt or all PromptKit cache entries when an immediate refresh is required.

**Why this priority**: A bounded stale period and targeted recovery control make caching safe during prompt publication changes and operational troubleshooting.

**Independent Test**: Populate multiple prompt and label entries, clear one prompt and verify its entries are refreshed while unrelated prompts remain cached, then clear all entries and verify every subsequent lookup is refreshed.

**Acceptance Scenarios**:

1. **Given** cached entries exist for several labels of one prompt and for unrelated prompts, **When** that prompt is explicitly cleared, **Then** all cached labels for that prompt are removed and unrelated prompt entries remain usable.
2. **Given** PromptKit cache entries exist, **When** an operator requests a global PromptKit cache clear, **Then** all PromptKit-owned prompt entries are removed without clearing unrelated application cache data.
3. **Given** a cached prompt expires and the registry reports that it is no longer available, **When** revalidation occurs, **Then** the cached entry is removed and the registry's current not-available outcome is returned without stale fallback.

### Edge Cases

- Two requests miss or revalidate the same cache entry concurrently; both callers receive a valid result and no partial or corrupt entry becomes visible.
- A prompt's on-live version changes while an earlier on-live representation remains cached; the earlier representation is used only until its bounded freshness window ends, after which revalidation discovers the new representation.
- An on-live assignment is removed, a custom label is moved, or the requested prompt is deleted after caching; revalidation removes the obsolete entry and preserves the registry's no-fallback behavior.
- A cached value or validator is absent, malformed, or cannot be decoded; it is treated as a miss rather than returned to the caller.
- The cache service is unavailable or rejects an operation; retrieval continues through the registry when possible, and cache failure does not change the registry result or expose credentials.
- The registry returns a full successful response without a usable validator; the current result is returned but is not retained as a conditionally revalidatable entry.
- A conditional request contains multiple validators or a weak validator; matching follows HTTP validator semantics and never treats a partial string match as valid.
- A request fails authentication or authorization; neither its error response nor data from a differently authorized request is cached or returned.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration MUST offer one documented, explicitly opt-in cache-aware helper that preserves the existing read-only prompt lookup inputs and result semantics; the client returned by `get_client()` and its `fetch()` operation MUST remain unchanged and uncached.
- **FR-002**: A successful retrieval MUST retain the complete retrieved prompt representation, its registry-issued validator, a freshness boundary, and a separate revalidation-retention boundary.
- **FR-003**: Cache identity MUST distinguish the non-secret registry address, globally unique prompt slug, and explicit versus omitted label selection so different registries or resolutions cannot satisfy one another; credentials and category MUST NOT form part of the identity.
- **FR-004**: A non-expired, valid matching entry MUST satisfy a repeated lookup without making any registry request or downloading a full prompt representation.
- **FR-005**: The default freshness period MUST be 60 seconds and MUST be replaceable with a positive application-level setting; it controls only whether an entry may be returned without registry contact, while zero MUST disable fresh reuse, and negative, non-numeric, boolean, or otherwise invalid values MUST fail application startup without exposing credentials.
- **FR-006**: After freshness expires but before revalidation retention expires, the next lookup MUST use the retained validator for conditional registry revalidation and MUST NOT return the stale representation unless the registry confirms it is unchanged; after retention expires, the next lookup MUST perform a full registry retrieval.
- **FR-007**: Every successful registry prompt representation eligible for caching MUST include a deterministic HTTP entity validator that changes whenever any client-observable field in that representation changes.
- **FR-008**: When a conditional request validator matches the current representation, the registry MUST return HTTP 304 with no representation body; when it does not match, the registry MUST return the complete current representation and current validator.
- **FR-009**: Conditional validator comparison MUST support valid HTTP `If-None-Match` forms used for retrieval, including weak validators and validator lists, and MUST reject malformed or partial matches safely.
- **FR-010**: A not-modified result MUST cause the integration to return the cached prompt and begin new freshness and revalidation-retention periods without replacing the cached representation.
- **FR-011**: A full successful revalidation response MUST atomically replace the cached representation and validator before the new entry is made available.
- **FR-012**: If the registry reports that an expired prompt is unavailable or inaccessible, the integration MUST remove the matching cached entry and return that current outcome; it MUST NOT return a stale prompt or fall back to `latest`, a custom label, a draft, or another prompt version.
- **FR-013**: Authentication, authorization, validation, transport, server, and other unsuccessful responses MUST NOT be stored as reusable prompt entries.
- **FR-014**: Missing, malformed, incomplete, or undecodable cache entries MUST be treated as misses and MUST NOT be returned to callers.
- **FR-015**: Cache read, write, expiry, or deletion failure MUST NOT alter successful registry result semantics; when registry retrieval remains possible, the integration MUST return that result without caching it.
- **FR-016**: The integration MUST expose a documented manual invalidation operation that can clear all cached labels for one prompt or all PromptKit-owned prompt entries while preserving unrelated application cache data.
- **FR-017**: Prompt-specific invalidation MUST NOT remove cached entries belonging to another prompt, and label-specific cache identities MUST NOT collide.
- **FR-018**: Concurrent misses, revalidations, and invalidations MUST never expose a partial representation, mismatched validator, or cache entry belonging to another prompt resolution.
- **FR-019**: Credentials and authorization headers MUST NOT appear in cache identifiers, cached prompt metadata beyond what the retrieved representation already contains, errors, or logs.
- **FR-020**: This feature MUST preserve the core SDK's framework independence and read-only behavior and MUST NOT add prompt mutation, prompt compilation, LLM invocation, provider selection, tracing, evaluation, analytics, or workflow behavior.
- **FR-021**: All new public retrieval, conditional response, expiry, invalidation, isolation, failure, and no-fallback behaviors MUST have repeatable automated contract coverage.

### Key Entities *(include if feature involves data)*

- **Cached prompt entry**: One resolved read-only prompt representation, its validator, freshness boundary, revalidation-retention boundary, prompt identity, and label resolution identity.
- **Entity validator**: A registry-issued opaque value representing one exact client-observable prompt response revision and used only to test whether that representation has changed.
- **Conditional retrieval**: A registry lookup carrying one or more prior validators and resulting in either a bodyless not-modified outcome or a complete current representation.
- **Invalidation scope**: The operator-selected boundary for removing all cached labels of one prompt or all PromptKit-owned entries.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a sequence of 100 repeated lookups for one unchanged prompt within the freshness window, at least 99 lookups return the correct prompt without a full registry response body after the initial retrieval.
- **SC-002**: 100% of unchanged stale-entry checks performed within revalidation retention return the cached prompt only after a bodyless not-modified registry response and begin new freshness and retention windows.
- **SC-003**: 100% of changed, relabeled, unpublished, deleted, or inaccessible prompt cases converge to the registry's current representation or current error on the first lookup after expiry, with no stale or cross-label fallback.
- **SC-004**: Unless manually invalidated sooner, no cached prompt is treated as fresh for more than the configured TTL; with the default configuration, the maximum freshness interval is 60 seconds.
- **SC-005**: 100% of matching conditional registry requests transfer zero prompt-representation body bytes, while 100% of non-matching requests return the complete current representation and validator.
- **SC-006**: Prompt-specific invalidation removes 100% of that prompt's cached label variants and 0% of unrelated prompt entries; global invalidation removes 100% of PromptKit-owned entries and 0% of unrelated application cache entries.
- **SC-007**: Across automated isolation and concurrency checks, zero lookups return a prompt, label resolution, or validator belonging to another cache identity, and zero callers observe a partial cached entry.
- **SC-008**: 100% of tested cache-backend failures preserve the registry's observable success or error result and disclose zero credential values.
- **SC-009**: Existing uncached read-only lookup, label resolution, authentication, and client-side compilation behaviors continue to pass their established contract checks unchanged.

## Assumptions

- The feature spans the registry's read-only fetch response and one explicitly opt-in cache-aware helper in the official Django integration; decorators are outside scope, and the registered client, its existing `fetch()` operation, and the core SDK remain uncached and framework agnostic.
- The default short TTL is 60 seconds. Applications may choose a different positive duration, and a value of zero explicitly disables cache reuse.
- Fresh entries are returned without contacting the registry; the first lookup after expiry performs conditional revalidation, so publication changes may take up to one configured TTL to become visible.
- A stale retained representation is conditional-request metadata, not a fallback response: it is returned only after a matching not-modified result, and registry errors remain visible to the caller.
- Cache entries are private application data and are not shared across application deployments unless the application's selected cache service intentionally shares them.
- Only successful, validator-bearing prompt retrievals are reusable. Error-response caching and stale-on-error service are outside scope.
- Manual prompt invalidation covers all cached label variants for the selected prompt because label assignments can change independently.
- Existing API-key authentication, on-live default resolution, published-only label rules, and the prohibition on `production` and fallback behavior remain authoritative.
- Prompt slugs remain globally unique within a registry, matching the current database and read API contract; category-scoped prompt slugs and category-qualified retrieval are outside scope.
- Cache metrics dashboards, distributed locking, proactive invalidation events, background refresh, cache warming, and changes to prompt compilation are outside scope.
