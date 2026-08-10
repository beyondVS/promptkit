# Tasks: SDK Local Prompt Compilation

**Input**: Design documents from `/specs/011-sdk-compile-rendering/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [sdk-compile-api.md](contracts/sdk-compile-api.md), [quickstart.md](quickstart.md)

**Tests**: Required. The specification and constitution require isolated automated coverage for every public compile success path and typed failure outcome.

**Organization**: Tasks are grouped by user story. The shared public error/result surface is created once before story implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks after stated dependencies are complete.
- **[Story]**: Maps the task to a user story from [spec.md](spec.md).
- Every task includes its exact target file path.

## Phase 1: Setup (Shared Test Inputs)

**Purpose**: Extend the existing SDK test fixtures with reusable compile scenarios without changing package configuration.

- [ ] T001 Add reusable retrieved-prompt payload builders for typed variables, defaults, and sections in `tests/promptkit/unit/conftest.py`

---

## Phase 2: Foundational (Public Compile Surface)

**Purpose**: Establish the typed result and error vocabulary used by all compilation paths.

**⚠️ CRITICAL**: Complete this phase before adding `compile()` behavior or its story tests.

- [ ] T002 Add `MissingVariableError`, `InvalidVariableTypeError`, `UnexpectedVariableError`, and `TemplateValidationError` as `PromptKitError` subclasses in `packages/promptkit/src/promptkit/exceptions.py`
- [ ] T003 Add immutable `CompiledPrompt` and its rendered-section representation with source slug, version, and label fields in `packages/promptkit/src/promptkit/models.py`
- [ ] T004 Export `CompiledPrompt` and all compile-specific public errors from `packages/promptkit/src/promptkit/__init__.py`

**Checkpoint**: The package exposes the documented result/error types, with no compilation behavior added yet.

---

## Phase 3: User Story 1 - Render a Retrieved Prompt Locally (Priority: P1) 🎯 MVP

**Goal**: A developer compiles a retrieved prompt entirely in-process and receives rendered aggregate content and ordered rendered sections.

**Independent Test**: Compile fixtures with declared text variables, repeated placeholders, and no variables; assert exact rendered content/sections and source metadata without using a client transport or provider adapter.

### Tests for User Story 1

- [ ] T005 [US1] Add failing `unittest.TestCase` public compile tests for valid rendering, repeated placeholders, all four valid declared types, and no-variable prompts in `tests/promptkit/unit/test_compiler.py`
- [ ] T006 [US1] Add failing `unittest.TestCase` public compile tests for preservation of slug, version, label, roles, and section order in `tests/promptkit/unit/test_compiler.py`

### Implementation for User Story 1

- [ ] T007 [US1] Implement constrained parsing, full delimiter/declaration validation, strict Pydantic v2 schema validation, default normalization, and one-pass aggregate/section rendering helpers in `packages/promptkit/src/promptkit/compiler.py`
- [ ] T008 [US1] Add `RetrievedPrompt.compile(params=...)` orchestration that validates before constructing `CompiledPrompt` in `packages/promptkit/src/promptkit/models.py`

**Checkpoint**: The public compile path validates every template and input before returning exact local output with traceable metadata.

---

## Phase 4: User Story 2 - Receive Clear Validation Feedback (Priority: P2)

**Goal**: A developer receives typed, safe failures when input is missing, undeclared, malformed, or incompatible with a declared variable type.

**Independent Test**: Compile fixtures with each invalid input category and assert the exact typed error, affected name/condition, absence of supplied values in the message, and absence of a result.

### Tests for User Story 2

- [ ] T009 [US2] Add failing `unittest.TestCase` tests for required-value omission, valid caller override of defaults, and valid normalized defaults for all declared types in `tests/promptkit/unit/test_compiler.py`
- [ ] T010 [US2] Add failing `unittest.TestCase` tests for strict wrong-type inputs, malformed defaults, and undeclared input keys in `tests/promptkit/unit/test_compiler.py`
- [ ] T011 [US2] Add failing `unittest.TestCase` tests that compile errors do not include supplied values in `tests/promptkit/unit/test_compiler.py`

### Implementation for User Story 2

- [ ] T012 [US2] Complete typed translation for Pydantic v2 missing, extra, and strict-type failures without exposing supplied values in `packages/promptkit/src/promptkit/compiler.py`
- [ ] T013 [US2] Complete default-normalization failure handling and caller-precedence edge cases in `packages/promptkit/src/promptkit/compiler.py`

**Checkpoint**: All declared input/default rules fail safely and predictably before rendering.

---

## Phase 5: User Story 3 - Preserve Template Safety and Traceability (Priority: P3)

**Goal**: A developer cannot accidentally compile malformed or declaration-inconsistent templates, while successful results retain the fetched prompt identity.

**Independent Test**: Compile malformed-delimiter, unsupported-placeholder, undeclared-placeholder, and unreferenced-required-declaration fixtures; assert `TemplateValidationError` and no partial result, then verify placeholder-looking supplied content remains literal.

### Tests for User Story 3

- [ ] T014 [US3] Add failing `unittest.TestCase` tests for unclosed/orphaned delimiters and unsupported placeholder expressions in `tests/promptkit/unit/test_compiler.py`
- [ ] T015 [US3] Add failing `unittest.TestCase` tests for undeclared placeholders, unreferenced required declarations, and one-pass handling of placeholder-looking values in `tests/promptkit/unit/test_compiler.py`

### Implementation for User Story 3

- [ ] T016 [US3] Complete malformed-delimiter, unsupported-syntax, and declaration-mismatch diagnostics in `packages/promptkit/src/promptkit/compiler.py`
- [ ] T017 [US3] Confirm template-validation errors are raised before `CompiledPrompt` construction and retain single-pass rendering behavior in `packages/promptkit/src/promptkit/compiler.py`

**Checkpoint**: Invalid templates never return a partially rendered prompt, and successful output remains traceable and non-recursive.

---

## Phase 6: Polish & Cross-Cutting Verification

**Purpose**: Verify the published surface, performance boundary, package isolation, and all quality gates.

- [ ] T018 [P] Add a `unittest.TestCase` public-import regression assertion for compile models and errors in `tests/promptkit/unit/test_models.py`
- [ ] T019 [P] Add the 50-variable/200-placeholder performance-boundary `unittest.TestCase` in `tests/promptkit/unit/test_compiler.py`
- [ ] T020 Run the focused SDK tests, full test suite, Ruff check/format check, and MyPy; record results in `specs/011-sdk-compile-rendering/quickstart.md`
- [ ] T021 Review `packages/promptkit/src/promptkit/` and `tests/promptkit/unit/` against [sdk-compile-api.md](contracts/sdk-compile-api.md) to confirm no server call, LLM invocation, framework dependency, or supplied-value disclosure was introduced
- [ ] T022 Document `RetrievedPrompt.compile()`, `CompiledPrompt`, typed errors, and the local-only rendering boundary in `packages/promptkit/README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Starts immediately.
- **Phase 2**: Depends on T001 and blocks all public compilation implementation.
- **US1 (Phase 3)**: Depends on T002–T004; it is the MVP.
- **US2 (Phase 4)**: Depends on US1's compile entry point (T007–T008) and adds validation before rendering.
- **US3 (Phase 5)**: Depends on US1's renderer (T007–T008) and hardens its parser and pre-render validation.
- **Polish (Phase 6)**: Depends on all selected story phases.

### User Story Dependencies

- **US1 (P1)**: No story dependency after the foundational public surface.
- **US2 (P2)**: Extends US1's public compile flow with Pydantic validation and typed failure mapping.
- **US3 (P3)**: Extends US1's parser with safety validation; it may follow US2 so all error mapping is complete.

### Parallel Opportunities

- T002 and T003 may proceed in parallel after T001 because they modify different files; T004 follows both.
- Within US1, T005 and T006 can be prepared together in `tests/promptkit/unit/test_compiler.py`, but should be coordinated to avoid same-file conflicts.
- Within US2, T009–T011 are a single test file and should be completed sequentially by one owner; T012 begins after their expected behavior is agreed.
- T018 and T019 can run in parallel after US3 because they affect separate test modules.

## Parallel Example: Foundation and Polish

```text
Task: "T002 Add compile-specific errors in packages/promptkit/src/promptkit/exceptions.py"
Task: "T003 Add CompiledPrompt in packages/promptkit/src/promptkit/models.py"

Task: "T018 Add public-import regression in tests/promptkit/unit/test_models.py"
Task: "T019 Add performance-boundary test in tests/promptkit/unit/test_compiler.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001–T004.
2. Write T005–T006 and confirm they fail.
3. Complete T007–T008, including full validation before any output is constructed.
4. Run the focused US1 tests and validate fully rendered local output.

### Incremental Delivery

1. Deliver US1 for fully validated local rendering and traceable result metadata.
2. Deliver US2 for strict Pydantic validation, defaults, and safe typed errors.
3. Deliver US3 for complete template syntax/declaration safety.
4. Complete Phase 6 quality gates before handoff.

## Notes

- All tasks use the existing `packages/promptkit` SDK and `tests/promptkit/unit` suite; no server, migration, adapter, or dependency-management task is in scope.
- Compile tests are public-interface tests. They must not call a registry transport or an LLM provider.
