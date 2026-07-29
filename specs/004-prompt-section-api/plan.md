# Implementation Plan: Prompt & Section CRUD 및 다차원 검색 API 개발

**Branch**: `004-prompt-section-api` | **Date**: 2026-07-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-prompt-section-api/spec.md`

## Summary

Prompt 및 Section 엔티티의 생성, 조회, 수정, 삭제(CRUD) RESTful API 엔드포인트를 Django REST Framework(DRF) 기반으로 구축하고, 프롬프트 이름(Name) 키워드 부분 일치 검색, 업무 분류(Task) 지정 검색, 복수 태그(Tags, AND 조건) 조합 검색을 지원하는 다차원 검색 엔진 및 유닛 테스트 세트를 구현합니다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework (DRF), Pydantic v2

**Storage**: PostgreSQL (개발/테스트용 SQLite 호환), Django ORM

**Testing**: pytest, `django.test.TestCase` (서버 ORM 테스트용) 및 `unittest.TestCase` (유틸리티 테스트용)

**Target Platform**: Linux Server / Containerized Environment

**Project Type**: web-service (`apps/server` Django REST Server)

**Performance Goals**: 100건 이상 프롬프트 검색 필터링 시 response latency < 1.0s

**Constraints**:
- 프롬프트 이름(`name`)은 시스템 전체에서 중복될 수 없음 (`unique=True`).
- 복수 태그 검색 조건은 모든 태그를 만족해야 하는 AND 매칭 적용.
- Constitution 원칙 I에 따라 LLM 호출/호스팅 로직은 일절 포함하지 않음 (Pure Prompt Registry).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Prompt Registry Focus**: LLM Gateway 기능 없이 프롬프트 저장, 조회, 검색 역할에만 집중하는가? -> **PASSED**
- [x] **II. SDK-First & Framework Agnostic**: 서버 코드가 `apps/server/`에 국한되어 있는가? -> **PASSED**
- [x] **III. Prompt Compilation & Adapters**: 컴파일 오버헤드를 서버에 전가하지 않고 단순 데이터 전달에 집중하는가? -> **PASSED**
- [x] **IV. Label-Driven Resolution**: 기본 라벨 제공 규칙을 따르는가? -> **PASSED**
- [x] **V. Lightweight & Self-Hosted First**: 비본질적 추가 모듈(Tracing, Evaluation 등) 없이 범위가 최소화되어 있는가? -> **PASSED**
- [x] **개발 및 코드 품질 제어**: Ruff, MyPy, pytest 하네스 및 Type Hints 사용 지침 준수하는가? -> **PASSED**

## Project Structure

### Documentation (this feature)

```text
specs/004-prompt-section-api/
├── plan.md              # 이 문서 (구현 설계서)
├── research.md          # Phase 0 연구 및 기술 결정 사항
├── data-model.md        # Phase 1 데이터 모델 및 ERD 명세
├── quickstart.md        # Phase 1 검증 가이드
└── contracts/           # Phase 1 API 사양서 (OpenAPI JSON)
    └── prompt-api.json
```

### Source Code (repository root)

```text
apps/server/
├── prompts/
│   ├── models.py        # Prompt, Section ORM 모델 확장 (task, tags, unique constraints)
│   ├── serializers.py   # PromptSerializer, PromptDetailSerializer, SectionSerializer
│   ├── views.py         # PromptViewSet, SectionViewSet (CRUD 및 다차원 검색 필터)
│   ├── filters.py       # PromptFilterSet (icontains, exact, AND tag matching)
│   ├── urls.py          # DRF Router URL 매핑
│   └── tests/           # CRUD 및 다차원 검색 API 유닛 테스트 (django.test.TestCase)
│       ├── test_prompt_crud.py
│       ├── test_section_crud.py
│       └── test_search.py
```

**Structure Decision**: Django REST Framework 하이브리드 아키텍처 규격을 준수하여 `apps/server/prompts/` 앱 내에 모델, 시리얼라이저, 뷰, 필터셋 및 유닛 테스트를 모듈화하여 배치합니다.

## Complexity Tracking

> **Constitution Check 결과 모든 GATE 항목을 위반 없이 100% 준수하였으므로 정당화가 필요한 추가 복잡성이 없습니다.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |
