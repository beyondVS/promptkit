# Phase 1 Quickstart Validation Guide: PromptCategory 독립 모델링 및 관리 API 개발

**Feature**: [`spec.md`](./spec.md) | **Branch**: `005-prompt-category-api` | **Date**: 2026-07-30

본 가이드는 `PromptCategory` CRUD 엔티티 개발 및 `Prompt` 연동 API 변경사항을 검증하기 위한 하네스 및 매뉴얼 테스트 실행 가이드입니다.

---

## 1. Prerequisites & Environment Setup

```bash
# 1. 의존성 및 하네스 환경 동기화
uv sync

# 2. Django 데이터베이스 마이그레이션 적용
uv run python apps/server/manage.py migrate
```

---

## 2. Automated Test Execution (하네스 검증)

모든 API 엔드포인트, 외래키 제약조건(ON DELETE Restrict), 카테고리 필터링 및 하위 호환성 검증 유닛 테스트를 구동합니다.

```bash
# Linting 및 타입 검사
uv run ruff check ; uv run ruff format ; uv run mypy .

# Pytest 유닛 테스트 구동 (django.test.TestCase & unittest.TestCase)
uv run pytest apps/server/prompts/tests/
```

---

## 3. Manual Scenario Validation (cURL / HTTP Test)

### Scenario A: PromptCategory CRUD & Count Validation

```bash
# 1. 신규 카테고리 생성
curl -X POST http://localhost:8000/api/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "고객지원", "slug": "customer-support", "description": "고객 지원용 프롬프트 범주"}'

# Expected Outcome: HTTP 201 Created (id: 1, prompt_count: 0)

# 2. 카테고리 목록 조회 (prompt_count 집계 확인)
curl -X GET http://localhost:8000/api/categories/

# Expected Outcome: HTTP 200 OK (prompt_count 포함 배열)
```

### Scenario B: Prompt-Category Relationship & Mandatory Validation

```bash
# 1. 카테고리 미지정 프롬프트 생성 시도 (Mandatory 검증)
curl -X POST http://localhost:8000/api/prompts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "잘못된 프롬프트", "description": "카테고리 누락"}'

# Expected Outcome: HTTP 400 Bad Request ("category" 필드 필수 에러)

# 2. 유효한 카테고리를 지정하여 프롬프트 생성
curl -X POST http://localhost:8000/api/prompts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "환불 안내 지침", "category": 1, "tags": ["support", "v1"]}'

# Expected Outcome: HTTP 201 Created
```

### Scenario C: Category Deletion Restrict Validation

```bash
# 연결된 프롬프트가 존재하는 카테고리 삭제 시도 (Restrict 검증)
curl -X DELETE http://localhost:8000/api/categories/1/

# Expected Outcome: HTTP 409 Conflict ("Cannot delete category with linked prompts")
```

### Scenario D: Category Filtering & Legacy Search Compatibility Validation

```bash
# 1. category_slug 기반 프롬프트 필터링
curl -X GET "http://localhost:8000/api/prompts/?category_slug=customer-support"

# 2. 레거시 task 파라미터 검색 호환성 검증
curl -X GET "http://localhost:8000/api/prompts/?task=customer-support"

# Expected Outcome: HTTP 200 OK (동일한 카테고리의 프롬프트 목록 반환)
```
