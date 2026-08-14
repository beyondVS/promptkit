# Implementation Plan: Django SDK Integration Setup

**Branch**: `014-django-sdk-integration` | **Date**: 2026-08-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/014-django-sdk-integration/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Create the independently installable `promptkit-django` distribution. It reads one
`PROMPTKIT` Django settings mapping, validates it eagerly during application startup,
and stores one configured `PromptKitClient` on the Django application-config instance.
The public accessor returns that instance without lazy construction. Package and
contract tests cover validation, lifecycle identity, secret redaction, and Git
subdirectory installation with the core SDK resolved from a locally built wheel.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, promptkit 0.1.x, Pydantic v2

**Storage**: N/A; configuration is read from the active Django settings object

**Testing**: pytest, pytest-django, isolated `uv` environment subprocesses for package-install verification

**Target Platform**: Python/Django applications on supported Python 3.13+ platforms

**Project Type**: independently distributed Django integration library in a Python monorepo

**Performance Goals**: one in-memory client construction per Django application lifecycle; no registry request during initialization

**Constraints**: eager startup validation; no lazy construction; unknown settings fail startup; no API-key disclosure; no dependency from core SDK to Django; no LLM, cache, retry, or server behavior

**Scale/Scope**: one default client per Django Apps registry; `BASE_URL`, `API_KEY`, and optional `TIMEOUT`; no named clients or runtime reconfiguration

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Principle / gate | Plan response | Status |
|---|---|---|
| Prompt Registry Focus | The integration only configures the existing read-only client; it creates no prompts and calls no LLM. | Pass |
| SDK-first framework separation | All Django imports and lifecycle behavior live in `packages/promptkit-django`; core `packages/promptkit` remains unchanged. | Pass |
| Lightweight and self-hosted | No new service, database, cache, tracing, retry, or provider dependency is introduced. | Pass |
| Public API and typing | The distribution exposes only the settings contract, accessor, and integration errors with type hints and docstrings. | Pass |
| Independent deployment | Packaging has direct runtime declarations and a Git-subdirectory test resolves the core distribution from a wheelhouse, never a sibling path. | Pass |
| Security | Validation reports field names only and never renders API-key values in errors, representations, or test output. | Pass |
| Testability | Unit and lifecycle tests run without a registry request; packaging validation runs in a fresh environment. | Pass |

## Project Structure

### Documentation (this feature)

```text
specs/014-django-sdk-integration/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
packages/
├── promptkit/                         # Existing framework-agnostic core SDK
└── promptkit-django/
    ├── pyproject.toml
    ├── README.md
    └── src/promptkit_django/
        ├── __init__.py                # Deliberate public exports
        ├── apps.py                    # Eager Django AppConfig registration
        ├── configuration.py            # Settings mapping validation
        ├── exceptions.py               # Safe integration-specific errors
        ├── registry.py                 # AppConfig-scoped client access
        └── py.typed

tests/
└── promptkit_django/
    ├── unit/
    │   ├── test_configuration.py
    │   └── test_registry.py
    └── integration/
        ├── test_django_lifecycle.py
        └── test_git_subdirectory_install.py
```

**Structure Decision**: Add one isolated library package and its tests. The
existing core SDK and Prompt Server stay untouched except for the monorepo
workspace lock metadata needed to recognize the new package.

## Complexity Tracking

No constitution violations or exception justifications are required.
