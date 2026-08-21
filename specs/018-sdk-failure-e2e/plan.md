# Implementation Plan: SDK Failure Resilience E2E Validation

**Branch**: `018-sdk-failure-e2e` | **Date**: 2026-08-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/018-sdk-failure-e2e/spec.md`

## Summary

Add one focused pytest integration module that starts a disposable Prompt Server through pytest-django's real loopback HTTP server, proves readiness, retrieves a test-owned on-live prompt through the public SDK, and then verifies communication, authentication, credential-configuration, and compilation-variable failures. The suite will assert public exception categories, atomic failure, zero downstream calls, secret-safe exception/application-log content, and no SDK-created logging activity on the scoped fetch/compile failure paths. Existing SDK and server contracts remain unchanged unless the E2E evidence exposes a defect.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework 3.15+, PromptKit core SDK, httpx, Pydantic v2, pytest 8+, pytest-django 4.8+

**Storage**: Pytest-owned transactional SQLite test database by default; test-owned ORM fixtures only, with no persistent or shared data

**Testing**: pytest-django `live_server` for a real loopback HTTP boundary, transactional database access for cross-thread fixture visibility, standard-library sockets for reserved refused-connection and accept-then-close endpoints, and pytest log capture/application test logger for diagnostics

**Target Platform**: Python 3.13+ development and CI environments, including Windows; loopback networking only

**Project Type**: Python monorepo containing a framework-agnostic SDK and a Django registry web service

**Performance Goals**: The focused Day 18 E2E module completes comfortably within one minute under normal local conditions; the full implementation and validation workflow remains feasible within the one-hour session

**Constraints**: uv-only commands; no new dependency, subprocess `runserver`, fixed port, external LLM, production credential, shared server, retry, fallback, tracing, or telemetry backend; every client/socket/server resource must be deterministically closed

**Scale/Scope**: One focused E2E module covering one real-HTTP success setup, one real-HTTP authentication rejection, local credential configuration, refused-connection and mid-request-disconnect server unavailability, three invalid-variable classes, application-owned safe logging, three repeated executions, and selected success regressions

## Constitution Check

*GATE: Passes before Phase 0 research. Re-checked after Phase 1 design: Passes.*

- **Prompt Registry Focus**: The design exercises read-only retrieval and local compilation only. It adds no LLM call, model selection, CUD endpoint, or gateway responsibility.
- **SDK-First & Framework Agnostic Core**: The core SDK gains no Django dependency or test-server helper. Cross-component setup stays in the repository integration suite.
- **Client-side compilation and adapters**: Variable rendering remains inside the SDK. Provider invocation is represented only by a zero-call spy; adapter behavior is not changed.
- **Label-driven resolution**: The controlled prompt is published and on-live. No `latest`, draft, `production`, or fallback substitution is introduced.
- **Lightweight and self-hosted**: The suite uses existing pytest-django/httpx dependencies, loopback networking, and temporary test resources; it adds no observability service or runtime component.
- **Hybrid test architecture**: The feature is an integration/E2E test across real HTTP and ORM boundaries, so pytest-django transactional fixtures are appropriate. Existing server model tests retain `django.test.TestCase` and `setUpTestData` conventions.
- **Independent deployment**: All server lifecycle and Django fixture code remains outside `packages/promptkit`; core runtime dependencies and independent installation remain unchanged.
- **Quality and security**: Test-only sentinel credentials and prompt/variable values prove non-disclosure. No real secret is stored, and the full Ruff, MyPy, and pytest harness remains required.
- **Minimal change**: Current research shows the public exception and atomic compilation contracts already satisfy the feature. Production changes are permitted only as a narrow correction backed by a failing E2E assertion.

## Project Structure

### Documentation (this feature)

```text
specs/018-sdk-failure-e2e/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── failure-resilience-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/server/
├── config/
│   ├── settings.py                 # Test settings and loopback host contract
│   └── urls.py                     # Health and SDK prompt routes
└── prompts/
    ├── auth.py                     # Real 401 authentication boundary
    ├── models.py                   # Test-owned prompt/version data
    └── services/lifecycle.py       # Publish and on-live fixture setup

packages/promptkit/src/promptkit/
├── client.py                       # Public configuration, communication, and auth errors
├── compiler.py                     # Atomic variable validation and rendering
└── exceptions.py                   # Public failure hierarchy

tests/promptkit/
├── integration/
│   ├── test_public_sdk_harness.py  # Existing public success/error regressions
│   └── test_sdk_failure_e2e.py     # New real-HTTP failure-resilience matrix
└── unit/
    ├── test_client.py              # Existing transport/error unit contract
    └── test_compiler.py            # Existing variable validation contract
```

**Structure Decision**: Keep all new implementation in one root-discovered integration test module under `tests/promptkit/integration/`. Use existing server models, lifecycle services, health route, authentication, and public SDK without introducing helpers into a distributable package. If the new E2E test exposes a production defect, modify only the directly responsible SDK or server file and retain the new test as evidence.

## Complexity Tracking

No constitution violations or complexity exceptions are required.
