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

- [ ] T001 Create the LocMem-cache fixture and shared registry transport helpers in `tests/promptkit_django/unit/test_cache.py`

---

## Phase 2: Foundational (Conditional HTTP Contract)

**Purpose**: Complete the server and framework-agnostic SDK contract that every cache-aware lookup depends on.

**⚠️ CRITICAL**: Complete this phase before implementing any Django cache behavior.

- [ ] T002 [P] Add direct ETag, valid/malformed/list/weak `If-None-Match`, bodyless 304, and unchanged error/auth regression cases in `apps/server/prompts/tests/test_read_only_api.py`
- [ ] T003 [P] Add validator-aware HTTPX transport cases, 304 typed outcome, ETag validation, and unchanged `fetch()` redirect/error behavior in `tests/promptkit/unit/test_client.py`
- [ ] T004 [P] Implement canonical serialized-response ETag generation and successful GET conditional 304 handling in `apps/server/prompts/views/api.py`
- [ ] T005 [P] Define the typed conditional retrieval result with prompt-or-not-modified invariants in `packages/promptkit/src/promptkit/models.py`
- [ ] T006 Implement the validator-aware `PromptKitClient` retrieval operation, header handling, 304 branching, and ETag validation in `packages/promptkit/src/promptkit/client.py`
- [ ] T007 Export the new conditional retrieval result and operation's supporting public types in `packages/promptkit/src/promptkit/__init__.py`
- [ ] T008 Update ETag/304 status and response-header guarantees in `docs/sdk-read-api-contract.md`

**Checkpoint**: A direct authenticated registry request emits a deterministic ETag, a matching conditional request returns 304 with no body, and the core SDK can distinguish that 304 without changing existing `fetch()`.

---

## Phase 3: User Story 1 - Reuse a Recently Retrieved Prompt (Priority: P1) 🎯 MVP

**Goal**: Let a Django application explicitly use a helper that stores and reuses a fresh prompt through its configured default cache backend.

**Independent Test**: With a Django LocMem default cache and a successful ETag-bearing registry response, call `fetch_cached()` twice within `CACHE_TTL` and verify the second call returns the same `RetrievedPrompt` without another registry request; verify `get_client().fetch()` remains uncached.

### Tests for User Story 1

- [ ] T009 [P] [US1] Add `CACHE_TTL` default, zero, invalid-type/value, unknown-key, and credential-redaction tests in `tests/promptkit_django/unit/test_configuration.py`
- [ ] T010 [P] [US1] Add fresh-hit, omitted-versus-explicit-label, registry-address identity, and uncached-client regression cases in `tests/promptkit_django/unit/test_cache.py`
- [ ] T011 [P] [US1] Add startup registration coverage for retained validated cache settings in `tests/promptkit_django/integration/test_django_lifecycle.py`

### Implementation for User Story 1

- [ ] T012 [US1] Extend strict `PROMPTKIT` parsing with the defaulted, finite, non-negative `CACHE_TTL` field and a validated-settings client factory in `packages/promptkit-django/src/promptkit_django/configuration.py`
- [ ] T013 [US1] Retain validated settings with the one registered client during AppConfig startup in `packages/promptkit-django/src/promptkit_django/apps.py`
- [ ] T014 [US1] Implement single-record cache serialization, safe canonical identity hashing, fresh-window lookup, normal ETag-bearing fetch storage, and `CACHE_TTL=0` bypass in `packages/promptkit-django/src/promptkit_django/cache.py`
- [ ] T015 [US1] Export the opt-in `fetch_cached()` helper without changing `get_client()` in `packages/promptkit-django/src/promptkit_django/__init__.py`
- [ ] T016 [US1] Extend deliberate public-export coverage for the cache helper in `tests/promptkit_django/unit/test_public_api.py`

**Checkpoint**: User Story 1 works with only the default Django cache backend and no request to the registry during the configured fresh interval.

---

## Phase 4: User Story 2 - Revalidate an Expired Prompt Efficiently (Priority: P1)

**Goal**: Revalidate stale retained entries with ETag instead of transferring an unchanged prompt body, while replacing changed representations atomically.

**Independent Test**: Advance a cached entry beyond freshness but within revalidation retention; verify `fetch_cached()` sends its ETag, returns the retained prompt only after 304, and replaces it after a changed 200 response.

### Tests for User Story 2

- [ ] T017 [US2] Add stale-retention, outgoing `If-None-Match`, bodyless 304 refresh, changed-200 replacement, ETag-less response, post-retention full-fetch, malformed-entry, and registry-error no-stale-fallback cases in `tests/promptkit_django/unit/test_cache.py`

### Implementation for User Story 2

- [ ] T018 [US2] Extend cache-entry validation and `fetch_cached()` with two-window freshness/revalidation logic, typed conditional SDK retrieval, atomic replacement, and cache-miss fallback behavior in `packages/promptkit-django/src/promptkit_django/cache.py`

**Checkpoint**: User Story 2 returns a stale retained prompt only after a matching 304; changed, missing, malformed, or failed registry outcomes never serve stale data.

---

## Phase 5: User Story 3 - Bound or Clear Stale Cached Data (Priority: P2)

**Goal**: Give an operator prompt-level and global PromptKit invalidation without deleting unrelated Django cache entries.

**Independent Test**: Cache two labels for one prompt and one entry for another, clear the first prompt, then globally clear PromptKit entries; verify each affected lookup refreshes and an unrelated application cache key survives.

### Tests for User Story 3

- [ ] T019 [US3] Add per-prompt/all-entry invalidation, unrelated-key preservation, cache-backend failure, concurrent invalidation/write, and no-partial-entry cases in `tests/promptkit_django/unit/test_cache.py`

### Implementation for User Story 3

- [ ] T020 [US3] Add global and per-prompt generation-token keys, pre-write generation recheck, cache-failure bypass, and `clear_prompt_cache(slug=None)` in `packages/promptkit-django/src/promptkit_django/cache.py`
- [ ] T021 [US3] Export `clear_prompt_cache()` and document its cache-isolation behavior in `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: User Story 3 invalidates only PromptKit-owned entries in the intended scope and never calls the Django backend's global clear operation.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Complete user documentation and run the feature's focused and repository-wide verification ladder.

- [ ] T022 [P] Document `CACHES["default"]`, `CACHE_TTL`, `fetch_cached()`, and `clear_prompt_cache()` in `packages/promptkit-django/README.md`
- [ ] T023 Run every focused ETag, SDK, configuration, cache, and lifecycle scenario from `specs/015-cache-etag-ttl/quickstart.md`
- [ ] T024 Run Ruff check/format verification, MyPy, and the full pytest suite specified in `pyproject.toml`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately.
- **Phase 2**: T002–T005 can start after T001; T006 depends on T005; T007 depends on T006; T008 follows T004 and T006. It blocks every user story.
- **Phase 3 / US1**: T009–T011 can run after Phase 2; T012 then T013 precede T014; T015 follows T014; T016 verifies T015.
- **Phase 4 / US2**: Depends on US1's T014 cache entry and helper; T017 precedes T018.
- **Phase 5 / US3**: Depends on US1's cache identity and US2's completed two-window state handling; T019 precedes T020, then T021.
- **Phase 6**: T022 follows public API completion; T023 and T024 run after all desired story phases.

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
- T004 and T005 modify different server/core files and can proceed in parallel after their tests exist.
- T009, T010, and T011 are independent US1 test files.
- T022 can be prepared after the public cache API is stable while later verification work is in progress.

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
- Total tasks: 24.
