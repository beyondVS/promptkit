# Database Health & Connection Contract Specification

## Overview

본 계약서는 Django 서버와 PostgreSQL 데이터베이스 간의 연결 상태 확인 및 검증 방식을 정의합니다.

---

## 1. Connection Verification Command Contract

### Command
```bash
uv run python apps/server/manage.py check --database default
```

### Expected Output
- **Success**: 0 exit code, `System check identified no issues (0 silenced).`
- **Failure**: Non-zero exit code, `django.db.utils.OperationalError` 관련 로그 출력

---

## 2. Migration Execution Contract

### Command
```bash
uv run python apps/server/manage.py migrate
```

### Expected Behavior
- PostgreSQL 데이터베이스에 `django_migrations` 및 기본 테이블 스키마가 성공적으로 적용되어야 한다.
- 재실행 시 idempotency(동일성)를 유지하여 `No migrations to apply.` 결과를 반환해야 한다.
