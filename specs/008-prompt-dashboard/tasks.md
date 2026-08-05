# Tasks: Prompt Management Dashboard

**Input**: Design documents from `specs/008-prompt-dashboard/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [SDK read contract](contracts/sdk-read-api.md), [quickstart.md](quickstart.md)

**Tests**: Required. The project constitution requires pytest coverage for public APIs and core logic; Django ORM/view tests use `django.test.TestCase` and isolated utilities use `unittest.TestCase`.

**Organization**: Tasks are grouped by user story. Governance, documentation, and schema/routing work that blocks every story appears first.

## Phase 1: Governance and Documentation Setup

**Purpose**: Make the approved on-live and label policy authoritative before application behavior changes.

- [X] T001 Amend on-live default lookup, published-only labels, `latest`, and `production` prohibition in `.specify/memory/constitution.md`
- [X] T002 Align branch workflow, documentation scope, and post-implementation audit guidance in `AGENTS.md`
- [X] T003 [P] Replace rollback/environment/production assumptions with draft-publish-on-live policy in `docs/prompt-server-requirements.md`
- [X] T004 [P] Replace label, compile-flow, and SDK default-lookup policy in `docs/project-spec.md`
- [X] T005 [P] Update lifecycle, routing, API boundary, and MVP architecture in `docs/architecture.md`
- [X] T006 Update only incomplete Day 08+ milestones for lifecycle, labels, SDK lookup, and validation in `docs/project-plan.md`
- [X] T007 [P] Create the durable SDK read API policy in `docs/sdk-read-api-contract.md`
- [X] T008 Verify policy consistency across `.specify/memory/constitution.md`, `AGENTS.md`, and `docs/*.md`

---

## Phase 2: Foundational Lifecycle, Routing, and Test Infrastructure

**Purpose**: Establish the data invariants and API/dashboard boundaries that block all user stories.

**⚠️ CRITICAL**: Complete this phase before user-story implementation.

- [X] T009 Add lifecycle, on-live, revision, category-scoped name, label, variable-type, and section-role migrations in `apps/server/prompts/migrations/0005_prompt_dashboard_lifecycle.py`; classify existing labels and lifecycle data, transform supported records, and reject unsupported records with actionable migration diagnostics.
- [X] T010 Implement Version lifecycle fields, Prompt category-scoped name constraint, Label restrictions, variable types, and section roles in `apps/server/prompts/models.py`
- [X] T011 [P] Add model and migration regression coverage for lifecycle constraints and each supported/rejected existing-data migration outcome in `apps/server/prompts/tests/test_models_lifecycle.py`
- [X] T012 Implement reusable template-reference parsing, validation, rename propagation, and default-value validation in `apps/server/prompts/services/templates.py`
- [X] T013 [P] Add isolated parser and variable-validation tests in `apps/server/prompts/tests/test_template_validation.py`
- [X] T014 Implement transaction helpers for prompt creation with an initial empty draft, cascading prompt deletion, publish, clone, on-live changes, label moves, and stale-revision detection in `apps/server/prompts/services/lifecycle.py`
- [X] T015 [P] Add transaction and conflict tests in `apps/server/prompts/tests/test_lifecycle_services.py`
- [X] T016 Normalize SDK and dashboard URL inclusion to `/api/v1/prompts/<slug>/` and `/dashboard/` only in `apps/server/config/urls.py` and `apps/server/prompts/urls.py`
- [X] T017 [P] Update SDK response serialization for version status, sections, variables, and optional labels in `apps/server/prompts/serializers.py`
- [X] T018 Add routing and method/auth boundary regression tests in `apps/server/prompts/tests/test_routing_contract.py`
- [X] T019 [P] Add prompt dashboard create, update, category-move, on-live deletion guard, cascading-deletion, and initial-empty-draft tests in `apps/server/prompts/tests/test_prompt_dashboard.py`
- [X] T020 Implement staff prompt create, update, category-move, and deletion dashboard handlers through lifecycle transactions in `apps/server/prompts/views/dashboard.py`
- [X] T021 Add prompt create/edit forms, category selection or creation, and deletion confirmation UI in `apps/server/prompts/templates/prompts/prompt_form.html` and `apps/server/prompts/templates/prompts/prompt_list.html`
- [X] T022 Add prompt dashboard CUD routes in `apps/server/prompts/urls.py`

**Checkpoint**: Governance, data invariants, transaction primitives, and URL boundaries are ready.

---

## Phase 3: User Story 1 — 버전별 프롬프트 작성 및 발행 (Priority: P1) 🎯 MVP

**Goal**: Staff can edit drafts, validate template content and variables, publish immutably, and receive conflict-safe feedback.

**Independent Test**: Create a draft, manage sections and variables, use valid `{{ variable_name }}` references, publish it, and verify all draft mutations and publish reversion are rejected afterward.

### Tests for User Story 1

- [X] T023 [P] [US1] Add draft-only section and variable CUD tests in `apps/server/prompts/tests/test_dashboard_sections_variables.py`
- [X] T024 [P] [US1] Add publish immutability and irreversible-state tests in `apps/server/prompts/tests/test_dashboard_publish.py`
- [X] T025 [P] [US1] Add stale revision conflict tests for draft edits in `apps/server/prompts/tests/test_dashboard_conflicts.py`

### Implementation for User Story 1

- [X] T026 [US1] Implement staff-only prompt detail and selected-version context in `apps/server/prompts/views/dashboard.py`
- [X] T027 [P] [US1] Add draft section CUD POST handlers with role/order/content validation in `apps/server/prompts/views/dashboard.py`
- [X] T028 [P] [US1] Add draft variable CUD handlers with type/default/reference validation in `apps/server/prompts/views/dashboard.py`
- [X] T029 [US1] Implement publish action through lifecycle transactions in `apps/server/prompts/views/dashboard.py`
- [X] T030 [US1] Add version-detail, section editor, variable editor, and immutable read-only UI states in `apps/server/prompts/templates/prompts/prompt_detail.html`
- [X] T031 [US1] Add dashboard routes for detail, draft sections, draft variables, and publish actions in `apps/server/prompts/urls.py`
- [X] T032 [US1] Update staff dashboard styles/messages for validation and conflict feedback in `apps/server/prompts/templates/prompts/prompt_form.html`

**Checkpoint**: A complete draft-to-published workflow is independently usable and protected from stale or post-publication writes.

---

## Phase 4: User Story 2 — 독립된 새 버전 생성 (Priority: P1)

**Goal**: Staff can clone either a draft or published version into an independent new draft and delete drafts safely.

**Independent Test**: Clone both a draft and a published version, modify the clone, confirm source isolation, and verify only drafts can be deleted.

### Tests for User Story 2

- [X] T033 [P] [US2] Add clone source-state, deep-copy, and isolation tests in `apps/server/prompts/tests/test_version_clone.py`
- [X] T034 [P] [US2] Add draft-deletion and published-deletion rejection tests in `apps/server/prompts/tests/test_version_delete.py`

### Implementation for User Story 2

- [X] T035 [US2] Implement clone-to-draft and draft-delete lifecycle operations in `apps/server/prompts/services/lifecycle.py`
- [X] T036 [US2] Add clone and draft-delete dashboard actions in `apps/server/prompts/views/dashboard.py`
- [X] T037 [US2] Add clone-source selection, version sidebar, and draft-delete confirmation UI in `apps/server/prompts/templates/prompts/prompt_detail.html`
- [X] T038 [US2] Add clone and draft-delete routes in `apps/server/prompts/urls.py`

**Checkpoint**: Version branching is independent, draft-only deletion is enforced, and published history remains intact.

---

## Phase 5: User Story 3 — 배포 대상과 라벨 관리 (Priority: P1)

**Goal**: Staff can manage on-live and published-only labels; the SDK fetches only the on-live version by default.

**Independent Test**: Publish two versions, move on-live, clear it, manage labels, and verify omitted/explicit SDK lookups follow the contract without any draft or `production` fallback.

### Tests for User Story 3

- [X] T039 [P] [US3] Add on-live set, switch, clear, and single-target transaction tests in `apps/server/prompts/tests/test_on_live.py`
- [X] T040 [P] [US3] Add latest and custom-label lifecycle tests in `apps/server/prompts/tests/test_label_lifecycle.py`
- [X] T041 [P] [US3] Add SDK default/explicit-label/no-deployable-version contract tests in `apps/server/prompts/tests/test_read_only_api.py`

### Implementation for User Story 3

- [X] T042 [US3] Implement on-live set/clear and `latest` publication behavior in `apps/server/prompts/services/lifecycle.py`
- [X] T043 [US3] Implement published-only custom label create, move, and remove operations in `apps/server/prompts/services/lifecycle.py`
- [X] T044 [US3] Implement on-live and label dashboard handlers with stale-write protection in `apps/server/prompts/views/dashboard.py`
- [X] T045 [US3] Replace `production` default resolution with on-live and explicit published-label resolution in `apps/server/prompts/views/api.py`
- [X] T046 [US3] Add on-live controls, latest state, and custom-label management UI in `apps/server/prompts/templates/prompts/prompt_detail.html`
- [X] T047 [US3] Add on-live and label action routes in `apps/server/prompts/urls.py`

**Checkpoint**: Default SDK resolution, explicit labels, and dashboard deployment controls comply with the durable read API contract.

---

## Phase 6: User Story 4 — 카테고리 기반 탐색과 관리 (Priority: P2)

**Goal**: Staff can manage categories and browse prompts by category without violating category or prompt-name constraints.

**Independent Test**: Create, update, filter, and safely delete categories; verify attached categories cannot be deleted and prompt-name conflicts within a target category are rejected.

### Tests for User Story 4

- [X] T048 [P] [US4] Add category dashboard CUD and deletion-protection tests in `apps/server/prompts/tests/test_category_dashboard.py`
- [X] T049 [P] [US4] Add category filter and category-scoped prompt-name tests in `apps/server/prompts/tests/test_category_prompt_relation.py`

### Implementation for User Story 4

- [X] T050 [US4] Implement staff category CUD and category-filtered prompt list actions in `apps/server/prompts/views/dashboard.py`
- [X] T051 [US4] Enforce category-scoped prompt-name validation on create and move in `apps/server/prompts/views/dashboard.py`
- [X] T052 [US4] Add category management and filtered-list UI in `apps/server/prompts/templates/prompts/category_list.html` and `apps/server/prompts/templates/prompts/prompt_list.html`
- [X] T053 [US4] Add category dashboard routes in `apps/server/prompts/urls.py`

**Checkpoint**: Category management and browse flows are independently usable and preserve relational integrity.

---

## Phase 7: User Story 5 — 서비스 진입과 안전한 대시보드 접근 (Priority: P2)

**Goal**: Visitors can reach a landing page and login, while only staff users can access dashboard management features.

**Independent Test**: Visit the public root, direct-load protected URLs while unauthenticated or non-staff, then sign in as staff and reach the dashboard.

### Tests for User Story 5

- [X] T054 [P] [US5] Add landing, login redirect, staff authorization, and non-staff rejection tests in `apps/server/prompts/tests/test_dashboard_access.py`
- [X] T055 [P] [US5] Add CSRF protection tests for dashboard mutation routes in `apps/server/prompts/tests/test_dashboard_csrf.py`

### Implementation for User Story 5

- [X] T056 [US5] Implement public landing view and root URL mapping in `apps/server/core/views.py` and `apps/server/config/urls.py`
- [X] T057 [US5] Add landing template and navigation to dashboard login in `apps/server/core/templates/core/landing.html`
- [X] T058 [US5] Apply staff session authorization and POST-only CSRF-safe mutation behavior across `apps/server/prompts/views/dashboard.py`

**Checkpoint**: Public entry and dashboard access controls are independently verified.

---

## Phase 8: Polish and Cross-Cutting Verification

**Purpose**: Complete durable documentation, migrations, tests, and project harness validation.

- [X] T059 Reconcile admin registrations with lifecycle and label restrictions in `apps/server/prompts/admin.py`
- [X] T060 [P] Update SDK/client-facing examples to the on-live and explicit-label contract in `apps/server/README.md`
- [X] T061 [P] Retire or rewrite obsolete production/fallback and REST-CUD test assumptions in `apps/server/prompts/tests/test_version_api.py`, `apps/server/prompts/tests/test_prompt_crud.py`, and `apps/server/prompts/tests/test_search.py`
- [X] T062 Run migration tests and inspect generated migration SQL for PostgreSQL safety using `apps/server/prompts/migrations/0005_prompt_dashboard_lifecycle.py`
- [X] T063 Run formatting, linting, type checks, and full tests with `pyproject.toml` harness commands
- [X] T064 Execute every scenario in `specs/008-prompt-dashboard/quickstart.md` and record any fixes in the corresponding tests
- [X] T065 Perform final policy cross-check against `.specify/memory/constitution.md`, `AGENTS.md`, `docs/*.md`, and `specs/008-prompt-dashboard/contracts/sdk-read-api.md`

---

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 is mandatory and precedes all application changes.
- Phase 2 depends on Phase 1 and blocks every user story.
- US1 and US2 can begin after Phase 2; US3 requires Phase 2 plus published-version behavior from US1/US2.
- US4 can proceed after Phase 2 in parallel with P1 work.
- US5 can proceed after Phase 2 in parallel with P1/P2 work.
- Phase 8 follows the desired user-story phases.

### User story dependencies

- **US1 (P1)**: Depends on Phase 2 only; establishes draft/publish behavior.
- **US2 (P1)**: Depends on Phase 2; integrates with US1 lifecycle primitives but remains independently testable.
- **US3 (P1)**: Depends on published-version lifecycle behavior from US1 and clone/delete invariants from US2.
- **US4 (P2)**: Depends on Phase 2 only.
- **US5 (P2)**: Depends on Phase 2 only.

### Parallel opportunities

- T003–T005 and T007 can run in parallel after T001–T002 establish the governing policy.
- T015, T017, T019, T021, and T022 can run in parallel once their target implementation contracts are ready.
- US4 and US5 can run in parallel with US1/US2 after Phase 2.
- Within US3, T039–T041 can run in parallel; T042–T043 can run in parallel before dashboard/API integration.

## Parallel Example: User Story 3

```text
T039: on-live transaction tests
T040: latest/custom-label lifecycle tests
T041: SDK read API contract tests

T042: on-live/latest lifecycle implementation
T043: custom-label lifecycle implementation
```

## Implementation Strategy

### MVP first

1. Finish the governance/documentation and foundational phases.
2. Deliver US1 draft authoring and immutable publishing.
3. Validate US1 independently.
4. Add US2 clone/delete, then US3 on-live and SDK read resolution to complete the deployable registry MVP.

### Incremental delivery

1. Governance + foundation establishes a valid target architecture.
2. US1 delivers safe authoring.
3. US2 delivers iteration from any source version.
4. US3 delivers controlled deployment and read-only SDK consumption.
5. US4 and US5 complete management and entry/access flows.

## Format Validation

Every task uses the required checkbox, sequential ID, optional `[P]`, user-story label where applicable, and explicit file path format.
