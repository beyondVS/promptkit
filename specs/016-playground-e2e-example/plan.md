# Implementation Plan: Playground Compilation and Gemini E2E Example

**Branch**: `016-playground-e2e-example` | **Date**: 2026-08-18 | **Spec**: [spec.md](spec.md)

**Input**: Day 16 Playground SDK compilation preview and real Prompt Server-to-SDK-to-Gemini E2E example.

## Summary

Extend the existing staff-only `DashboardPlaygroundView` to handle a CSRF-protected POST on its current URL. A dynamic Django form converts browser strings into the strict SDK variable types, while a small dashboard service maps the selected ORM `Version` into the public `RetrievedPrompt` contract and calls `compile()` exactly once. The view re-renders HTML with either an immutable `CompiledPrompt` preview or field/template errors; it performs no provider call or persistence.

Add a self-contained `examples/gemini-e2e/` consumer project that retrieves an on-live prompt through `PromptKitClient`, compiles it, converts it with `GeminiAdapter`, and invokes `google-genai` only when `--live` is explicitly present. The example owns `google-genai>=2.18.1,<3`; neither the core SDK nor Prompt Server gains provider execution responsibility.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.2.16, Django REST Framework 3.17.1, Pydantic 2.13.4, HTTPX 0.28.1; example-only `google-genai>=2.18.1,<3`

**Storage**: Existing PostgreSQL prompt/version/section/variable data; preview inputs and compiled results are request-local and never stored

**Testing**: pytest, pytest-django, Django `TestCase` with `setUpTestData`, `unittest.mock`/injected fakes for registry and Gemini boundaries

**Target Platform**: Self-hosted Django dashboard and a cross-platform synchronous Python CLI example run through `uv`

**Project Type**: Django registry web application plus framework-agnostic SDK and an isolated consumer example in a Python monorepo

**Performance Goals**: A valid local Playground compilation renders within 2 seconds; non-live and automated example runs make zero Gemini requests; a live run makes exactly one Gemini request

**Constraints**: Existing Playground URL and session/staff authorization remain; POST remains CSRF protected; no internal compilation API, browser compiler, database write, LLM call from Django or SDK, prompt CUD from the example, secret logging, or core provider dependency

**Scale/Scope**: One selected prompt version and its ordered sections/variables per request; one synchronous E2E retrieval/compile/adapter/provider journey; text-only, non-streaming response; no migration or new persistent model

## Constitution Check

*GATE: Passed before Phase 0 research and re-checked after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Prompt Server remains a registry, not an LLM gateway | Pass | Dashboard POST performs only request-local SDK compilation. Gemini invocation exists solely in consumer example code. |
| Core SDK remains framework agnostic and read-only | Pass | Django form/ORM mapping stays under `apps/server`; the example consumes existing public retrieval, compilation, and adapter APIs. |
| Compilation and adapters retain their constitutional roles | Pass | `RetrievedPrompt.compile()` performs rendering; `GeminiAdapter` only reshapes `CompiledPrompt`; the example-owned client performs the provider call. |
| Label resolution preserves the on-live/no-fallback policy | Pass | The E2E example calls `fetch(slug)` without a label and stops on missing on-live deployment; Playground compiles only its explicitly selected dashboard version. |
| Lightweight/self-hosted boundary is preserved | Pass | `google-genai` is confined to an isolated example project and bounded below major version 3; no provider dependency enters core or server runtime. |
| Secrets and output integrity are protected | Pass | CSRF/session/staff controls remain; environment variables own credentials; errors and logs exclude submitted values, compiled text, and keys. |
| Public behavior and core logic are mechanically tested | Pass | Django database/view tests cover preview contracts; isolated example tests replace external boundaries; live verification is explicit and separate. |

## Project Structure

### Documentation (this feature)

```text
specs/016-playground-e2e-example/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── playground-preview.md
│   └── gemini-e2e-cli.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/server/
├── pyproject.toml                              # Declare compatible core promptkit dependency
└── prompts/
    ├── forms.py                                # Dynamic, typed, non-persisting Playground form
    ├── services/
    │   ├── __init__.py                         # Dashboard service package boundary
    │   └── playground.py                       # ORM-to-RetrievedPrompt mapping and compile orchestration
    ├── views/dashboard.py                      # Existing GET plus CSRF-protected POST rendering
    ├── templates/prompts/playground.html       # Named inputs, submit action, errors, compiled preview
    └── tests/test_dashboard_playground.py      # Staff/CSRF/compile/error/no-write view coverage

examples/gemini-e2e/
├── .env.example                                # Secret-free example configuration contract
├── pyproject.toml                              # Isolated promptkit + google-genai dependency contract
├── uv.lock                                     # Reproducible example-only dependency lock
├── README.md                                   # Safe setup and live invocation guide
└── gemini_e2e.py                               # Fetch → compile → adapt → optional single live call

tests/
├── examples/
│   └── test_gemini_e2e.py                      # Fake-boundary orchestration and secret-safety tests
└── promptkit/integration/
    └── test_public_sdk_harness.py               # Public SDK import regression assertions

uv.lock                                         # Updated server/core dependency lock
```

**Structure Decision**: Keep Playground web concerns in the existing Django app, with form parsing and ORM-to-SDK conversion separated from the thin CBV. Keep live provider execution in an independently configured example project. The core SDK source and public contracts require no feature change.

## Complexity Tracking

No constitution violations require complexity justification.
