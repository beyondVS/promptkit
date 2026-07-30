# Tasks: PromptCategory(도메인 범주) 독립 모델링 및 관리 API 개발

**Input**: Design documents from `/specs/005-prompt-category-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prompt-category-api.json, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure verification

- [ ] T001 Verify project structure and spec documents in `specs/005-prompt-category-api/`
- [ ] T002 [P] Verify `uv` environment and Django dependencies in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core ORM models and schema migrations that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `PromptCategory` ORM model in `apps/server/prompts/models.py`
- [ ] T004 Update `Prompt` ORM model to replace string `task` with `category` ForeignKey (`on_delete=models.RESTRICT`, `related_name='prompts'`) in `apps/server/prompts/models.py`
- [ ] T005 Create Django Schema and Data Migrations for `PromptCategory` table creation and existing `task` string data migration in `apps/server/prompts/migrations/`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - PromptCategory CRUD Management (Priority: P1) 🎯 MVP

**Goal**: Provide RESTful CRUD API endpoints for PromptCategory (create, list, retrieve, update, delete with ON DELETE Restrict protection)

**Independent Test**: Invoke `/api/categories/` REST endpoints to CRUD PromptCategory and verify 200/201/409 responses independently.

### Implementation for User Story 1

- [ ] T006 [P] [US1] Create `PromptCategorySerializer` and `PromptCategoryCreateSerializer` in `apps/server/prompts/serializers.py`
- [ ] T007 [US1] Implement `PromptCategoryViewSet` with ProtectedError (409 Conflict) handling on deletion in `apps/server/prompts/views.py`
- [ ] T008 [US1] Register `/api/categories/` router endpoints in `apps/server/prompts/urls.py`
- [ ] T009 [US1] Write unit tests for PromptCategory CRUD and ON DELETE Restrict validation in `apps/server/prompts/tests/test_category_crud.py`

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently (MVP ready!)

---

## Phase 4: User Story 2 - Prompt ↔ PromptCategory Relationship & Search API (Priority: P2)

**Goal**: Update Prompt CRUD & search APIs to require mandatory category, and support filtering by `category`, `category_slug`, and legacy `task` parameter.

**Independent Test**: Create Prompt with category FK, and filter prompts by category ID/slug/task parameter.

### Implementation for User Story 2

- [ ] T010 [P] [US2] Update `PromptSerializer` and `PromptDetailSerializer` to serialize `category` in `apps/server/prompts/serializers.py`
- [ ] T011 [P] [US2] Update `PromptFilterSet` to filter by `category`, `category_slug`, and legacy `task` query parameters in `apps/server/prompts/filters.py`
- [ ] T012 [US2] Update `PromptViewSet` to validate mandatory category and handle category filters in `apps/server/prompts/views.py`
- [ ] T013 [US2] Write unit tests for Prompt-Category relationship mapping and filtering search in `apps/server/prompts/tests/test_category_prompt_relation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 work independently and in integration

---

## Phase 5: User Story 3 - Category Prompt Count Aggregation & Testing (Priority: P3)

**Goal**: Include `prompt_count` aggregate metadata in category list API, and verify 100% test pass rate.

**Independent Test**: Fetch category list and verify `prompt_count` matches linked prompts.

### Implementation for User Story 3

- [ ] T014 [US3] Update `PromptCategoryViewSet.get_queryset()` to annotate `prompt_count=Count('prompts')` in `apps/server/prompts/views.py`
- [ ] T015 [US3] Update `PromptCategorySerializer` to include `prompt_count` field in `apps/server/prompts/serializers.py`
- [ ] T016 [US3] Add unit test cases for `prompt_count` aggregation in `apps/server/prompts/tests/test_category_crud.py`

**Checkpoint**: All user stories are independently functional and fully tested

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Mechanical linter, static type check, and quickstart end-to-end validation

- [ ] T017 [P] Run code formatting, linting, and static type checks (`uv run ruff check ; uv run ruff format ; uv run mypy .`)
- [ ] T018 Run full automated test suite (`uv run pytest apps/server/prompts/tests/`)
- [ ] T019 Validate scenario execution using `specs/005-prompt-category-api/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) → User Story 2 (P2) → User Story 3 (P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T006 [P] [US1] (serializers) can run in parallel with T009 skeleton setup
- T010 [P] [US2] (serializers) and T011 [P] [US2] (filters) can run in parallel
- T017 [P] (linter/typecheck) can run in parallel with documentation checks

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - ORM models and migrations)
3. Complete Phase 3: User Story 1 (PromptCategory CRUD API)
4. **STOP and VALIDATE**: Test User Story 1 independently (`test_category_crud.py`)

### Incremental Delivery

1. Foundation ready (Phase 1 + 2)
2. Deliver US1 (PromptCategory CRUD MVP)
3. Deliver US2 (Prompt-Category Relation & Search)
4. Deliver US3 (Prompt Count Aggregation & Full Test Suite)
5. Polish & Verification (Phase 6)
