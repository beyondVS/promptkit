# Tasks: Prompt Version(이력 관리 및 롤백) API 개발

**Input**: Design documents from `/specs/006-prompt-version-api/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prompt-version-api.json, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure verification

- [X] T001 Verify project structure and spec documents in `specs/006-prompt-version-api/`
- [X] T002 [P] Verify `uv` environment and Django dependencies in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core ORM models and schema migrations that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Verify `Version` ORM model constraints (`UniqueConstraint(fields=["prompt", "version_number"])` and ordering `["prompt", "-version_number"]`) in `apps/server/prompts/models.py`
- [X] T004 Verify Django Schema Migrations for `Version` model in `apps/server/prompts/migrations/`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Prompt Version Auto-Generation & History List/Detail (Priority: P1) 🎯 MVP

**Goal**: Automatically create immutable Version snapshot on Prompt update (with Skip Creation check for unchanged text), and provide list/detail REST API endpoints.

**Independent Test**: Update Prompt template_text, verify new Version snapshot is created, and query GET `/api/v1/prompts/{prompt_id}/versions/` independently.

### Implementation for User Story 1

- [X] T005 [P] [US1] Create `VersionSerializer` in `apps/server/prompts/serializers.py`
- [X] T006 [US1] Implement Prompt creation/update hook to auto-create `Version` snapshot (with Skip Creation logic for unchanged template_text) in `apps/server/prompts/serializers.py` and `apps/server/prompts/views.py`
- [X] T007 [US1] Implement `VersionViewSet` (list and retrieve actions, 405 Method Not Allowed for PUT/PATCH/DELETE) in `apps/server/prompts/views.py`
- [X] T008 [US1] Register `/api/v1/prompts/{prompt_id}/versions/` router endpoints in `apps/server/prompts/urls.py`
- [X] T009 [US1] Write unit tests for Version auto-creation, list, and detail retrieval in `apps/server/prompts/tests/test_version_api.py`

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently (MVP ready!)

---

## Phase 4: User Story 2 - Rollback to Past Version (Priority: P2)

**Goal**: Provide rollback API to copy target version template_text and issue a new latest version (Append-Only) with optional/auto changelog.

**Independent Test**: Call POST `/api/v1/prompts/{prompt_id}/versions/rollback/` with `target_version=1`, verify new version v3 is created with v1 content.

### Implementation for User Story 2

- [X] T010 [P] [US2] Create `RollbackRequestSerializer` in `apps/server/prompts/serializers.py`
- [X] T011 [US2] Implement `rollback` action on `VersionViewSet` (copying target version template_text and issuing new version with optional/auto changelog) in `apps/server/prompts/views.py`
- [X] T012 [US2] Register `/api/v1/prompts/{prompt_id}/versions/rollback/` endpoint in `apps/server/prompts/urls.py`
- [X] T013 [US2] Write unit tests for Rollback action (verifying Append-Only creation and 404 for invalid target_version) in `apps/server/prompts/tests/test_version_api.py`

**Checkpoint**: At this point, User Stories 1 AND 2 work independently and in integration

---

## Phase 5: User Story 3 - Version Structured Line Diff Comparison & Testing (Priority: P3)

**Goal**: Provide Diff comparison API returning line-by-line Structured JSON diff between two versions using `difflib`.

**Independent Test**: Call GET `/api/v1/prompts/{prompt_id}/versions/diff/?from_version=1&to_version=2` and verify line diff JSON array response.

### Implementation for User Story 3

- [X] T014 [P] [US3] Create `VersionDiffResponseSerializer` and `difflib` line parsing helper function in `apps/server/prompts/serializers.py`
- [X] T015 [US3] Implement `diff` action on `VersionViewSet` (parsing `from_version` & `to_version` and returning Structured Line Diff) in `apps/server/prompts/views.py`
- [X] T016 [US3] Add unit test cases for Version Diff comparison in `apps/server/prompts/tests/test_version_api.py`

**Checkpoint**: All user stories are independently functional and fully tested

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Mechanical linter, static type check, and quickstart end-to-end validation

- [X] T017 [P] Run code formatting, linting, and static type checks (`uv run ruff check ; uv run ruff format ; uv run mypy .`)
- [X] T018 Run full automated test suite (`uv run pytest apps/server/prompts/tests/`)
- [X] T019 Validate scenario execution using `specs/006-prompt-version-api/quickstart.md`

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
- T005 [P] [US1] (serializers) can run in parallel with T009 test setup
- T010 [P] [US2] (serializers) can run in parallel with T012 url routing
- T014 [P] [US3] (diff parsing helper) can run in parallel with T016 test skeleton
- T017 [P] (linter/typecheck) can run in parallel with documentation checks

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (`Version` ORM model constraints)
3. Complete Phase 3: User Story 1 (Version Auto-Generation & History List/Detail)
4. **STOP and VALIDATE**: Test User Story 1 independently (`test_version_api.py`)

### Incremental Delivery

1. Foundation ready (Phase 1 + 2)
2. Deliver US1 (Version History List/Detail MVP)
3. Deliver US2 (Rollback Action API)
4. Deliver US3 (Structured Line Diff API & Full Test Suite)
5. Polish & Verification (Phase 6)
