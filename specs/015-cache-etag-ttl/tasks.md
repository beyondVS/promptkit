# Tasks: Cache and ETag Consistency

**Input**: Design documents from `/specs/015-cache-etag-ttl/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [cached-fetch contract](contracts/cached-fetch.md), [quickstart.md](quickstart.md)

**Tests**: Required. The specification requires repeatable automated contract coverage for every new public behavior and failure path.

**Organization**: Tasks are grouped by user story after the shared conditional-HTTP foundation. The integration's cache helper remains opt-in; `get_client().fetch()` is never made cache-aware.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes distinct files and has no unfinished dependency.
- **[US1]**, **[US2]**, **[US3]**: User-story traceability label.
- Every task includes its exact target path.

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Prepare the focused Django-cache test module without changing application runtime behavior.

- [X] T001 Create the LocMem-cache fixture and shared registry transport helpers in `tests/promptkit_django/unit/test_cache.py`

---

## Phase 2: Foundational (Conditional HTTP Contract)

**Purpose**: Complete the server and framework-agnostic SDK contract that every cache-aware lookup depends on.

**⚠️ CRITICAL**: Complete this phase before implementing any Django cache behavior.

- [X] T002 [P] Convert shared ORM fixtures to `setUpTestData()` and add direct ETag, ETag changes after serialized-field updates, on-live movement, and label reassignment, valid/malformed/list/weak/wildcard `If-None-Match`, bodyless 304, and unchanged error/auth regression cases in `apps/server/prompts/tests/test_read_only_api.py`
- [X] T003 [P] Add public `ConditionalFetchResult` import, `fetch_conditional()` signature and invariants, validator-aware HTTPX transport, 304 outcome, missing-ETag validation, and unchanged `fetch()` redirect/error cases in `tests/promptkit/unit/test_client.py`
- [X] T004 [P] Implement canonical serialized-response ETag generation and successful GET conditional 304 handling in `apps/server/prompts/views/api.py`
- [X] T005 [P] Define `ConditionalFetchResult` with the 200 prompt and 304 not-modified invariants in `packages/promptkit/src/promptkit/models.py`
- [X] T006 Implement `PromptKitClient.fetch_conditional(slug, *, label=None, etag=None) -> ConditionalFetchResult`, header handling, 304 branching, and missing-ETag validation in `packages/promptkit/src/promptkit/client.py`
- [X] T007 Export `ConditionalFetchResult` as the supporting public type for `fetch_conditional()` in `packages/promptkit/src/promptkit/__init__.py`
- [X] T008 Update ETag/304 status and response-header guarantees in `docs/sdk-read-api-contract.md`

**Checkpoint**: A direct authenticated registry request emits a deterministic ETag, a matching conditional request returns 304 with no body, and the core SDK can distinguish that 304 without changing existing `fetch()`.

---

## Phase 3: User Story 1 - Reuse a Recently Retrieved Prompt (Priority: P1) 🎯 MVP

**Goal**: Let a Django application explicitly use a helper that stores and reuses a fresh prompt through its configured default cache backend.

**Independent Test**: With a Django LocMem default cache and a successful ETag-bearing registry response, call `fetch_cached()` twice within `CACHE_TTL` and verify the second call returns the same `RetrievedPrompt` without another registry request; verify `get_client().fetch()` remains uncached.

### Tests for User Story 1

- [X] T009 [P] [US1] Add `CACHE_TTL` default, zero, invalid-type/value, unknown-key, and credential-redaction tests in `tests/promptkit_django/unit/test_configuration.py`
- [X] T010 [P] [US1] Add an exact 100-lookup/one-registry-call performance assertion, fresh-hit behavior, omitted-versus-explicit-label and registry-address isolation, credential absence from cache keys/values/errors/logs, unsuccessful-response non-storage, and uncached-client regression cases in `tests/promptkit_django/unit/test_cache.py`
- [X] T011 [P] [US1] Add startup registration coverage for retained validated cache settings in `tests/promptkit_django/integration/test_django_lifecycle.py`
- [X] T012 [P] [US1] Add the expected `fetch_cached()` export, typing marker, and public docstring contract before implementation in `tests/promptkit_django/unit/test_public_api.py`

### Implementation for User Story 1

- [X] T013 [US1] Extend strict `PROMPTKIT` parsing with the defaulted, finite, non-negative `CACHE_TTL` field and a validated-settings client factory in `packages/promptkit-django/src/promptkit_django/configuration.py`
- [X] T014 [US1] Retain validated settings with the one registered client during AppConfig startup in `packages/promptkit-django/src/promptkit_django/apps.py`
- [X] T015 [US1] Implement single-record cache serialization without credentials, safe canonical identity hashing, fresh-window lookup, successful ETag-bearing response storage only, and `CACHE_TTL=0` bypass in `packages/promptkit-django/src/promptkit_django/cache.py`
- [X] T016 [US1] Export the opt-in `fetch_cached()` helper with a public type hint and docstring without changing `get_client()` in `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: User Story 1 works with only the default Django cache backend and no request to the registry during the configured fresh interval.

---

## Phase 4: User Story 2 - Revalidate an Expired Prompt Efficiently (Priority: P1)

**Goal**: Revalidate stale retained entries with ETag instead of transferring an unchanged prompt body, while replacing changed representations atomically.

**Independent Test**: Advance a cached entry beyond freshness but within revalidation retention; verify `fetch_cached()` sends its ETag, returns the retained prompt only after 304, and replaces it after a changed 200 response.

### Tests for User Story 2

- [X] T017 [US2] Add stale-retention, outgoing `If-None-Match`, bodyless 304 refresh, changed-200 replacement, ETag-less successful-response rejection, post-retention full-fetch, malformed-entry, label reassignment, on-live removal, deletion, access denial, and registry-error no-stale-or-cross-label-fallback cases in `tests/promptkit_django/unit/test_cache.py`

### Implementation for User Story 2

- [X] T018 [US2] Extend cache-entry validation and `fetch_cached()` with two-window freshness/revalidation logic, typed conditional SDK retrieval, atomic replacement, and cache-miss fallback behavior in `packages/promptkit-django/src/promptkit_django/cache.py`

**Checkpoint**: User Story 2 returns a stale retained prompt only after a matching 304; changed, missing, malformed, or failed registry outcomes never serve stale data.

---

## Phase 5: User Story 3 - Bound or Clear Stale Cached Data (Priority: P2)

**Goal**: Give an operator prompt-level and global PromptKit invalidation without deleting unrelated Django cache entries.

**Independent Test**: Cache two labels for one prompt and one entry for another, clear the first prompt, then globally clear PromptKit entries; verify each affected lookup refreshes and an unrelated application cache key survives.

### Tests for User Story 3

- [X] T019 [P] [US3] Add per-prompt/all-entry invalidation, unrelated-key preservation, cache-backend failure with credential-redacted errors/logs, concurrent invalidation/write, and no-partial-entry cases in `tests/promptkit_django/unit/test_cache.py`
- [X] T020 [P] [US3] Add the expected `clear_prompt_cache()` export, type hint, docstring, and coexistence with `fetch_cached()` to `tests/promptkit_django/unit/test_public_api.py`

### Implementation for User Story 3

- [X] T021 [US3] Add global and per-prompt generation-token keys, pre-write generation recheck, credential-safe cache-failure bypass, and `clear_prompt_cache(slug=None)` in `packages/promptkit-django/src/promptkit_django/cache.py`
- [X] T022 [US3] Export `clear_prompt_cache()` with a public type hint and cache-isolation docstring in `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: User Story 3 invalidates only PromptKit-owned entries in the intended scope and never calls the Django backend's global clear operation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete user documentation and run the feature's focused and repository-wide verification ladder.

- [X] T023 [P] Document `CACHES["default"]`, `CACHE_TTL`, `fetch_cached()`, and `clear_prompt_cache()` in `packages/promptkit-django/README.md`
- [X] T024 Run every focused ETag, SDK, configuration, cache, and lifecycle scenario from `specs/015-cache-etag-ttl/quickstart.md`
- [X] T025 Run Ruff check/format verification, MyPy, and the full pytest suite specified in `pyproject.toml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately.
- **Phase 2**: T002 and T003 start after T001 and must first fail for the missing behavior; T004 starts after T002, T005 starts after T003, T006 depends on T003 and T005, T007 depends on T006, and T008 follows T004 and T006. It blocks every user story.
- **Phase 3 / US1**: T009–T012 can run after Phase 2 and must first fail for the missing behavior; T013 then T014 precede T015, and T016 follows T012 and T015.
- **Phase 4 / US2**: Depends on US1's T015 cache entry and helper; T017 precedes T018.
- **Phase 5 / US3**: Depends on US1's cache identity and US2's completed two-window state handling; T019 and T020 must first fail for the missing behavior, T021 follows T019, and T022 follows T020 and T021.
- **Phase 6**: T023 follows public API completion; T024 and T025 run after all desired story phases.

### User Story Dependencies

```text
Conditional HTTP foundation
        ↓
US1: fresh opt-in cache helper (MVP)
        ↓
US2: ETag stale revalidation
        ↓
US3: scoped invalidation
        ↓
Polish and full verification
```

### Parallel Opportunities

- T002 and T003 are independent server/core contract tests.
- T004 and T005 modify different server/core files and can proceed in parallel after T002 and T003 have established failing tests.
- T009, T010, T011, and T012 are independent US1 test files.
- T019 and T020 cover different US3 test modules and can be authored in parallel.
- T023 can be prepared after the public cache API is stable while later verification work is in progress.

## Implementation Strategy

### MVP First (User Story 1)

1. Complete the conditional HTTP foundation in Phase 2.
2. Complete T009–T016 for fresh cache hits and AppConfig TTL validation.
3. Run the US1 independent test before moving on.

### Incremental Delivery

1. Deliver server ETag plus the framework-agnostic conditional SDK primitive.
2. Deliver fresh cache reuse through the explicit Django helper.
3. Add stale ETag revalidation without weakening the no-fallback rule.
4. Add bounded manual invalidation and verify no unrelated Django cache entries are affected.

### Format Validation

- Every implementation task uses the required checkbox, sequential ID, optional `[P]`, story label where applicable, and exact path format.
- Total tasks: 25.
