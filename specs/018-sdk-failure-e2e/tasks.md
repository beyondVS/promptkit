# Tasks: SDK Failure Resilience E2E Validation

**Input**: Design documents from `/specs/018-sdk-failure-e2e/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [failure-resilience-contract.md](./contracts/failure-resilience-contract.md), [quickstart.md](./quickstart.md)

**Tests**: Required. This feature's value is automated E2E validation of the public SDK failure contract; write assertions before any conditional production correction.

**Organization**: Tasks are grouped by user story. All new implementation is kept in the root-discovered integration suite unless a failing assertion proves a narrow defect in an existing production contract.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel after its listed dependencies are complete.
- **[Story]**: Maps to the user story in [spec.md](./spec.md).

## Phase 1: Setup

**Purpose**: Establish the focused E2E test module and its test-only sentinel vocabulary.

- [ ] T001 Create the focused pytest integration module with test-only API-key, variable-value, and template-content sentinels in `tests/promptkit/integration/test_sdk_failure_e2e.py`

---

## Phase 2: Foundational Test Infrastructure

**Purpose**: Build reusable fixtures that block all user-story assertions until a real loopback registry boundary is available safely.

- [ ] T002 Add transactional test-database fixtures that create a category, prompt, required variables, ordered sections, published version, and on-live version through existing services in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T003 Add `live_server` health-readiness, accepted/rejected test-key, SDK-client cleanup, bind-only refused-connection, and accept-then-close loopback socket fixtures in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T004 Add reusable assertions for public exception non-disclosure, `promptkit`-namespace record filtering, logger-state snapshots, application-owned safe records, and a zero-call downstream spy in `tests/promptkit/integration/test_sdk_failure_e2e.py`

**Checkpoint**: A test-owned published on-live prompt can be reached through the ready local HTTP Prompt Server; fixture/setup failures remain distinct from SDK scenario failures.

---

## Phase 3: User Story 1 - Distinguish Registry Availability and Authentication Failures (Priority: P1) 🎯 MVP

**Goal**: Give callers distinct, safe outcomes for local credential configuration, unavailable registry transport, and real registry authentication rejection.

**Independent Test**: Run only `tests/promptkit/integration/test_sdk_failure_e2e.py` and verify a real HTTP successful setup, zero-request invalid configuration, refused loopback communication, and HTTP 401 authentication outcomes without prompt fallback.

### Tests for User Story 1

- [ ] T005 [US1] Write real-HTTP readiness and successful published on-live prompt retrieval assertions using `live_server` and the public `PromptKitClient` in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T006 [US1] Write blank/whitespace API-key construction assertions for `InvalidConfigurationError` and zero HTTP requests in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T007 [US1] Write refused-connection and accept-then-close mid-request-disconnect assertions for one no-retry `CommunicationError` each, zero prompt result, and deterministic client/socket cleanup in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T008 [US1] Write real local-HTTP rejected-nonempty-key assertions for `AuthenticationError`, no prompt result, and no credential disclosure in `tests/promptkit/integration/test_sdk_failure_e2e.py`

### Conditional Contract Correction for User Story 1

- [ ] T009 [US1] Run `uv run pytest tests/promptkit/integration/test_sdk_failure_e2e.py -q`; only if T005–T008 expose a public-contract defect, apply the smallest responsible correction in `packages/promptkit/src/promptkit/client.py` or `apps/server/prompts/auth.py` and rerun the focused module

**Checkpoint**: Registry configuration, communication, and authentication failures are independently distinguishable and safe through the public SDK.

---

## Phase 4: User Story 2 - Reject Invalid Variables Without Partial Output (Priority: P1)

**Goal**: Prove that a prompt retrieved through the real registry boundary cannot yield a partial compilation or downstream action when variable validation fails.

**Independent Test**: Retrieve the controlled prompt through the public SDK, compile it separately with missing, unexpected, and incompatible values, and confirm the mapped exception, no compiled result, and zero downstream calls for every case.

### Tests for User Story 2

- [ ] T010 [US2] Write the real-HTTP retrieval-to-compilation missing-required-variable assertion for `MissingVariableError`, the affected variable name in its safe message, no compiled result, and zero downstream calls in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T011 [US2] Write the real-HTTP retrieval-to-compilation unexpected-variable assertion for `UnexpectedVariableError`, the affected variable name in its safe message, no compiled result, and zero downstream calls in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T012 [US2] Write the real-HTTP retrieval-to-compilation incompatible-variable-type assertion for `InvalidVariableTypeError`, the affected variable name or validation reason in its safe message, no compiled result, and zero downstream calls in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T013 [US2] Verify all three invalid-variable cases scan exception text and formatted exception chains for protected values in `tests/promptkit/integration/test_sdk_failure_e2e.py`

### Conditional Contract Correction for User Story 2

- [ ] T014 [US2] Run `uv run pytest tests/promptkit/integration/test_sdk_failure_e2e.py -q`; only if T010–T013 expose a compilation contract defect, apply the smallest responsible correction in `packages/promptkit/src/promptkit/compiler.py` and rerun the focused module

**Checkpoint**: Each invalid variable category remains atomic, publicly distinguishable, and incapable of reaching downstream consumers.

---

## Phase 5: User Story 3 - Log SDK Failures Safely in the Calling Application (Priority: P2)

**Goal**: Prove that callers own logging while the selected SDK failure paths preserve safe exceptions and do not mutate logging configuration.

**Independent Test**: For each scoped failure, catch the public exception, record only its safe type/message through an application test logger, then verify no `promptkit` record, handler mutation, protected-value disclosure, or cross-run leakage.

### Tests for User Story 3

- [ ] T015 [US3] Write logger/root-state snapshot and `promptkit`-namespace zero-record assertions around the scoped configuration, communication, authentication, and compilation failure paths in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T016 [US3] Write application-owned safe exception-record assertions and protected-sentinel scans while excluding unrelated live-Django server records in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T017 [US3] Write same-process three-run resilience assertions for zero SDK handler creation, zero scoped SDK records, and zero cross-run protected-value leakage in `tests/promptkit/integration/test_sdk_failure_e2e.py`
- [ ] T018 [US3] Write an application-handler-failure-after-catch assertion proving the already delivered SDK exception category and safe message remain unchanged in `tests/promptkit/integration/test_sdk_failure_e2e.py`

### Conditional Contract Correction for User Story 3

- [ ] T019 [US3] Run `uv run pytest tests/promptkit/integration/test_sdk_failure_e2e.py -q`; only if T015–T018 expose a scoped logging contract defect, apply the smallest responsible correction in `packages/promptkit/src/promptkit/client.py` or `packages/promptkit/src/promptkit/compiler.py` and rerun the focused module

**Checkpoint**: The calling application controls diagnostics, while the scoped SDK failures remain log-free, safe, and stable across repeated execution.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Confirm no regression to existing SDK/server contracts and verify the documented validation path.

- [ ] T020 [P] Run the selected SDK and server regressions from `tests/promptkit/unit/`, `tests/promptkit/integration/test_public_sdk_harness.py`, and `apps/server/prompts/tests/test_read_only_api.py` using `uv run pytest`
- [ ] T021 [P] Run static quality checks for changed Python paths with `uv run ruff check`, `uv run ruff format --check`, and `uv run mypy .` using `pyproject.toml`
- [ ] T022 Run the full test suite with `uv run pytest` from `pyproject.toml` and resolve only failures attributable to `tests/promptkit/integration/test_sdk_failure_e2e.py` or a directly exposed contract defect
- [ ] T023 Verify the focused command and expected outcomes in `specs/018-sdk-failure-e2e/quickstart.md` match the implemented test module

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately.
- **Phase 2**: Depends on T001 and blocks all user-story work.
- **US1 (Phase 3)**: Depends on T002–T004; it is the MVP and produces the live retrieved prompt baseline.
- **US2 (Phase 4)**: Depends on T002–T005 because it consumes the real-HTTP retrieved prompt, but is independently testable after that setup.
- **US3 (Phase 5)**: Depends on T002–T004 and the scoped failure assertions in T006–T013.
- **Polish (Phase 6)**: Depends on all desired story tasks; T020 and T021 may run in parallel, followed by T022 and T023.

### User Story Dependencies

- **US1**: No dependency on another user story after foundational fixtures; MVP.
- **US2**: Reuses the successful real-HTTP retrieval baseline from US1 but has separate compilation failure outcomes.
- **US3**: Reuses the scoped failure actions from US1 and US2 to observe logging ownership without adding SDK logging.

## Parallel Opportunities

- After the focused E2E module is complete, T020 and T021 can run in parallel because they do not modify the same files.
- If a contract defect is found, its narrowly responsible production correction can be prepared while another contributor reviews the corresponding test assertion, but the correction must not be merged without the focused rerun.

## Parallel Example: Cross-Cutting Validation

```text
Task: "Run selected SDK/server regressions from tests/promptkit/unit/, tests/promptkit/integration/test_public_sdk_harness.py, and apps/server/prompts/tests/test_read_only_api.py"
Task: "Run Ruff format/lint and MyPy using pyproject.toml"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001–T004 to make the local HTTP registry and safety helpers deterministic.
2. Complete T005–T009 to lock the three recovery-relevant retrieval outcomes.
3. Run the focused module; no production edit is expected unless the assertions reveal a defect.

### Incremental Delivery

1. Add US1 for safe configuration, communication, and authentication recovery.
2. Add US2 to prove local compilation cannot release incomplete output.
3. Add US3 to prove application-owned logging and repeated-run resilience.
4. Run selected regressions and the full project harness before handoff.

## Notes

- Every task uses the required checkbox, ID, and exact path format.
- `[P]` marks only tasks that can run without shared-file or unfinished-task conflicts.
- Do not add a dependency, a fixed port, a subprocess server, an external LLM call, or real credentials.
- Existing adapter warning behavior is outside this feature; the zero-record assertions apply only to the selected fetch/compile failure paths.
