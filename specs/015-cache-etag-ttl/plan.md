# Implementation Plan: Cache and ETag Consistency

**Branch**: `015-cache-etag-ttl` | **Date**: 2026-08-17 | **Spec**: [spec.md](spec.md)

**Input**: Day 15 cache-aware Django helper, registry ETag/conditional GET support, and configurable Django integration cache TTL.

## Summary

Add an explicitly opt-in `promptkit-django` cached-fetch helper while preserving the existing uncached `get_client().fetch()` contract. The helper uses only the host application's configured Django default cache backend, validates `PROMPTKIT.CACHE_TTL` during AppConfig startup, and uses a short fresh window followed by an equal-length revalidation-only window. It calls a new validator-aware core SDK operation after freshness expires. The Prompt Server emits deterministic representation ETags and returns bodyless 304 responses for matching `If-None-Match` values.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.2, Django REST Framework, Pydantic v2, HTTPX

**Storage**: Existing PostgreSQL registry data; host application's Django `CACHES["default"]` backend for integration cache entries

**Testing**: pytest, pytest-django, Django `TestCase`, HTTPX mock transport

**Target Platform**: Self-hosted Django server and Django applications on supported Python platforms

**Project Type**: Django registry web service plus framework-agnostic SDK and Django integration packages in a monorepo

**Performance Goals**: At least 99 of 100 unchanged fresh repeated lookups avoid a registry request; matching conditional GET responses transfer no prompt body

**Constraints**: Use only the host-configured Django default cache backend; default fresh TTL is 60 seconds; `CACHE_TTL=0` disables storage and reuse; no credentials in cache keys or logs; no stale-on-error fallback; preserve existing core `fetch()` behavior

**Scale/Scope**: One AppConfig-registered client per Django application lifecycle; cache identity isolates registry address, globally unique prompt slug, and omitted versus explicit label; no multi-client registry in the integration lifecycle

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Prompt registry stays read-only | Pass | The server adds only response validation. The helper performs retrieval, never CUD or LLM invocation. |
| Core SDK remains framework agnostic | Pass | Django cache access is confined to `promptkit-django`; the core exposes only HTTP conditional retrieval. |
| Client-side compilation remains local | Pass | Cached values are `RetrievedPrompt` representations; no compilation moves to the registry. |
| Label resolution preserves no-fallback policy | Pass | Cache misses, stale entries, and failed revalidation return the registry's existing outcomes; no `latest`, draft, or alternate-label fallback is added. |
| Lightweight/self-hosted design | Pass | Reuses Django's configured cache backend and existing HTTPX/Pydantic dependencies; no cache service dependency, worker, or telemetry service is added. |
| Public APIs and core logic are tested | Pass | Unit, integration, and server contract tests are included in the implementation sequence. |

## Project Structure

### Documentation (this feature)

```text
specs/015-cache-etag-ttl/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/cached-fetch.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/server/prompts/
├── views/api.py                         # Read endpoint ETag and 304 behavior
├── serializers.py                        # Client-observable response shape
└── tests/test_read_only_api.py           # Server conditional-response contracts

packages/promptkit/src/promptkit/
├── client.py                             # Validator-aware HTTP retrieval primitive
├── models.py                             # Conditional retrieval result type
└── __init__.py                           # Public SDK exports, if needed

packages/promptkit-django/src/promptkit_django/
├── configuration.py                      # Strict CACHE_TTL configuration validation
├── apps.py                               # Lifecycle-scoped validated settings/client state
├── cache.py                              # Cache entry, keys, helper, invalidation
├── registry.py                            # Existing uncached client access remains intact
└── __init__.py                           # Explicit cached helper/invalidation exports

tests/
├── promptkit/unit/test_client.py
├── promptkit_django/unit/test_configuration.py
├── promptkit_django/unit/test_cache.py
└── promptkit_django/integration/test_django_lifecycle.py
```

**Structure Decision**: Extend the existing three-layer boundary: the server owns ETag generation and HTTP conditional handling, the core SDK owns HTTP transport and typed outcomes, and `promptkit-django` owns Django settings, cache access, and the opt-in public helper.

## Complexity Tracking

No constitution violations require complexity justification.
