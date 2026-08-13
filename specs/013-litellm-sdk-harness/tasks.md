# Tasks: LiteLLM Adapter and SDK Harness

**Input**: Design documents from `/specs/013-litellm-sdk-harness/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [SDK contract](contracts/sdk-litellm-and-public-harness.md), [quickstart.md](quickstart.md)

**Tests**: Tests are required by FR-012 through FR-017 and the project constitution. Add or update tests before their corresponding implementation work, then run the focused and full core SDK validation commands.

**Organization**: Tasks are grouped by user story so each increment remains independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks that modify different files and have no unfinished dependency.
- **[Story]**: Maps to the user story in [spec.md](spec.md).

## Phase 1: Setup

**Purpose**: Establish the Day 13 validation baseline before changing the core SDK.

- [ ] T001 Run the baseline core SDK suite and retain the result against `tests/promptkit/` before modifying `packages/promptkit/`.

---

## Phase 2: Foundational

**Purpose**: Confirm the shared foundations that all feature work uses.

The existing immutable `CompiledPrompt` models and `_resolve_sections()` policy in `packages/promptkit/src/promptkit/models.py` and `packages/promptkit/src/promptkit/adapters.py` already provide the required validation, ordering, fallback, and safe-warning foundation. No new foundational production component is required.

**Checkpoint**: Existing shared policy is available; user story work can proceed.

---

## Phase 3: User Story 1 - Prepare a compiled prompt for LiteLLM (Priority: P1) 🎯 MVP

**Goal**: Let an application developer obtain ordered LiteLLM-compatible message arguments from a compiled prompt without a LiteLLM dependency or provider call.

**Independent Test**: Run `uv run pytest tests/promptkit/unit/test_adapters.py tests/promptkit/integration/test_git_subdirectory_install.py` and verify exact mapping, all shared safety policies, root import, isolated installation, and absent LiteLLM dependency.

### Tests for User Story 1

- [ ] T002 [US1] Add initially failing LiteLLM conversion tests for ordered roles/content, repeated roles, sectionless aggregate fallback, exact text fidelity, and no input mutation in `tests/promptkit/unit/test_adapters.py`.
- [ ] T003 [US1] Extend shared adapter-policy parameterization for LiteLLM: duplicate-order and unsupported-role rejection, one safe system-only WARNING, no runtime warning, no provider import, and the 200-section performance boundary in `tests/promptkit/unit/test_adapters.py`.

### Implementation for User Story 1

- [ ] T004 [US1] Add typed LiteLLM message/completion-argument contracts and `LiteLLMAdapter.to_completion_args()` using the existing `_resolve_sections()` and `_partition_sections()` policy in `packages/promptkit/src/promptkit/adapters.py`.
- [ ] T005 [US1] Export `LiteLLMAdapter`, `LiteLLMChatMessage`, and `LiteLLMCompletionArgs` from the package root and add them to `__all__` in `packages/promptkit/src/promptkit/__init__.py`.
- [ ] T006 [US1] Document LiteLLM conversion usage and the caller-owned model/credential/execution boundary in `packages/promptkit/README.md`.
- [ ] T007 [US1] Extend the isolated Git-subdirectory install assertion for the LiteLLM adapter and confirm the installed environment has no LiteLLM dependency in `tests/promptkit/integration/test_git_subdirectory_install.py`.

**Checkpoint**: LiteLLM conversion is publicly importable, provider-free, and independently testable.

---

## Phase 4: User Story 2 - Validate the complete public SDK journey (Priority: P1)

**Goal**: Give SDK maintainers one local pytest harness that validates every package-root public API through import, behavior, or defined failure paths.

**Independent Test**: Run `uv run pytest tests/promptkit/integration/test_public_sdk_harness.py` and verify a mock registry response travels through `PromptKitClient.fetch()`, `RetrievedPrompt.compile()`, Gemini/OpenAI/LiteLLM conversion, model contracts, and public exceptions without a real registry or provider request.

### Tests and Harness for User Story 2

- [ ] T008 [US2] Create a package-root public API inventory and two-way coverage-map assertion that reports missing and stale export names in `tests/promptkit/integration/test_public_sdk_harness.py`.
- [ ] T009 [US2] Add public-import and data-contract assertions for every exported client, prompt model, adapter, typed argument contract, and exception hierarchy in `tests/promptkit/integration/test_public_sdk_harness.py`.
- [ ] T010 [US2] Add a controlled successful journey using `httpx.MockTransport`: authenticated `PromptKitClient.fetch()`, `RetrievedPrompt.compile()`, and all Gemini, OpenAI, and LiteLLM conversion outputs in `tests/promptkit/integration/test_public_sdk_harness.py`.
- [ ] T011 [US2] Add public failure-path assertions for client configuration/request/label, HTTP status and transport errors, malformed registry responses, compilation errors, and `AdapterConversionError` while checking API keys and supplied secret values remain undisclosed in `tests/promptkit/integration/test_public_sdk_harness.py`.

**Checkpoint**: The full declared package-root public surface has local end-to-end contract coverage without contacting external services.

---

## Phase 5: User Story 3 - Detect public surface drift (Priority: P2)

**Goal**: Fail clearly when a declared export and its public-harness coverage mapping diverge.

**Independent Test**: Use an isolated altered inventory/map fixture and confirm the harness identifies an unmapped current export and a stale mapping by name.

### Tests for User Story 3

- [ ] T012 [US3] Add isolated missing-export and stale-mapping drift tests with actionable symbol-name assertions in `tests/promptkit/integration/test_public_sdk_harness.py`.

**Checkpoint**: Future Public API changes cannot silently bypass the complete harness.

---

## Phase 6: Polish and Cross-Cutting Validation

**Purpose**: Verify the complete feature against project quality gates and delivery documentation.

- [ ] T013 [P] Reconcile implementation behavior and executable commands with the LiteLLM/public-harness contract in `specs/013-litellm-sdk-harness/contracts/sdk-litellm-and-public-harness.md` and `specs/013-litellm-sdk-harness/quickstart.md`.
- [ ] T014 Run the full core SDK pytest suite from `tests/promptkit/` after all focused tests pass.
- [ ] T015 Run Ruff and MyPy for `packages/promptkit/` and `tests/promptkit/`, fixing only Day 13 violations in the files named by those tools.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (T001)**: Starts immediately and establishes the baseline.
- **Foundational (Phase 2)**: Uses existing models and shared adapter policy; it does not introduce a blocking implementation task.
- **US1 (T002–T007)**: Starts after T001. T002 and T003 define expected behavior; T004 implements it; T005–T007 expose and prove it.
- **US2 (T008–T011)**: Starts after T005 because the complete inventory and successful journey include the new LiteLLM public exports.
- **US3 (T012)**: Starts after T008 because it tests the coverage-map mechanism.
- **Polish (T013–T015)**: Starts after the desired user stories are complete. T014 follows focused tests; T015 follows the complete pytest suite.

### User Story Dependencies

- **US1 (P1)**: Independent adapter increment; it has no dependency on the public-harness implementation.
- **US2 (P1)**: Depends on US1 package-root exports so it can test the complete supported conversion journey.
- **US3 (P2)**: Depends on US2's inventory and coverage map.

## Parallel Opportunities

- T002 and T003 modify the same unit-test file, so execute them sequentially before T004.
- After T004, T005 (`__init__.py`), T006 (`README.md`), and T007 (isolated-install test) touch different files and can proceed in parallel.
- T013 can run in parallel with review of completed user-story work, but T014 and T015 must run in order as the final validation ladder.

## Implementation Strategy

### MVP First (US1)

1. Complete T001–T004 to implement and prove LiteLLM conversion.
2. Complete T005–T007 to expose, document, and independently-install the feature.
3. Run the US1 independent test command before starting the full public harness.

### Incremental Delivery

1. Deliver LiteLLM conversion (US1) with no provider dependency.
2. Add the complete package-root public journey harness (US2).
3. Add public-surface drift regression protection (US3).
4. Complete the pytest → Ruff → MyPy validation ladder and synchronize the validation guide.

## Notes

- Every task follows the required checklist format and names its target file or directory.
- The implementation must retain the conversion-only boundary: no LiteLLM package import, model choice, credentials, provider request, or Prompt Server/Django dependency.
- Use Conventional Commit messages for logical groups, per `docs/project-plan.md`.
