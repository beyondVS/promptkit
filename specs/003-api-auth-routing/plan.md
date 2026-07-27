# Implementation Plan: API Routing and API Key Authentication Setup

**Branch**: `003-api-auth-routing` | **Date**: 2026-07-27 | **Spec**: [spec.md](file:///D:/Projects/Private/promptkit/specs/003-api-auth-routing/spec.md)

**Input**: Feature specification from `specs/003-api-auth-routing/spec.md`

## Summary

Configure Django REST Framework (DRF) settings, implement custom API Key authentication middleware/backend (`X-API-Key`), establish `/api/v1/` URL routing structure with public health check and protected endpoints, and verify codebase via Ruff and MyPy harness checks.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework 3.15+

**Storage**: Environment variables (`PROMPTKIT_API_KEY`) for secret key definition

**Testing**: pytest (`pytest-django`)

**Target Platform**: Linux server / Self-hosted Python 3.13 runtime

**Project Type**: Web service (`apps/server`)

**Performance Goals**: Sub-2ms authentication evaluation overhead per request

**Constraints**: Strict typing via MyPy, zero Ruff linter warnings, no hardcoded API key secrets

**Scale/Scope**: All incoming API requests to `apps/server`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Prompt Registry Focus**: PASS. Authentication secures prompt registry endpoints without LLM gateway overhead.
- **Principle II: SDK-First & Framework Agnostic SDK Core**: PASS. Auth code resides strictly within `apps/server/core/auth.py`.
- **Principle III: Prompt Compilation & Adapters**: PASS. No prompt compilation logic in auth backend.
- **Principle IV: Label-Driven Resolution**: PASS. N/A for auth backend.
- **Principle V: Lightweight & Self-Hosted First**: PASS. Lightweight header-based API key auth without complex OAuth2/session servers.
- **No Hardcoding**: PASS. API Keys loaded via environment variables (`PROMPTKIT_API_KEY`).
- **Zero Tolerance Output Integrity**: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/003-api-auth-routing/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── auth-routing-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code Layout

```text
apps/server/
├── config/
│   ├── settings.py      # DRF DEFAULT_AUTHENTICATION_CLASSES configuration
│   └── urls.py          # /api/v1/ routing inclusion
└── core/                # Core shared server utilities
    ├── __init__.py
    ├── auth.py          # APIKeyAuthentication backend
    ├── views.py         # HealthCheckView & ProtectedTestView
    └── tests/
        └── test_auth.py # Auth & routing unit tests
```

**Structure Decision**: Created `apps/server/core/` package to hold server-wide authentication backends, health-check views, and core middleware utilities.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
