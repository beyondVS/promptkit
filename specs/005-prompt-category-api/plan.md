# Implementation Plan: PromptCategory(도메인 범주) 독립 모델링 및 관리 API 개발

**Branch**: `005-prompt-category-api` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-prompt-category-api/spec.md`

## Summary

기존 `Prompt` 모델의 단순 문자열 `task` 필드를 정규화된 독립 엔티티인 `PromptCategory`(도메인 카테고리) 모델로 분리 및 구축합니다. `PromptCategory` 엔티티의 CRUD RESTful API 엔드포인트를 Django REST Framework(DRF) 기반으로 신규 작성하고, `Prompt` ↔ `PromptCategory` 간 1:N 외래키(ON DELETE Restrict, Mandatory) 매핑, 카테고리별 연결 프롬프트 개수 집계, 카테고리 ID/슬러그 기반 정밀 필터링 및 레거시 `task` 검색 파라미터 하위 호환 매핑 기능을 구현합니다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework (DRF), Pydantic v2

**Storage**: PostgreSQL (개발/테스트용 SQLite 호환), Django ORM

**Testing**: pytest, `django.test.TestCase` (서버 ORM 및 DRF API 테스트용) 및 `unittest.TestCase` (유틸리티 테스트용)

**Target Platform**: Linux Server / Containerized Environment

**Project Type**: web-service (`apps/server` Django REST Server)

**Performance Goals**: 카테고리 목록 및 프롬프트 카테고리 필터링 조회 시 response latency < 1.0s

**Constraints**:
- `PromptCategory` 이름(`name`) 및 슬러그(`slug`)는 시스템 전체에서 고유함 (`unique=True`).
- 프롬프트 ↔ 카테고리는 외래키(1:N) 필수(Mandatory) 매핑.
- 프롬프트가 1개 이상 연결되어 있는 카테고리는 삭제 불가능 (`ON DELETE Restrict` -> 409 Conflict 반환).
- Constitution 원칙 I에 따라 LLM 호출/호스팅 로직은 일절 포함하지 않음 (Pure Prompt Registry).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Prompt Registry Focus**: LLM Gateway 기능 없이 프롬프트 카테고리 저장, 관리 및 검색 역할에만 집중하는가? -> **PASSED**
- [x] **II. SDK-First & Framework Agnostic**: 서버 코드가 `apps/server/` 내에 명확히 모듈화되어 있는가? -> **PASSED**
- [x] **III. Prompt Compilation & Adapters**: 컴파일 및 LLM 어댑터 오버헤드를 서버에 전가하지 않고 카테고리 메타데이터 전달에 집중하는가? -> **PASSED**
- [x] **IV. Label-Driven Resolution**: 기본 라벨 제공 규칙 및 프롬프트 관리 체계를 이탈하지 않는가? -> **PASSED**
- [x] **V. Lightweight & Self-Hosted First**: 범위 외 모듈(Tracing, Evaluation 등) 없이 카테고리 정규화 및 CRUD에 최소화되어 있는가? -> **PASSED**
- [x] **개발 및 코드 품질 제어**: Ruff, MyPy, pytest 하네스 및 Type Hints 사용 지침 준수하는가? -> **PASSED**

## Project Structure

### Documentation (this feature)

```text
specs/005-prompt-category-api/
├── plan.md              # 이 문서 (구현 설계서)
├── research.md          # Phase 0 연구 및 기술 결정 사항
├── data-model.md        # Phase 1 데이터 모델 및 ERD 명세
├── quickstart.md        # Phase 1 검증 가이드
└── contracts/           # Phase 1 API 사양서 (OpenAPI JSON)
    └── prompt-category-api.json
```

### Source Code (repository root)

```text
apps/server/
├── prompts/
│   ├── models.py        # PromptCategory ORM 모델 추가 및 Prompt Foreign Key (category) 개정
│   ├── serializers.py   # PromptCategorySerializer, PromptCategoryCreateSerializer, PromptSerializer 개정
│   ├── views.py         # PromptCategoryViewSet 추가 및 PromptViewSet 카테고리 매핑/필터링 확장
│   ├── filters.py       # PromptFilterSet (category_id, category_slug, task backward compatibility)
│   ├── urls.py          # /api/categories/ Router URL 등록
│   └── tests/           # Category CRUD, Restrict 삭제, 필터링 유닛 테스트
│       ├── test_category_crud.py
│       └── test_category_prompt_relation.py
```

**Structure Decision**: Django REST Framework 하이브리드 아키텍처 규격을 준수하여 `apps/server/prompts/` 앱 내에 PromptCategory 모델, 시리얼라이저, 뷰셋, 필터셋 및 자동화 유닛 테스트를 모듈화하여 확장 배치합니다.

## Complexity Tracking

> **Constitution Check 결과 모든 GATE 항목을 위반 없이 100% 준수하였으므로 정당화가 필요한 추가 복잡성이 없습니다.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |
