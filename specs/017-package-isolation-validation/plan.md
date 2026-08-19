# Implementation Plan: 모노레포 패키지 격리 및 상호 운용성 검증

**Branch**: `017-package-isolation-validation` | **Date**: 2026-08-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/017-package-isolation-validation/spec.md`

## Summary

세 배포 단위(`promptkit`, `promptkit-django`, Prompt Server)를 매 실행마다 새 산출물로 만들고, 각 산출물 설치와 Git 서브디렉터리 설치를 서로 격리된 환경에서 검증한다. 공통 pytest 배포 하네스가 환경 생성, 의존성 제공, 설치, 공개 import, 최소 동작 및 결과 귀속을 시나리오별로 수행한다. Prompt Server는 먼저 독립 배포에 필요한 코드·템플릿·마이그레이션·실행 진입점이 산출물에 포함되도록 패키징 계약을 정립한다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: uv workspace, Hatchling build backend, pytest, Django, Django REST Framework, `promptkit`, `promptkit-django`

**Storage**: Temporary filesystem for wheelhouse, Git snapshots, and virtual environments; temporary SQLite only for the server smoke configuration

**Testing**: pytest integration tests with standard-library `subprocess` and temporary paths; `uv venv --seed` creates each environment and `uv pip install --python <environment-python>` performs every artifact and local Git installation

**Target Platform**: Windows development environment; commands and assertions keep repository paths out of child-process imports for CI portability

**Project Type**: Python monorepo containing two libraries and one Django web-service distribution

**Performance Goals**: A complete matrix result is readable and release-decidable within 5 minutes; it is not a load or latency benchmark

**Constraints**: uv commands only; fresh wheel and Git-subdirectory paths for all three units; no editable install, repository-root working directory, inherited `PYTHONPATH`, external Prompt Server, database service, or package-index dependency on unpublished `promptkit`; dependency acquisition is separated from wheelhouse-only validation; two SDK/Django requested-install orders must agree

**Scale/Scope**: 3 deployment units, 6 independent installation paths, 2 supported SDK/Django installation orders, and deterministic repeated local execution

## Constitution Check

*GATE: Passes before Phase 0 research. Re-checked after Phase 1 design: Passes.*

- **Prompt Registry Focus**: The harness only performs read-only SDK compilation and a database-free server health smoke. It does not add LLM calls, CUD behavior, or gateway responsibilities.
- **SDK-First & Framework Agnostic Core**: Core SDK artifact tests assert it can be installed and used without Django; Django behavior remains in `promptkit-django`.
- **Client-side compilation and adapters**: The core and integration smoke paths use local fixture data and `compile()` only; no provider SDK or network request is introduced.
- **Label-driven resolution**: Existing public SDK behavior is reused; no label policy is modified.
- **Lightweight and self-hosted**: The test harness uses temporary local resources and no new external service, observability platform, or runtime component.
- **Independent deployment standard**: Both generated artifacts and Git-subdirectory installs are expressly verified. The current unpublished-core policy is handled by supplying a freshly built core wheel through an isolated wheelhouse, never through repository source paths.
- **Quality and security**: The pure subprocess tests remain under `tests/`, use uv for package operations, do not contain real credentials, remove inherited `PYTHONPATH`, verify artifact metadata and installed distribution locations, and expose a single scenario summary.

## Project Structure

### Documentation (this feature)

```text
specs/017-package-isolation-validation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── isolation-validation-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/server/
├── pyproject.toml                    # Server namespace mapping, metadata, and included resources
├── manage.py                         # Installed-runtime-safe startup path when retained
├── config/                           # Django settings, URLs, WSGI/ASGI
├── core/                             # Health and landing application
└── prompts/                          # Registry application, imports, migrations, templates

packages/
├── promptkit/
│   ├── pyproject.toml
│   └── src/promptkit/
└── promptkit-django/
    ├── pyproject.toml
    └── src/promptkit_django/

tests/
└── deployment/
    ├── __init__.py
    ├── helpers.py                    # Temporary artifacts, environments, and subprocess assertions
    └── test_isolated_installation.py # Wheel, Git-subdirectory, and interoperability matrix
```

**Structure Decision**: Preserve the existing monorepo and `apps.server.*` public module identity if Hatchling can map that namespace from the subdirectory build context. Add one focused test package under `tests/` so root pytest discovers it. If namespace mapping alone cannot produce a valid wheel, update the complete affected server runtime surface (`config/`, `core/`, and `prompts/`) rather than assuming `settings.py` and `manage.py` are sufficient. Existing package-level tests remain behavior coverage; the new suite verifies what a consumer actually installs.

## Complexity Tracking

No constitution violations or complexity exceptions are required.
