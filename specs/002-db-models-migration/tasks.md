# Tasks: DB Modeling and Migrations

**Input**: Design documents from `specs/002-db-models-migration/`

**Prerequisites**: [plan.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/plan.md) (required), [spec.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/spec.md) (required for user stories), [research.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/research.md), [data-model.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/data-model.md), [contracts/orm-schema.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/contracts/orm-schema.md)

**Tests**: Included per PromptKit Constitution model verification rules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or non-conflicting chunks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Django application structure initialization

- [x] T001 Create `prompts` Django app directory structure in `apps/server/prompts/`
- [x] T002 Register `apps.server.prompts` in `INSTALLED_APPS` within `apps/server/config/settings.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core model test structure setup

- [x] T003 Setup Django test module structure in `tests/server/test_models.py` using `django.test.TestCase`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Prompt & Version Core Entity Storage (Priority: P1) 🎯 MVP

**Goal**: Store top-level prompt definitions and maintain immutable version records (`Prompt` and `Version` models) in a 1:N relationship.

**Independent Test**: Create a `Prompt` and multiple `Version` instances in test database and verify relationship, unique version numbers, and cascading deletion.

### Tests for User Story 1

- [x] T004 [P] [US1] Add ORM model unit tests for `Prompt` and `Version` creation, 1:N linking, and unique version constraint in `tests/server/test_models.py`

### Implementation for User Story 1

- [x] T005 [P] [US1] Implement `Prompt` ORM model (slug, name, description, timestamps) in `apps/server/prompts/models.py`
- [x] T006 [US1] Implement `Version` ORM model with 1:N FK to `Prompt`, `version_number`, `template_text`, `changelog`, and `unique_prompt_version_number` constraint in `apps/server/prompts/models.py`

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - Label-Based Version Tagging & Resolution (Priority: P2)

**Goal**: Tag prompt versions with release labels (`production`, `draft`, `dev`) with unique label constraint per prompt.

**Independent Test**: Assign `production` label to a version and verify `UniqueConstraint(fields=['prompt', 'name'])` prevents duplicate active labels per prompt.

### Tests for User Story 2

- [x] T007 [P] [US2] Add ORM model unit tests for `Label` creation, version targeting, and `unique_label_per_prompt` constraint in `tests/server/test_models.py`

### Implementation for User Story 2

- [x] T008 [US2] Implement `Label` ORM model with foreign keys to `Prompt` and `Version` and composite unique constraint `[prompt, name]` in `apps/server/prompts/models.py`

**Checkpoint**: User Stories 1 AND 2 functional independently.

---

## Phase 5: User Story 3 - Variable Definitions & Prompt Structure Sections (Priority: P3)

**Goal**: Store dynamic variable parameter specifications (`VariableDefinition`) and structured prompt message sections (`Section`) linked 1:N to `Version`.

**Independent Test**: Create variable definitions and section ordering for a prompt version and verify type/ordering unique constraints.

### Tests for User Story 3

- [x] T009 [P] [US3] Add ORM model unit tests for `VariableDefinition` (var_type choices, unique name) and `Section` (role choices, unique order) in `tests/server/test_models.py`

### Implementation for User Story 3

- [x] T010 [P] [US3] Implement `VariableDefinition` ORM model with `var_type` choices, required flag, default value, and `unique_variable_per_version` constraint in `apps/server/prompts/models.py`
- [x] T011 [P] [US3] Implement `Section` ORM model with `role` choices, ordering index, content block, and `unique_section_order_per_version` constraint in `apps/server/prompts/models.py`

**Checkpoint**: All 5 models (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section`) and 1:N relationships complete.

---

## Phase 6: Migrations & Admin

**Purpose**: Database schema migration file generation and Django Admin registration

- [x] T012 Generate initial Django migration script `0001_initial.py` by executing `uv run python apps/server/manage.py makemigrations prompts`
- [x] T013 [P] Register all 5 models in Django Admin in `apps/server/prompts/admin.py`

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality verification and quickstart validation

- [x] T014 Run full pytest test suite `uv run pytest tests/server/test_models.py` and verify zero failures
- [x] T015 Perform manual verification using Django shell per `specs/002-db-models-migration/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion
- **User Story 3 (Phase 5)**: Depends on Phase 3 completion (can run in parallel with Phase 4 if staffed)
- **Migrations & Admin (Phase 6)**: Depends on Phase 3, Phase 4, Phase 5 completion
- **Polish (Phase 7)**: Depends on Phase 6 completion

### Parallel Opportunities

- T004, T005 can run in parallel (Test vs Model file structure)
- T007, T009 can run in parallel (Tests for US2 and US3)
- T010, T011 can run in parallel (VariableDefinition vs Section model classes)
- T013 can run in parallel with T014

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup (T001, T002) + Foundational (T003)
2. Complete User Story 1 (T004, T005, T006)
3. Validate User Story 1 independently with test execution

### Incremental Delivery

1. Setup + Foundational -> Django app and test harness ready
2. User Story 1 -> `Prompt` & `Version` models (MVP)
3. User Story 2 -> `Label` model & version resolution
4. User Story 3 -> `VariableDefinition` & `Section` models
5. Migrations & Polish -> `0001_initial.py` migration script & quickstart validation
