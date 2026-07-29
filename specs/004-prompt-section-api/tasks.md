# Tasks: Prompt & Section CRUD 및 다차원 검색 API 개발

**Input**: Design documents from `/specs/004-prompt-section-api/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/prompt-api.json, quickstart.md

**Tests**: 명세서 요구사항에 따라 100% 유닛 테스트 및 정적검증 수용 기준 포함

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 개발 환경 준비 및 기본 구조 확인

- [ ] T001 Verify project environment and dependencies with `uv sync`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 User Story 구현 전에 완료되어야 하는 코어 모델 및 마이그레이션

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Expand Prompt and Section ORM models with `task`, `tags`, and `unique` name constraint in `apps/server/prompts/models.py`
- [ ] T003 Generate and apply Django database migrations in `apps/server/prompts/migrations/`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 프롬프트 및 섹션 생성과 관리 (Priority: P1) 🎯 MVP

**Goal**: Prompt 및 Section의 신규 등록, 상세 조회, 수정, 삭제(CRUD) RESTful API 구축 및 이름 중복 방지 검증

**Independent Test**: `POST /api/v1/prompts/`, `GET /api/v1/prompts/{id}/`, `POST /api/v1/prompts/{id}/sections/` 등을 호출하여 CRUD 동작 및 중복 이름 400/409 오류 검증

### Implementation for User Story 1

- [ ] T004 [P] [US1] Create PromptSerializer and SectionSerializer in `apps/server/prompts/serializers.py`
- [ ] T005 [P] [US1] Implement PromptViewSet CRUD endpoints in `apps/server/prompts/views.py`
- [ ] T006 [P] [US1] Implement SectionViewSet CRUD endpoints in `apps/server/prompts/views.py`
- [ ] T007 [US1] Register API routes for Prompts and Sections in `apps/server/prompts/urls.py`
- [ ] T008 [P] [US1] Write unit test suite for Prompt & Section CRUD operations in `apps/server/prompts/tests/test_prompt_crud.py`

**Checkpoint**: User Story 1 MVP fully functional and testable independently

---

## Phase 4: User Story 2 - 이름, 태그, 업무 기반 다차원 검색 (Priority: P2)

**Goal**: 프롬프트 이름(icontains), 업무 분류(exact), 태그(AND matching) 조건의 다차원 필터링 검색 API 구현

**Independent Test**: 단일/복수 조건 및 복수 태그(`?tags=v1&tags=support`) 지정 검색 시 조건(AND)에 맞는 프롬프트만 정확히 반환되는지 검증

### Implementation for User Story 2

- [ ] T009 [P] [US2] Create PromptFilterSet supporting Name icontains, Task exact, and Tags AND matching in `apps/server/prompts/filters.py`
- [ ] T010 [US2] Connect PromptFilterSet to PromptViewSet in `apps/server/prompts/views.py`
- [ ] T011 [P] [US2] Write unit test suite for multidimensional search API in `apps/server/prompts/tests/test_search.py`

**Checkpoint**: User Stories 1 and 2 work independently

---

## Phase 5: User Story 3 - 검색 결과 정렬 및 응답 유닛 테스트 검증 (Priority: P3)

**Goal**: 검색 결과 생성일시/수정일시 정렬 기능 제공 및 전체 API에 대한 100% 유닛 테스트 검증 통과

**Independent Test**: pytest 구동으로 모든 유닛 테스트 및 정렬 기능 통과 검증

### Implementation for User Story 3

- [ ] T012 [P] [US3] Add OrderingFilter support (`created_at`, `updated_at`, `name`) to PromptViewSet in `apps/server/prompts/views.py`
- [ ] T013 [P] [US3] Write unit test suite for search ordering in `apps/server/prompts/tests/test_ordering.py`

**Checkpoint**: All user stories functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 코드 품질 제어, 린팅, 타입 검사 및 최종 하네스 검증

- [ ] T014 [P] Run linter, formatter and type checker (`uv run ruff check ; uv run ruff format ; uv run mypy .`)
- [ ] T015 Run full test suite (`uv run pytest apps/server/prompts/`) and validate scenarios in `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase
- **User Story 2 (Phase 4)**: Depends on Foundational phase and US1 ViewSet structure
- **User Story 3 (Phase 5)**: Depends on US1 and US2
- **Polish (Phase 6)**: Depends on all user stories completion

---

## Parallel Opportunities

- T004, T005, T006, T008 (US1 Serializers, ViewSets, Tests) can be developed concurrently
- T009 and T011 (FilterSet & Search Tests) can run in parallel
- T012 and T013 (Ordering & Ordering Tests) can run in parallel
- T014 (Linting/Type check) can run in parallel with final verification

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational)
2. Complete Phase 3 (User Story 1 - Prompt & Section CRUD)
3. **VALIDATE**: Run `uv run pytest apps/server/prompts/tests/test_prompt_crud.py`
4. MVP Complete!

### Full Feature Incremental Delivery

1. Foundation ready (Phase 1, 2)
2. MVP Prompt & Section CRUD (Phase 3)
3. Multidimensional Search (Phase 4)
4. Ordering & Test Verification (Phase 5)
5. Quality Control & Polish (Phase 6)
