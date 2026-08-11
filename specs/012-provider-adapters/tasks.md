# Tasks: Gemini and OpenAI Prompt Adapters

**Input**: Design documents from `/specs/012-provider-adapters/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/sdk-provider-adapters.md, quickstart.md

**Tests**: The specification requires isolated automated coverage for every public adapter path. Within each user story, add the listed tests first, confirm that they fail for the missing behavior, and then implement the behavior.

**Organization**: Tasks are grouped by user story so Gemini and OpenAI happy-path conversion can be delivered independently before the shared safety policy is completed across all targets.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and has no dependency on an incomplete task
- **[Story]**: Maps the task to User Story 1, 2, or 3 from spec.md
- Every task includes the exact repository path it changes or validates

## Phase 1: Setup (Shared Test Infrastructure)

**Purpose**: Prepare focused, provider-free fixtures for test-first adapter development.

- [ ] T001 Create the `unittest.TestCase`-based adapter test module with reusable `CompiledPrompt` and ordered-section fixture builders in `tests/promptkit/unit/test_adapters.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the typed plain-data contracts and SDK error boundary shared by all adapters.

**⚠️ CRITICAL**: Complete this phase before starting any user story implementation.

- [ ] T002 [P] Add public `AdapterConversionError(PromptKitError)` without prompt-content disclosure in `packages/promptkit/src/promptkit/exceptions.py`
- [ ] T003 [P] Define the Gemini, Chat Completions, and Responses `TypedDict` argument/message shapes plus the module logger in new `packages/promptkit/src/promptkit/adapters.py`

**Checkpoint**: Shared types and the expected failure category exist without adding Gemini/OpenAI SDK dependencies.

---

## Phase 3: User Story 1 - Prepare a compiled prompt for Gemini (Priority: P1) 🎯 MVP

**Goal**: Convert valid compiled sections into exact `google-genai` `contents` and optional `config.system_instruction` plain dictionaries.

**Independent Test**: Convert deliberately unordered system, user, and assistant sections and assert exact role/parts/text shape, ascending order, assistant-to-model mapping, `\n\n` system joining, and omission of `config` when no system section exists, with no provider import or request.

### Tests for User Story 1

> **NOTE**: Write T004 first and confirm the new Gemini tests fail before T005.

- [ ] T004 [US1] Add failing Gemini contract tests for exact dictionary shape, ascending ordering, multiple-system joining, assistant-to-model mapping, distinct repeated roles, and no-system `config` omission in `tests/promptkit/unit/test_adapters.py`

### Implementation for User Story 1

- [ ] T005 [US1] Implement stateless `GeminiAdapter.to_generate_content_args()` for valid sectioned prompts in `packages/promptkit/src/promptkit/adapters.py`
- [ ] T006 [US1] Export `GeminiAdapter`, its public argument `TypedDict` contracts, and `AdapterConversionError` from `packages/promptkit/src/promptkit/__init__.py`
- [ ] T007 [US1] Run and pass the focused Gemini test selection in `tests/promptkit/unit/test_adapters.py`

**Checkpoint**: User Story 1 converts valid sectioned prompts for Gemini independently and all Gemini happy-path tests pass.

---

## Phase 4: User Story 2 - Prepare a compiled prompt for either OpenAI API (Priority: P1)

**Goal**: Convert the same valid compiled prompt through separate Chat Completions and Responses methods on one `OpenAIAdapter`.

**Independent Test**: Assert that Chat Completions preserves every ordered system/user/assistant section as a distinct role/content message, while Responses joins system text under `instructions` and preserves distinct ordered user/assistant `input` items, without an OpenAI import or request.

### Tests for User Story 2

> **NOTE**: Write T008 and T009 first and confirm the new OpenAI tests fail before T010.

- [ ] T008 [US2] Add failing Chat Completions tests for exact `messages` shape, ascending ordering, role/text preservation, and distinct consecutive roles in `tests/promptkit/unit/test_adapters.py`
- [ ] T009 [US2] Add failing Responses tests for exact `instructions`/`input` shape, `\n\n` system joining, ascending ordering, role/text preservation, distinct consecutive roles, and `instructions` omission in `tests/promptkit/unit/test_adapters.py`

### Implementation for User Story 2

- [ ] T010 [US2] Implement stateless `OpenAIAdapter.to_chat_completions_args()` and `OpenAIAdapter.to_responses_args()` for valid sectioned prompts in `packages/promptkit/src/promptkit/adapters.py`
- [ ] T011 [US2] Export `OpenAIAdapter` and its Chat Completions and Responses argument `TypedDict` contracts from `packages/promptkit/src/promptkit/__init__.py`
- [ ] T012 [US2] Run and pass the focused OpenAI test selection in `tests/promptkit/unit/test_adapters.py`

**Checkpoint**: User Story 2 exposes two independently callable OpenAI conversions and all OpenAI happy-path tests pass.

---

## Phase 5: User Story 3 - Detect prompts that cannot be converted safely (Priority: P2)

**Goal**: Apply one consistent local validation, fallback, fidelity, immutability, and system-only warning policy to all three public methods.

**Independent Test**: Exercise every public method with unsupported/blank roles, duplicate orders, no sections, system-only sections, sensitive and unusual text, and a frozen source prompt; assert local typed failures or exact provider-specific results, one safe WARNING only where required, no runtime warning, no mutation, and no provider activity.

### Tests for User Story 3

> **NOTE**: Write T013–T015 first and confirm the newly covered safety behavior fails before T016.

- [ ] T013 [US3] Add failing cross-adapter tests for duplicate-order rejection, blank/differently-cased/unknown role rejection, actionable content-safe errors, and sectionless aggregate-content fallback in `tests/promptkit/unit/test_adapters.py`
- [ ] T014 [US3] Add failing cross-adapter tests for exact provider-specific system-only outputs, one WARNING containing slug/version/label but no prompt text, absence of runtime warnings, text fidelity, source metadata exclusion, source immutability, and no provider calls in `tests/promptkit/unit/test_adapters.py`
- [ ] T015 [US3] Add a failing or unmet performance assertion that each public conversion handles a valid 200-section prompt in under one second in `tests/promptkit/unit/test_adapters.py`

### Implementation for User Story 3

- [ ] T016 [US3] Centralize pre-output role/order validation, copied ascending sorting, sectionless user fallback, exact text preservation, and one safe system-only logger call across all adapter methods in `packages/promptkit/src/promptkit/adapters.py`
- [ ] T017 [US3] Extend the isolated Git subdirectory installation regression to import and exercise the public adapters without provider SDK packages in `tests/promptkit/integration/test_git_subdirectory_install.py`
- [ ] T018 [US3] Run and pass all adapter unit and independent-install integration scenarios in `tests/promptkit/unit/test_adapters.py` and `tests/promptkit/integration/test_git_subdirectory_install.py`

**Checkpoint**: All three methods satisfy the complete safety and edge-case matrix without external dependencies, mutation, partial output, or provider calls.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Document the public surface and complete the project harness validation.

- [ ] T019 Document all three public conversion methods, return shapes, caller-owned model/settings, system-only warning behavior, and provider-free usage in `packages/promptkit/README.md`
- [ ] T020 [P] Run Ruff lint and format checks for `packages/promptkit/src/promptkit/adapters.py`, `packages/promptkit/src/promptkit/exceptions.py`, `packages/promptkit/src/promptkit/__init__.py`, `tests/promptkit/unit/test_adapters.py`, and `tests/promptkit/integration/test_git_subdirectory_install.py`
- [ ] T021 [P] Run strict MyPy validation for `packages/promptkit` and `tests/promptkit`
- [ ] T022 Run the full pytest suite and record the final adapter and regression results in `specs/012-provider-adapters/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; starts immediately.
- **Foundational (Phase 2)**: Depends on T001 and blocks all user story implementation.
- **User Story 1 (Phase 3)**: Depends on Phase 2 and delivers the suggested Gemini MVP.
- **User Story 2 (Phase 4)**: Depends on Phase 2, not on US1 behavior. When implemented concurrently, coordinate edits to `adapters.py`, `__init__.py`, and `test_adapters.py`.
- **User Story 3 (Phase 5)**: Depends on both US1 and US2 because it applies shared policies to all three completed conversion methods.
- **Polish (Phase 6)**: Depends on all selected user stories. T020 and T021 can run in parallel after T019; T022 follows both.

### User Story Dependency Graph

```text
Setup → Foundational ─┬→ US1 (Gemini) ──┐
                     └→ US2 (OpenAI) ──┴→ US3 (cross-adapter safety) → Polish
```

### Within Each User Story

- Add the story's contract tests and observe the expected failure before implementing it.
- Implement provider mapping before top-level public exports.
- Run the story-focused tests before advancing to the next checkpoint.
- For US3, add all shared-policy tests before refactoring the three methods onto the shared normalization path.

### Parallel Opportunities

- T002 and T003 can run in parallel after T001 because they create or edit different source files.
- US1 and US2 are semantically independent after Phase 2 and can be developed in isolated branches/worktrees; their shared-file edits must be merged deliberately.
- T020 and T021 can run in parallel after documentation is complete because both are read-only harness checks.
- US3 is intentionally serialized after US1 and US2 because it validates and refactors their shared behavior.

---

## Parallel Example: User Story 1

US1 uses one test file, one implementation file, and one public export file in strict TDD order, so its tasks should run sequentially: T004 → T005 → T006 → T007. Parallelize at the story level by developing US2 in an isolated worktree after Phase 2.

## Parallel Example: User Story 2

T008 and T009 both edit `tests/promptkit/unit/test_adapters.py` and therefore run sequentially, followed by T010 → T011 → T012. In an isolated worktree, this sequence can run concurrently with the complete US1 sequence.

## Parallel Example: User Story 3

US3 deliberately spans all public methods and shared files, so T013 → T014 → T015 → T016 → T017 → T018 is sequential. This prevents one target from adopting a different validation or warning policy.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 fixture setup.
2. Complete Phase 2 public types and error foundation.
3. Complete T004–T007 for Gemini.
4. Stop and validate the US1 independent test criteria.

### Incremental Delivery

1. Setup + Foundational establish provider-free typed contracts.
2. US1 delivers Gemini conversion and its focused tests.
3. US2 adds both OpenAI targets and their focused tests.
4. US3 unifies safety, fallback, warnings, fidelity, and independent-install coverage.
5. Polish documents the surface and runs the complete harness.

### Parallel Team Strategy

1. Complete T001–T003 together, with T002 and T003 in parallel.
2. Develop US1 and US2 in separate worktrees because both touch the same three files.
3. Merge both stories, then complete US3 against the integrated public surface.
4. Run Ruff and MyPy in parallel, followed by the full pytest suite.

---

## Notes

- `[P]` tasks are limited to genuinely independent files or read-only checks.
- No task installs `google-genai` or `openai`; plain dictionary compatibility is the owned boundary.
- Public adapter behavior and core logic require complete isolated unit coverage under the constitution.
- Do not add model selection, credentials, provider calls, tools, streaming, retry, response handling, or Django/Prompt Server changes.
- Commit after each task or cohesive task group, and stop at each story checkpoint for independent validation.
