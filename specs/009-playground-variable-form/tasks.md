# Tasks: Playground Variable Form

**Input**: Design documents from `/specs/009-playground-variable-form/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [dashboard-variable-schema.md](contracts/dashboard-variable-schema.md), [quickstart.md](quickstart.md)

**Tests**: Required. The dashboard schema interface is a protected server API and the project constitution requires public and core behavior to be covered by unit tests. Use `django.test.TestCase` and `setUpTestData` for database-backed tests.

**Organization**: Tasks are grouped by user story so each completed phase can be validated independently.

## Phase 1: Setup

**Purpose**: Prepare the focused regression-test module for the feature.

- [ ] T001 Create shared staff, non-staff, prompt, draft-version, published-version, and variable fixtures using `setUpTestData` in `apps/server/prompts/tests/test_dashboard_playground.py`

---

## Phase 2: Foundational

**Purpose**: Add import-safe protected view declarations and route entry points required by all Playground stories.

**⚠️ CRITICAL**: Complete this phase before user-story implementation.

- [ ] T002 Add protected Playground and schema view declarations in `apps/server/prompts/views/dashboard.py` and register their named version-primary-key routes in `apps/server/prompts/urls.py`

**Checkpoint**: The URL names and target shapes are available for isolated view and template work.

---

## Phase 3: User Story 1 - 프롬프트별 변수 입력 준비 (Priority: P1) 🎯 MVP

**Goal**: A staff user opens Playground from the currently selected draft or published version and sees only that version's variable schema with initial values.

**Independent Test**: Open each allowed version as staff; verify the page, schema response, target metadata, variable ordering, default values, and target isolation without using any compile or save action.

### Tests for User Story 1

- [ ] T003 [US1] Add page and schema contract tests for staff access, draft/published targets, schema ordering, nullable defaults, target isolation, and excluded template/section data in `apps/server/prompts/tests/test_dashboard_playground.py`

### Implementation for User Story 1

- [ ] T004 [US1] Implement selected-version lookup and read-only variable-schema response behavior in the protected Playground views using existing `Prompt`, `Version`, and `VariableDefinition` data in `apps/server/prompts/views/dashboard.py`
- [ ] T005 [US1] Add the selected-version Playground navigation link to the version toolbar in `apps/server/prompts/templates/prompts/prompt_detail.html`
- [ ] T006 [US1] Create the Playground page with target metadata, schema loading, per-variable labels/descriptions/required markers, default-value initialization, and browser-only state in `apps/server/prompts/templates/prompts/playground.html`

**Checkpoint**: Staff can independently prepare transient values for one selected draft or published version; no input is sent or stored.

---

## Phase 4: User Story 2 - 변수 유형에 맞는 입력 (Priority: P1)

**Goal**: A staff user receives type-appropriate controls and immediate local guidance for invalid or missing values.

**Independent Test**: With all four variable types, confirm valid values are accepted and invalid number/JSON values or missing required values are visibly identified without any server submission.

### Tests for User Story 2

- [ ] T007 [US2] Add response and rendered-page tests covering all four variable types, required/default metadata, and the absence of a value-submission endpoint in `apps/server/prompts/tests/test_dashboard_playground.py`

### Implementation for User Story 2

- [ ] T008 [US2] Extend the Playground renderer with text, number, boolean, and JSON controls plus client-side required, number, and JSON validation messages in `apps/server/prompts/templates/prompts/playground.html`

**Checkpoint**: The input form guides correct entry for all supported types while remaining local-only.

---

## Phase 5: User Story 3 - 비어 있는 변수 세트 이해 (Priority: P2)

**Goal**: A staff user understands a version with no variables, while invalid and unauthorized requests never disclose schema data.

**Independent Test**: Open a no-variable version, a nonexistent version, and both routes as unauthenticated and non-staff users; verify the empty state and access boundaries.

### Tests for User Story 3

- [ ] T009 [US3] Add tests for the no-variable empty state, unknown-version response, unauthenticated redirect, non-staff denial, and non-GET schema method rejection in `apps/server/prompts/tests/test_dashboard_playground.py`

### Implementation for User Story 3

- [ ] T010 [US3] Add a clear no-variable empty state and safe schema-load failure message to `apps/server/prompts/templates/prompts/playground.html`
- [ ] T011 [US3] Ensure the Playground and schema views preserve existing dashboard authorization and unknown-version handling in `apps/server/prompts/views/dashboard.py`

**Checkpoint**: Empty and failure states are understandable and no unauthorized actor can obtain schema details.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the feature against the documented contract and guard the intentionally excluded behavior.

- [ ] T012 [P] Verify route names, payload fields, method boundary, and SDK API separation against `specs/009-playground-variable-form/contracts/dashboard-variable-schema.md`
- [ ] T013 Run focused tests, full tests, Ruff, and MyPy, then complete the quickstart manual scenarios for type validation and refresh-time non-persistence in `specs/009-playground-variable-form/quickstart.md`
- [ ] T014 [P] Review changed dashboard templates and views for the explicit absence of persistence, compilation, preview, and LLM calls against `specs/009-playground-variable-form/spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Starts immediately.
- **Foundational (Phase 2)**: Depends on T001; provides stable route names.
- **US1 (Phase 3)**: Depends on Phase 2 and is the MVP.
- **US2 (Phase 4)**: Depends on the US1 page renderer.
- **US3 (Phase 5)**: Depends on the US1 page and views; it can be implemented after the shared page exists.
- **Polish (Phase 6)**: Depends on all desired user stories.

### User Story Dependencies

- **US1**: No dependency beyond foundational routing; independently useful MVP.
- **US2**: Builds on the variable renderer delivered by US1.
- **US3**: Builds on the page and schema views delivered by US1 but validates an independent empty/failure slice.

### Parallel Opportunities

- T012 and T014 can run in parallel once US1–US3 are complete because they inspect distinct documentation and source scopes.
- Avoid parallel changes to `apps/server/prompts/views/dashboard.py`, `apps/server/prompts/templates/prompts/playground.html`, and `apps/server/prompts/tests/test_dashboard_playground.py` because each is intentionally shared across stories.

## Implementation Strategy

### MVP First

1. Complete T001–T002.
2. Complete T003–T006 for US1.
3. Run the focused test module and manually validate draft and published version entry.
4. Stop for a demo if transient schema-driven input is sufficient.

### Incremental Delivery

1. Add US1 for secure selected-version schema retrieval and basic input layout.
2. Add US2 for all type-specific controls and browser validation.
3. Add US3 for no-variable and protected error states.
4. Run the cross-cutting validation tasks before handoff.

## Notes

- Every task uses the required checklist, ID, and file-path format.
- No migration task exists because the feature reuses `VariableDefinition` and never stores Playground input values.
- Do not add SDK API-key access, input POST routes, compile/preview actions, or LLM invocation tasks.
