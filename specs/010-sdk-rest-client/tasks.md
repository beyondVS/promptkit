# Tasks: SDK Remote Prompt Retrieval

**Input**: Design documents from `specs/010-sdk-rest-client/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [sdk-client-api.md](contracts/sdk-client-api.md), [quickstart.md](quickstart.md)

**Tests**: Required. The feature specification requires automated isolated coverage for all public retrieval outcomes.

**Organization**: Tasks are grouped by user story. Every story can be verified with the stated independent test once its phase is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks after its listed prerequisites are complete.
- **[Story]**: User story association.
- Every task includes an exact repository path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the standalone package boundary and resolve its declared runtime dependencies.

- [X] T001 Create the standalone distribution metadata and `src` build configuration with only `httpx` and Pydantic v2 runtime dependencies in `packages/promptkit/pyproject.toml`
- [X] T002 [P] Create the package README describing read-only scope, explicit client configuration, and independent installation in `packages/promptkit/README.md`
- [X] T003 Regenerate `uv.lock` and synchronize the new package member after T001 without changing the already-matching root workspace configuration in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the importable package surface and test transport seam required by every story.

**⚠️ CRITICAL**: Complete this phase before implementing story behavior.

- [X] T004 Create the package module boundary and temporary explicit public exports in `packages/promptkit/src/promptkit/__init__.py`
- [X] T005 Create reusable `httpx.MockTransport` response builders and API-key-safe test fixtures in `tests/promptkit/unit/conftest.py`

**Checkpoint**: The package is importable in the workspace and every story can use an isolated HTTP transport.

---

## Phase 3: User Story 1 - Retrieve a Publishable Prompt (Priority: P1) 🎯 MVP

**Goal**: A developer can synchronously retrieve the on-live or explicitly labelled published prompt with its version metadata, sections, and declared variables.

**Independent Test**: `tests/promptkit/unit/test_client.py` proves exact authenticated GET requests and returns a typed prompt for both omitted-label and explicit-label responses without a real server.

### Tests for User Story 1

- [X] T006 [P] [US1] Add response-model tests for required fields, nested sections/variables, timestamps, and ignored unknown fields in `tests/promptkit/unit/test_models.py`
- [X] T007 [P] [US1] Add synchronous successful-fetch tests for the exact path, API-key header, omitted label, explicit label, and 10-second default in `tests/promptkit/unit/test_client.py`

### Implementation for User Story 1

- [X] T008 [US1] Implement typed Pydantic category, variable, section, and retrieved-prompt models that reject missing required data and ignore additional data in `packages/promptkit/src/promptkit/models.py`
- [X] T009 [US1] Implement the synchronous `PromptKitClient` constructor, injected transport seam, authenticated GET request, caller-overridable timeout, and successful response decoding in `packages/promptkit/src/promptkit/client.py`
- [X] T010 [US1] Export `PromptKitClient` and the retrieved-prompt model types as the package public interface in `packages/promptkit/src/promptkit/__init__.py`

**Checkpoint**: On-live and explicit-label retrieval work with typed content, version metadata, sections, and variable definitions.

---

## Phase 4: User Story 2 - Receive Actionable Retrieval Failures (Priority: P2)

**Goal**: A developer receives precise, API-key-safe outcomes for invalid input, availability, authorization, rate limiting, transport, redirect, and invalid-response failures.

**Independent Test**: Controlled `httpx.MockTransport` responses and transport failures each raise the documented public exception, and rejected local input never invokes the transport.

### Tests for User Story 2

- [X] T011 [US2] Add tests for empty slug, forbidden `production`, unsafe registry URLs, and API-key-safe local validation failures in `tests/promptkit/unit/test_client.py`
- [X] T012 [US2] Add response-mapping tests for 401, unknown-slug 404, `no_deployable_version`, `label_not_found`, `invalid_label`, 429, and 3xx responses in `tests/promptkit/unit/test_client.py`
- [X] T013 [US2] Add transport and payload-failure tests for timeout/connection/TLS failures, no automatic retry, malformed JSON, and missing required response fields in `tests/promptkit/unit/test_client.py`

### Implementation for User Story 2

- [X] T014 [US2] Define the base public error and typed authentication, missing-prompt, no-deployable-version, label, invalid-label, rate-limit, redirect, communication, and invalid-response errors in `packages/promptkit/src/promptkit/exceptions.py`
- [X] T015 [US2] Add client preflight validation for non-empty slug, explicit API key, forbidden `production`, HTTPS-or-loopback-HTTP URLs, and no-request local failures in `packages/promptkit/src/promptkit/client.py`
- [X] T016 [US2] Add no-retry, no-redirect HTTP status/error mapping and malformed-response handling to `packages/promptkit/src/promptkit/client.py`
- [X] T017 [US2] Export the typed public error hierarchy in `packages/promptkit/src/promptkit/__init__.py`

**Checkpoint**: Every required error category is distinguishable; no response path silently falls back to another prompt, version, or label.

---

## Phase 5: User Story 3 - Install the SDK Independently (Priority: P3)

**Goal**: A developer can install and import `promptkit` from the monorepo package subdirectory without Django server or framework integration dependencies.

**Independent Test**: A clean temporary virtual environment installs from the committed local Git repository using `#subdirectory=packages/promptkit` and imports `PromptKitClient`.

### Tests for User Story 3

- [X] T018 [US3] Add a subprocess-based isolated-install regression test that creates a temporary virtual environment, installs the committed local Git `HEAD` subdirectory, and imports the public client in `tests/promptkit/integration/test_git_subdirectory_install.py`

### Implementation for User Story 3

- [X] T019 [US3] Add package installation and minimal client-import usage instructions matching the public API in `packages/promptkit/README.md`
- [X] T020 [US3] After an explicitly user-approved checkpoint commit includes `packages/promptkit`, run the Git-subdirectory installation scenario from `specs/010-sdk-rest-client/quickstart.md` and report the result without modifying test source files

**Checkpoint**: The committed package installs through its Git subdirectory and imports without Django, DRF, or `promptkit-django`.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Validate the completed public library and keep the package contract aligned with its implementation.

- [X] T021 Reconcile the active server serializer and error behavior in `docs/sdk-read-api-contract.md` with `apps/server/prompts/views/api.py` and `apps/server/prompts/serializers.py`
- [X] T022 [P] Verify package metadata, README examples, and public exports against `specs/010-sdk-rest-client/contracts/sdk-client-api.md` in `packages/promptkit/pyproject.toml`, `packages/promptkit/README.md`, and `packages/promptkit/src/promptkit/__init__.py`
- [X] T023 Run targeted SDK tests, workspace lint/format checks, and strict typing checks from `tests/promptkit/`, `packages/promptkit/`, and root `pyproject.toml`
- [X] T024 Run the full project test suite and re-run the independent-install quickstart after the final user-approved commit using `specs/010-sdk-rest-client/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately. T003 depends on T001.
- **Phase 2**: Depends on T001; T004 and T005 can proceed independently once package metadata exists.
- **US1 (Phase 3)**: Depends on T004 and T005. T006 and T007 precede T008-T010; T008 precedes T009; T009 precedes T010.
- **US2 (Phase 4)**: Depends on the US1 client. T011-T013 execute sequentially because they share one test module; T014 precedes T016 and T017; T015 precedes T016; T016 precedes T017.
- **US3 (Phase 5)**: Depends on completed package implementation and an explicitly user-approved checkpoint commit. T018 precedes T020; T019 can run alongside T018.
- **Polish (Phase 6)**: Depends on all desired stories. T021 and T022 can run in parallel; T024 requires a user-approved final commit for the Git-subdirectory check.

### User Story Dependencies

- **US1 (P1)**: MVP; no dependency on other user stories after the foundational package surface.
- **US2 (P2)**: Extends US1's client implementation but remains independently testable through injected transport responses.
- **US3 (P3)**: Depends on the package built by US1/US2 and an approved commit because Git installation reads `HEAD`.

### Parallel Opportunities

- T002 can run alongside T001.
- T006 and T007 can run in parallel after T004-T005.
- T018 and T019 can run in parallel after the package implementation is committed.
- T021 and T022 can run in parallel after all user stories are complete.

## Parallel Example: User Story 1

```text
Task: "Add response-model tests in tests/promptkit/unit/test_models.py"
Task: "Add synchronous successful-fetch tests in tests/promptkit/unit/test_client.py"
```

US2 tests intentionally share `tests/promptkit/unit/test_client.py`; execute T011-T013 sequentially to preserve a conflict-free working tree.

## Implementation Strategy

### MVP First

1. Complete package metadata and foundational test seam.
2. Complete US1 and run its isolated success-path tests.
3. Demonstrate on-live and labelled retrieval with a typed returned prompt.

### Incremental Delivery

1. Add US2 error and security behavior without changing US1's success contract.
2. Validate every failure category with mocked transport before any live-server check.
3. Add US3 independent installation validation only after a user-approved commit makes the package available to Git installation.

### Safety Notes

- `uv sync` downloads new declared dependencies and must be run with the approval required by project policy.
- Git-subdirectory installation uses committed `HEAD`; do not claim it passed from an uncommitted working tree.
- Never place a real API key in test fixtures, documentation, command history, or committed files.
