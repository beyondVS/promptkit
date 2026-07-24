# Data Model & Configuration Specifications: Monorepo & Django PostgreSQL Setup

## Overview

본 문서는 Day 01 피처에서 다루는 모노레포 워크스페이스 구조, 서버 환경 설정, 그리고 PostgreSQL 데이터베이스 접속 설정 엔티티를 정의합니다.

---

## 1. Monorepo Workspace Configuration Entity (`pyproject.toml`)

### Attributes
- **`project.name`**: `"promptkit-monorepo"`
- **`project.version`**: `"0.1.0"`
- **`requires-python`**: `">=3.13"`
- **`tool.uv.workspace.members`**: `["apps/server", "packages/*"]`

### Validation Rules
- 파이썬 인터프리터 버전은 반드시 3.13 이상이어야 한다.
- 패키지 추가 시 `pip` 직접 설치가 아닌 `pyproject.toml` 및 `uv.lock`에 기록되어야 한다.

---

## 2. Server Environment Configuration Entity (`.env`)

### Attributes

| Environment Variable | Required | Type | Default / Description |
|----------------------|----------|------|-----------------------|
| `SECRET_KEY`         | Yes      | String | Django 애플리케이션 시크릿 키 |
| `DEBUG`              | Yes      | Boolean | `True` (Dev) / `False` (Prod) |
| `ALLOWED_HOSTS`      | No       | List[String] | `localhost,127.0.0.1` |
| `POSTGRES_DB`        | Yes      | String | PostgreSQL DB 이름 (e.g. `promptkit_db`) |
| `POSTGRES_USER`      | Yes      | String | DB 사용자 (e.g. `promptkit_user`) |
| `POSTGRES_PASSWORD`  | Yes      | String | DB 비밀번호 |
| `POSTGRES_HOST`      | Yes      | String | DB 호스트 (e.g. `localhost` or `127.0.0.1`) |
| `POSTGRES_PORT`      | Yes      | Integer | DB 포트 (Default: `5432`) |

### Validation & Security Rules
- `.env` 파일은 레포지토리에 커밋되지 않아야 하며, `.gitignore`에 등록되어야 한다.
- 실제 운영/개발용 환경 변수 구조를 안내하는 예시 파일 `.env.example`이 제공되어야 한다.

---

## 3. Database Connection State Entity (Django `DATABASES`)

### State Transitions
1. **Unconfigured**: 데이터베이스 접속 정보 환경 변수 미로드 상태.
2. **Configured**: `.env`로부터 DB 설정 파싱 완료.
3. **Connected / Migrated**: PostgreSQL 데이터베이스 커넥션 확인 및 Django 초기 마이그레이션(`auth`, `contenttypes`, `sessions` 등) 정상 적용 상태.
4. **Connection Error**: DB 호스트 접속 불가 또는 자격 증명 오류 발생 시 예외 로깅 처리 상태.
