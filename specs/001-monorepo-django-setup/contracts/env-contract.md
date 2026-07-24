# Environment Variables Contract Specification

## Overview

본 계약서는 `apps/server` 애플리케이션 및 모노레포 환경에서 사용하는 필수/선택적 환경 변수의 규격을 정의합니다.

---

## 1. Environment File Location & Rules

- **Target File**: `.env` (프로젝트 루트 및 `apps/server` 경로)
- **Template File**: `.env.example` (git 추적 대상)
- **Rule**: `.env`에 등록된 어떠한 비밀 키나 패스워드도 코드 베이스에 하드코딩될 수 없다.

---

## 2. Schema Specification

```ini
# Django Application Core Settings
SECRET_KEY=django-insecure-change-me-in-production-environment-key-01
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database Configuration
POSTGRES_DB=promptkit
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

---

## 3. Compliance Criteria

1. 개발 및 테스트 시 `.env` 파일이 존재하지 않는 경우 적절한 기본값(로컬 개발용)으로 동작하거나 명확한 안내 오류 메시지를 출력한다.
2. Production 환경(`DEBUG=False`)일 경우 시크릿 키 미설정 시 실행이 즉시 중단되어야 한다.
