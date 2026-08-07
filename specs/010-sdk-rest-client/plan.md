# Implementation Plan: SDK Remote Prompt Retrieval

**Branch**: `010-sdk-rest-client` | **Date**: 2026-08-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-sdk-rest-client/spec.md`

## Summary

Create the framework-agnostic `promptkit` Python package as an independently installable workspace member. Its synchronous client will retrieve one published prompt from the existing read-only registry endpoint, validate the response into typed models, and return precise exceptions without retries, redirects, fallback resolution, or LLM calls. The package will use a 10-second caller-overridable timeout, explicit API-key configuration, HTTPS or loopback HTTP URL validation, and isolated `httpx.MockTransport` tests.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Pydantic v2 for public response models and validation; httpx for synchronous HTTP transport

**Storage**: N/A; the SDK holds request configuration and retrieved prompt data only

**Testing**: pytest with `httpx.MockTransport`; root Ruff and MyPy configuration

**Target Platform**: Python applications on supported desktop, server, and CI platforms

**Project Type**: Framework-agnostic Python library in a uv monorepo workspace

**Performance Goals**: One synchronous request per fetch; default total wait limit of 10 seconds; no automatic retries

**Constraints**: Read-only GET operation; API key supplied explicitly at client construction; HTTPS required except loopback HTTP; redirects rejected; `production` label rejected before transport; no caching, compilation, adapters, framework integration, or LLM invocation

**Scale/Scope**: One new package member, one public synchronous client, typed prompt models and error hierarchy, isolated unit tests, and a Git-subdirectory installation verification guide

## Constitution Check

| Gate | Status | Evidence |
|---|---|---|
| Prompt Registry Focus | PASS | Client exposes only prompt retrieval; no CUD or LLM calls. |
| SDK-First & Framework Agnostic | PASS | `packages/promptkit` has no Django, DRF, or `promptkit-django` dependency. |
| Client-Side Compilation Boundary | PASS | This slice transports template sections and variable declarations only; it does not render on the server or add compilation work. |
| Label-Driven Resolution | PASS | Omitted label delegates to on-live; explicit labels are sent unchanged except forbidden `production`, with no fallback. |
| Lightweight & Self-Hosted First | PASS | Uses only Pydantic and httpx; no tracing, analytics, caching engine, or workflow system. |
| Security & public API quality | PASS | Explicit API-key input, no key serialization, URL preflight, disabled redirects, type hints, Pydantic models, and isolated tests. |
| Independent deployment | PASS | Package-owned `pyproject.toml`, `src/` layout, and Git subdirectory install verification are planned. |

**Post-design re-check**: PASS. The design introduces no constitutional exception. The existing server read contract is consumed as-is; no server CUD, migration, or framework package work is required.

## Project Structure

### Documentation (this feature)

```text
specs/010-sdk-rest-client/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── sdk-client-api.md
```

### Source Code (repository root)

```text
packages/
└── promptkit/
    ├── pyproject.toml
    ├── README.md
    └── src/
        └── promptkit/
            ├── __init__.py
            ├── client.py
            ├── exceptions.py
            └── models.py

tests/
└── promptkit/
    └── unit/
        ├── test_client.py
        └── test_models.py
```

**Structure Decision**: Add a standalone `packages/promptkit` workspace member with a `src` layout. Keep protocol code, typed models, and public errors inside the package; keep its isolated tests under the existing `tests/promptkit/unit/` skeleton. Do not create compile, adapter, Django, cache, or async modules in this Day 10 slice.

## Complexity Tracking

No constitution violations or additional complexity justifications are required.
