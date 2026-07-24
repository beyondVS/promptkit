# Implementation Plan: Monorepo & Django PostgreSQL Setup

**Branch**: `001-monorepo-django-setup` | **Date**: 2026-07-24 | **Spec**: [spec.md](file:///D:/Projects/Private/promptkit/specs/001-monorepo-django-setup/spec.md)

**Input**: Feature specification from `specs/001-monorepo-django-setup/spec.md`

## Summary

`uv` 패키지 매니저 기반의 모노레포 워크스페이스 구조를 생성하고 `apps/server` 경로에 Django REST Framework 서버 프로젝트를 셋업합니다. 환경 변수(`.env`)를 통해 PostgreSQL 데이터베이스에 접속하도록 구성하며, Ruff, MyPy, Pytest 기계적 하네스 검증 환경을 일괄 구축합니다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x+, Django REST Framework, psycopg (v3), python-dotenv / django-environ

**Storage**: PostgreSQL 16+

**Testing**: pytest, pytest-django, unittest

**Target Platform**: Linux / Windows / macOS Server (Self-hosted)

**Project Type**: Monorepo (`apps/server`, `packages/promptkit`, `packages/promptkit-django`)

**Performance Goals**: `uv sync` 의존성 동기화 시간 < 10s, Django DB 마이그레이션 및 헬스 체크 < 3s

**Constraints**: 환경 변수 기반 비밀 관리 (`.env` 노출 금지), Ruff/MyPy 린트 및 정적 타입 0 error PASS

**Scale/Scope**: Day 01 모노레포 셋업 및 Django PostgreSQL 연결 초기화

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Prompt Registry Focus**: LLM 직접 호출 로직 없음 (Registry 서버 인프라에만 집중)
- [x] **II. SDK-First & Framework Agnostic**: `packages/promptkit`과 Django 연동 패키지/서버를 완벽 분리
- [x] **III. Prompt Compilation & Adapters**: 서버단 컴파일 과부하 없음
- [x] **IV. Label-Driven Resolution**: 기본 라벨 규약 준수
- [x] **V. Lightweight & Self-Hosted First**: 불필요한 서드파티 통합 없음
- [x] **개발 표준 & 보안**: API 키 및 DB 자격 증정 `.env` 처리, 하드코딩 금지
- [x] **기계적 하네스 준수**: 패키지 매니저는 오직 `uv`만 사용, Ruff/MyPy/Pytest 검증 수행

## Project Structure

### Documentation (this feature)

```text
specs/001-monorepo-django-setup/
├── plan.md              # Implementation plan (/speckit-plan output)
├── research.md          # Technical decisions & rationale (Phase 0)
├── data-model.md        # Configuration & Workspace entity specs (Phase 1)
├── quickstart.md        # Feature validation guide (Phase 1)
└── contracts/           # Environment & DB connection contracts (Phase 1)
    ├── env-contract.md
    └── db-health-contract.md
```

### Source Code (repository root)

```text
.env.example             # Environment variable template
pyproject.toml           # Monorepo root workspace configuration
uv.lock                  # Lockfile for reproducible installs

apps/
└── server/              # Django Registry Server
    ├── config/          # Django settings & routing
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── manage.py

packages/
├── promptkit/           # Core framework-agnostic Python SDK
└── promptkit-django/    # Django integration package

tests/                   # Unit & integration test suites
```

**Structure Decision**: Monorepo 구조를 채택하여 `apps/server`에 Django 서버 애플리케이션을 격리하고, `packages/` 경로에 SDK 코어 및 Django 연동 패키지를 전용 모듈로 구성합니다.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*(Constitution Check 항목 중 위반 사항 없음 - PASS)*
