# Tasks: promptkit 프로젝트 컨셉 재정의 및 문서화

**Input**: Design documents from `/specs/007-redefine-concept-docs/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/sdk-server-api.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Server App**: `apps/server/prompts/`, `apps/server/config/`
- **Documentation**: `constitution.md`, `AGENTS.md`, `README.md`, `docs/project_plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project environment validation and test harness configuration

- [x] T001 Verify project dependencies and environment setup using `uv sync`
- [x] T002 [P] Create test directory structure for dashboard and API tests in `apps/server/prompts/tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user stories can be implemented

- [x] T003 Configure Django Session Authentication and Login redirect URL settings in `apps/server/config/settings.py`
- [x] T004 [P] Implement `PROMPTKIT_API_KEY` environment variable reader and authentication helper in `apps/server/prompts/auth.py`
- [x] T005 [P] Setup base URL routing for dashboard (`/dashboard/`) and API (`/api/v1/`) in `apps/server/config/urls.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Django Template 대시보드 CUD 및 세션 인증 (Priority: P1) 🎯 MVP

**Goal**: 프롬프트 관리자가 Django Session Auth 기반으로 대시보드에 로그인하여 프롬프트/카테고리 생성, 수정, 삭제(CUD) 및 버전 관리를 수행할 수 있도록 구현

**Independent Test**: 대시보드 로그인 후 프롬프트 CUD 조작이 가능하며, `PROMPTKIT_API_KEY`로는 대시보드 진입이 403으로 차단됨을 검증

### Implementation for User Story 1

- [x] T006 [P] [US1] Create Django Session Auth Login and Logout view handling in `apps/server/prompts/views/dashboard.py`
- [x] T007 [P] [US1] Create Django HTML Templates for dashboard login and prompt list in `apps/server/prompts/templates/prompts/login.html` and `apps/server/prompts/templates/prompts/prompt_list.html`
- [x] T008 [P] [US1] Create Django HTML Templates for prompt create/update/delete forms in `apps/server/prompts/templates/prompts/prompt_form.html` and `apps/server/prompts/templates/prompts/prompt_confirm_delete.html`
- [x] T009 [US1] Implement Prompt & Category CUD View logic in `apps/server/prompts/views/dashboard.py` (depends on T006, T007, T008)
- [x] T010 [US1] Register dashboard URL routing in `apps/server/prompts/urls.py`
- [x] T011 [US1] Add unit & integration tests for Dashboard CUD and Session Auth isolation in `apps/server/prompts/tests/test_dashboard.py`

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently (MVP Complete)

---

## Phase 4: User Story 2 - 서버측 Read-only 프롬프트 조회 API 및 Header 인증 (Priority: P2)

**Goal**: `promptkit-server`에 SDK가 사용할 Read-only Fetch 전용 REST API 엔드포인트와 `X-PromptKit-Api-Key` HTTP Header 인증 기능 제공

**Independent Test**: cURL 또는 HTTP 클라이언트를 사용한 Read-only API 호출 및 API Key 불일치 시 401 오류 반환, CUD API 요청 시 405/403 차단 검증

### Implementation for User Story 2

- [x] T012 [P] [US2] Create DRF Serializer for Read-only prompt details response in `apps/server/prompts/serializers.py`
- [x] T013 [P] [US2] Implement Read-only Fetch API View with `X-PromptKit-Api-Key` Header authentication check in `apps/server/prompts/views/api.py`
- [x] T014 [US2] Register Read-only API URL routing (`/api/v1/prompts/<slug>/`) in `apps/server/prompts/urls.py`
- [x] T015 [US2] Add unit & integration tests for Read-only API and API Key header validation in `apps/server/prompts/tests/test_read_only_api.py`

**Checkpoint**: User Story 1 and 2 are both functional and testable independently

---

## Phase 5: User Story 3 - 프로젝트 핵심 문서 및 일정 로드맵 최신화 (Priority: P3)

**Goal**: 재정의된 아키텍처 사양(대시보드 CUD, SDK Read-only, 인증 분리)에 맞추어 거버넌스 및 프로젝트 핵심 문서 전면 최신화

**Independent Test**: 최신화된 각 문서 내 대시보드 CUD, SDK Read-only, `.env` 인증 규칙의 정합성 확인

### Implementation for User Story 3

- [x] T016 [P] [US3] Update project governance principles in `.specify/memory/constitution.md`
- [x] T017 [P] [US3] Update AI agent guidelines and architecture constraints in `AGENTS.md`
- [x] T018 [P] [US3] Update project overview, architecture diagram, and SDK usage in `README.md`
- [x] T019 [P] [US3] Update remaining documentation files under `docs/` to reflect new architecture boundaries in `docs/`
- [x] T020 [US3] Reorganize milestones and update uncompleted schedule tasks in `docs/project_plan.md`

**Checkpoint**: All user stories and documentation updates are completed

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality checks, linter verification, and end-to-end validation

- [x] T021 [P] Run code formatting and static type analysis using `uv run ruff check ; uv run ruff format ; uv run mypy .`
- [x] T022 Run full test suite using `uv run pytest`
- [x] T023 Execute quickstart validation guide scenarios per `specs/007-redefine-concept-docs/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational phase completion
  - US1 (Dashboard CUD) → US2 (Server Read-only API) → US3 (Docs Update)
- **Polish (Phase 6)**: Depends on all user stories being complete

### Parallel Opportunities

- T002, T004, T005 in Setup & Foundational can run in parallel
- Within US1: T006, T007, T008 (Views and Templates) can run in parallel
- Within US2: T012, T013 can run in parallel
- Within US3: T016, T017, T018, T019 can run in parallel
