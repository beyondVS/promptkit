# Tasks: Monorepo & Django PostgreSQL Setup

**Input**: Design documents from `specs/001-monorepo-django-setup/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- File paths are explicitly specified in task descriptions.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic workspace setup

- [ ] T001 Define root `pyproject.toml` with `uv` workspace members (`apps/server`, `packages/*`) and Python 3.13+ requirement
- [ ] T002 Create `.env.example` file specifying PostgreSQL and Django configuration variables per `contracts/env-contract.md`
- [ ] T003 [P] Configure `.gitignore` to prevent tracking `.env`, `.venv`, and build artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can be tested and run

- [ ] T004 Create Django project structure in `apps/server` with settings module in `apps/server/config`
- [ ] T005 Configure `pyproject.toml` dependencies for Django 5.x, Django REST Framework, psycopg v3, and django-environ
- [ ] T006 [P] Configure Ruff, MyPy, and Pytest configuration blocks in `pyproject.toml`
- [ ] T007 Configure `apps/server/config/settings.py` to dynamically load PostgreSQL credentials from `.env`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Monorepo Virtual Environment & Dependency Synchronization (Priority: P1) 🎯 MVP

**Goal**: Enable developer to synchronize monorepo virtual environment and dependencies using `uv sync`

**Independent Test**: Run `uv sync` from repository root and verify `.venv` is populated without errors

### Implementation for User Story 1

- [ ] T008 [P] [US1] Run `uv sync` to lock dependencies in `uv.lock` and build `.venv` environment
- [ ] T009 [US1] Create unit test in `tests/unit/test_workspace.py` to verify Python 3.13+ version and workspace isolation

**Checkpoint**: User Story 1 is independently testable via `uv sync` and pytest unit test

---

## Phase 4: User Story 2 - Django Application Structure Creation under `apps/server` (Priority: P1)

**Goal**: Establish Django application structure under `apps/server` capable of running management commands and tests

**Independent Test**: Run `uv run python apps/server/manage.py check` to verify Django setup

### Implementation for User Story 2

- [ ] T010 [P] [US2] Configure URL routing in `apps/server/config/urls.py` and WSGI/ASGI entrypoints
- [ ] T011 [US2] Create integration test in `tests/integration/test_server_app.py` using `django.test.TestCase` to verify Django application initialization

**Checkpoint**: User Story 2 is independently testable via Django system check and integration test

---

## Phase 5: User Story 3 - PostgreSQL Database Connection & Migration Environment (Priority: P1)

**Goal**: Connect Django server to PostgreSQL database and execute database migrations successfully

**Independent Test**: Run `uv run python apps/server/manage.py check --database default` and `migrate`

### Implementation for User Story 3

- [ ] T012 [P] [US3] Implement database connection health check logic in `apps/server/config/settings.py`
- [ ] T013 [US3] Execute `uv run python apps/server/manage.py migrate` and create integration test in `tests/integration/test_db_connection.py` to verify PostgreSQL schema state

**Checkpoint**: User Story 3 is independently testable via DB migration and integration test

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate code quality, formatting, and quickstart documentation

- [ ] T014 [P] Run full harness check (`uv run ruff check ; uv run ruff format --check ; uv run mypy . ; uv run pytest`) and ensure 0 exit code
- [ ] T015 Execute end-to-end validation procedure documented in `specs/001-monorepo-django-setup/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - Can proceed sequentially (US1 → US2 → US3) or in parallel
- **Polish (Phase 6)**: Depends on completion of all User Stories

### Parallel Opportunities

- T003 (gitignore) in Phase 1 can run in parallel with T001/T002
- T006 (harness config) in Phase 2 can run in parallel with T004/T005
- T008 (US1), T010 (US2), T012 (US3) can run in parallel once Foundational Phase completes
- T014 (Harness check) in Phase 6 can run in parallel with T015 validation

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup (Phase 1)
2. Complete Foundational (Phase 2)
3. Complete User Story 1 (Phase 3)
4. Validate `uv sync` and workspace test

### Incremental Delivery

1. Setup + Foundational → Base environment ready
2. Add US1 → `uv sync` & workspace isolation verified (MVP)
3. Add US2 → Django app structure & settings verified
4. Add US3 → PostgreSQL connection & migration verified
5. Polish → Harness checks (0 error) & quickstart validation
