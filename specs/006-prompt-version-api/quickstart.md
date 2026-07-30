# Quickstart Validation Guide: Prompt Version(이력 관리 및 롤백) API 개발

**Feature**: [`spec.md`](./spec.md) | **Branch**: `006-prompt-version-api` | **Date**: 2026-07-30

## Prerequisites

- Python 3.13+ (`uv` package manager)
- PostgreSQL 또는 SQLite 개발 데이터베이스

---

## Scenario 1: Version 생성 및 이력 목록/상세 조회 검증

### 1.1 cURL을 통한 Version 목록 조회
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/prompts/1/versions/" \
  -H "X-API-Key: dev-secret-key" \
  -H "Accept: application/json"
```

### 1.2 cURL을 통한 특정 Version 상세 조회
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/prompts/1/versions/1/" \
  -H "X-API-Key: dev-secret-key" \
  -H "Accept: application/json"
```

---

## Scenario 2: 이전 버전으로의 안전한 롤백(Rollback) 검증

### 2.1 과거 버전 v1으로 롤백 요청 (신규 v3 생성)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/prompts/1/versions/rollback/" \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "target_version": 1,
    "changelog": "Rolled back to v1 due to issue in v2"
  }'
```

**Expected Outcome**:
HTTP 201 Created 응답과 함께 `version_number: 3`인 신규 Version 객체가 등록되고, `template_text`는 과거 v1의 내용과 100% 동일함.

---

## Scenario 3: 두 버전 간 Structured Line Diff 비교 검증

### 3.1 Version 1과 Version 2 간의 Diff 비교 요청
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/prompts/1/versions/diff/?from_version=1&to_version=2" \
  -H "X-API-Key: dev-secret-key" \
  -H "Accept: application/json"
```

**Expected Outcome**:
HTTP 200 OK 응답과 함께 라인별 변경점(`added`, `deleted`, `equal`)이 포함된 JSON 배열이 반환됨.

---

## Harness Execution Commands

```bash
# Code Formatting & Linting
uv run ruff check ; uv run ruff format ; uv run mypy .

# Automated Unit Tests Execution
uv run pytest apps/server/prompts/tests/
```
