# Research & Technical Decisions: Monorepo & Django PostgreSQL Setup

## Overview

본 문서는 Day 01 피처(모노레포 셋업 및 Django PostgreSQL 연동) 구현을 위해 검토된 기술적 결정 사항과 근거를 기록합니다.

---

## 1. Monorepo & Virtual Environment (`uv` Workspace)

### Decision
`uv` 패키지 매니저의 Workspace 기능(`[tool.uv.workspace]`)을 채택하여 모노레포 가상환경을 중앙에서 통제합니다.

### Rationale
- `uv`는 기존 `pip` / `poetry` / `pipenv` 대비 10~100배 빠른 의존성 조율 및 설치 속도를 제공합니다.
- `pyproject.toml` 루트 파일에서 `members = ["apps/*", "packages/*"]` 형태로 선언함으로써 `apps/server`, `packages/promptkit`, `packages/promptkit-django` 간의 독립적 개발과 하위 의존성 관리가 단일 `uv.lock`으로 투명하게 일관성을 유지할 수 있습니다.

### Alternatives Considered
- **Poetry Monorepo Workspaces**: 속도가 상대적으로 느리고 Python 3.13+ 지원 커스텀 빌드 오버헤드가 있음.
- **Pipenv / Virtualenv 다중 분리**: 패키지 간 로컬 개발 링크(`pip install -e`) 관리가 복잡해짐.

---

## 2. Django Server Architecture under `apps/server`

### Decision
`apps/server` 경로에 Django 5.x REST Framework 기반 프로젝트를 구성합니다. 설정 디렉토리는 `apps/server/config` 또는 `apps/server/server`로 배치하여 모노레포 구조에 맞게 커스터마이징합니다.

### Rationale
- Prompt 레지스트리 역할에 충실하기 위해 데이터베이스 접근, Admin 인터페이스, REST API 서빙에 가장 검증된 Django REST Framework를 기반으로 채택합니다.
- 프로젝트 루트 디렉토리와 분리된 `apps/server` 구조를 통해 프레임워크 종속성을 서버 영역에만 격리합니다.

### Alternatives Considered
- **FastAPI / SQLAlchemy**: 빠른 async 서빙이 장점이나 Admin 및 ORM 마이그레이션 생태계 생체 비용이 증가하여 Prompt Registry 관리에 Django 대비 오버헤드 발생.

---

## 3. Database Adapter & Environment Variables

### Decision
PostgreSQL 연동 어댑터로 `psycopg` (v3)를 사용하며, 환경 변수 로더로 `python-dotenv` / `django-environ`을 채택합니다.

### Rationale
- `psycopg` v3는 Python 3.13+과의 호환성이 뛰어나며 Django 5.x의 공식 권장 어댑터입니다.
- 프로젝트 헌법 (Constitution Rule: Absolute Security)에 따라 API 키, DB 비밀번호, Host 정보는 하드코딩되지 않고 `.env` 파일 및 시스템 환경 변수를 통해서만 로드됩니다.
- 배포 및 로컬 실행용 예시 파일로 `.env.example`을 제공합니다.

### Alternatives Considered
- **psycopg2-binary**: Python 3.13 환경에서 일부 C extension 컴파일 및 스레딩 이슈 가능성이 있으므로 최신 psycopg v3 우대.

---

## 4. Harness & Code Quality Pipeline

### Decision
- **Linter / Formatter**: Ruff (`uv run ruff check`, `uv run ruff format`)
- **Type Checker**: MyPy (`uv run mypy .`)
- **Test Framework**: Pytest + pytest-django (`uv run pytest`)

### Rationale
- 프로젝트 헌법 및 `AGENTS.md`에 명시된 하네스 명령어를 100% 만족시킵니다.
- DB 미사용 유틸리티 테스트는 `unittest.TestCase`, DB 연동 테스트는 `django.test.TestCase` + `setUpTestData` 구조로 설계하여 하이브리드 테스트 오버헤드를 최소화합니다.
