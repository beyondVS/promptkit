# Implementation Plan: Prompt Version(이력 관리 및 롤백) API 개발

**Branch**: `006-prompt-version-api` | **Date**: 2026-07-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-prompt-version-api/spec.md`

## Summary

`Prompt` 모델의 템플릿 수정 시 이력을 불변(Immutable) 상태로 추적 관리하는 `Version` API 및 과거 버전 원복(Rollback), 버전 간 라인 단위 차이점 비교(Diff) API를 개발합니다. Django REST Framework(DRF) 기반으로 버전 목록/상세 조회, 롤백(Append-Only 방식의 신규 버전 발행), `difflib` 기반 라인 Diff 비교 엔드포인트를 제공하고, 100% 자동화 유닛 테스트를 구축합니다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework (DRF), Pydantic v2, `difflib` (Python Standard Library)

**Storage**: PostgreSQL (개발/테스트용 SQLite 호환), Django ORM

**Testing**: pytest, `django.test.TestCase` (서버 ORM 및 DRF API 테스트용) 및 `unittest.TestCase` (유틸리티 Diff 파싱 테스트용)

**Target Platform**: Linux Server / Containerized Environment

**Project Type**: web-service (`apps/server` Django REST Server)

**Performance Goals**: 버전 목록/상세 조회 및 Diff 비교 연산 response latency < 1.0s

**Constraints**:
- `Version` 엔티티는 생성 후 수정/삭제가 불가능한 불변(Immutable) 스냅샷.
- (Prompt, Version Number) 복합 고유성 제약조건 (`UniqueConstraint`).
- 롤백 시 기존 이력 훼손 없이 과거 버전을 복사하여 신규 버전(`latest + 1`)을 발행하는 Append-Only 방식.
- Constitution 원칙 I에 따라 LLM 호출/호스팅 로직은 일절 포함하지 않음 (Pure Prompt Registry).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Prompt Registry Focus**: LLM Gateway 기능 없이 프롬프트 버전 저장, 이력 관리, 롤백 및 Diff 비교 역할에만 집중하는가? -> **PASSED**
- [x] **II. SDK-First & Framework Agnostic**: 서버 코드가 `apps/server/` 내에 명확히 모듈화되어 있는가? -> **PASSED**
- [x] **III. Prompt Compilation & Adapters**: 버전 스냅샷 저정 및 전달에만 집중하는가? -> **PASSED**
- [x] **IV. Label-Driven Resolution**: 기본 라벨 제공 규칙 및 버전 관리 체계를 이탈하지 않는가? -> **PASSED**
- [x] **V. Lightweight & Self-Hosted First**: 범위 외 모듈(Tracing, Evaluation 등) 없이 버전 이력 및 Diff 비교에 최소화되어 있는가? -> **PASSED**
- [x] **개발 및 코드 품질 제어**: Ruff, MyPy, pytest 하네스 및 Type Hints 사용 지침 준수하는가? -> **PASSED**

## Project Structure

### Documentation (this feature)

```text
specs/006-prompt-version-api/
├── plan.md              # 이 문서 (구현 설계서)
├── research.md          # Phase 0 연구 및 기술 결정 사항
├── data-model.md        # Phase 1 데이터 모델 및 ERD 명세
├── quickstart.md        # Phase 1 검증 가이드
└── contracts/           # Phase 1 API 사양서 (OpenAPI JSON)
    └── prompt-version-api.json
```

### Source Code (repository root)

```text
apps/server/
├── prompts/
│   ├── models.py        # Version ORM 모델 및 UniqueConstraint 확인/정비
│   ├── serializers.py   # VersionSerializer, RollbackSerializer, VersionDiffSerializer
│   ├── views.py         # VersionViewSet (list, retrieve, rollback, diff action)
│   ├── urls.py          # /api/v1/prompts/{prompt_id}/versions/ Nested Router 등록
│   └── tests/           # Version 이력 관리, 롤백, Diff 비교 유닛 테스트
│       └── test_version_api.py
```

**Structure Decision**: Django REST Framework 하이브리드 아키텍처 규격을 준수하여 `apps/server/prompts/` 앱 내에 Version 시리얼라이저, 뷰셋 액션 및 유닛 테스트를 모듈화하여 배치합니다.

## Complexity Tracking

> **Constitution Check 결과 모든 GATE 항목을 위반 없이 100% 준수하였으므로 정당화가 필요한 추가 복잡성이 없습니다.**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | N/A | N/A |
