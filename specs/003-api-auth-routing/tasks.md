# Tasks: API Routing and API Key Authentication Setup

**Input**: Design documents from `specs/003-api-auth-routing/`

**Prerequisites**: [plan.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/plan.md) (required), [spec.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/spec.md) (required for user stories), [research.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/research.md), [data-model.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/data-model.md), [contracts/auth-routing-api.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/contracts/auth-routing-api.md)

**Tests**: Included per PromptKit Constitution authentication verification rules.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or non-conflicting chunks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Core package structure initialization and DRF settings configuration

- [ ] T001 Create `core` package structure in `apps/server/core/` (`__init__.py`, `views.py`, `auth.py`)
- [ ] T002 Configure `REST_FRAMEWORK` and `PROMPTKIT_API_KEY` settings in `apps/server/config/settings.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Base test harness structure for authentication views

- [ ] T003 Setup core authentication test module structure in `tests/server/test_auth.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - API Key Request Authentication & Route Protection (Priority: P1) 🎯 MVP

**Goal**: Implement `APIKeyAuthentication` backend to inspect request headers and reject unauthenticated requests with 401 Unauthorized errors.

**Independent Test**: Send valid vs invalid API key requests to a protected endpoint and verify 200 OK vs 401 Unauthorized response codes.

### Tests for User Story 1

- [ ] T004 [P] [US1] Add unit tests for valid/invalid/missing API Key authentication scenarios in `tests/server/test_auth.py`

### Implementation for User Story 1

- [ ] T005 [P] [US1] Implement `APIKeyAuthentication` backend extending DRF `BaseAuthentication` in `apps/server/core/auth.py`
- [ ] T006 [US1] Implement protected test endpoint `ProtectedTestView` in `apps/server/core/views.py`

**Checkpoint**: User Story 1 fully functional and testable independently.

---

## Phase 4: User Story 2 - API Key Header Specification & Flexible Key Handling (Priority: P2)

**Goal**: Establish clean HTTP URL routing structure (`/api/v1/`) and public vs protected endpoint routing.

**Independent Test**: Verify public access to `/api/v1/health/` returns 200 OK without requiring authentication headers.

### Tests for User Story 2

- [ ] T007 [P] [US2] Add unit tests for `/api/v1/health/` public access and URL routing in `tests/server/test_auth.py`

### Implementation for User Story 2

- [ ] T008 [P] [US2] Implement public health check view `HealthCheckView` in `apps/server/core/views.py`
- [ ] T009 [US2] Configure `/api/v1/` routing inclusion and endpoints in `apps/server/config/urls.py`

**Checkpoint**: User Stories 1 AND 2 functional independently.

---

## Phase 5: User Story 3 - Mechanical Quality Harness & Static Analysis Integration (Priority: P3)

**Goal**: Pass all Ruff linter/formatter rules and MyPy strict static type checks across auth and routing modules.

**Independent Test**: Run `uv run ruff check`, `uv run ruff format`, and `uv run mypy .` with zero errors reported.

### Implementation for User Story 3

- [ ] T010 [P] [US3] Add strict type annotations to `apps/server/core/auth.py`, `apps/server/core/views.py`, and `apps/server/config/urls.py`
- [ ] T011 [US3] Run Ruff check/format and MyPy static analysis verification across codebase

---

## Phase 6: Polish & Verification

**Purpose**: Quality verification and quickstart validation

- [ ] T012 Run full pytest test suite `uv run pytest tests/server/test_auth.py` and verify zero failures
- [ ] T013 Perform manual HTTP verification per `specs/003-api-auth-routing/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion
- **User Story 2 (Phase 4)**: Depends on Phase 3 completion
- **User Story 3 (Phase 5)**: Depends on Phase 4 completion
- **Polish (Phase 6)**: Depends on Phase 5 completion

### Parallel Opportunities

- T004, T005 can run in parallel (Test vs Auth backend code)
- T007, T008 can run in parallel (Health test vs Health view)
- T010 can run in parallel with T012

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup (T001, T002) + Foundational (T003)
2. Complete User Story 1 (T004, T005, T006)
3. Validate User Story 1 independently with test execution

### Incremental Delivery

1. Setup + Foundational -> Core auth package and test harness ready
2. User Story 1 -> `APIKeyAuthentication` backend & protected endpoint (MVP)
3. User Story 2 -> `/api/v1/health/` public route & URL structure
4. User Story 3 -> Ruff & MyPy static analysis alignment
5. Polish -> Test suite pass & quickstart validation
