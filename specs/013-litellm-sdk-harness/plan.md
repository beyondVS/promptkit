# Implementation Plan: LiteLLM Adapter and SDK Harness

**Branch**: `013-litellm-sdk-harness` | **Date**: 2026-08-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-litellm-sdk-harness/spec.md`

## Summary

Add a public, stateless LiteLLM adapter to the framework-agnostic PromptKit core SDK. It will reuse existing section ordering, role validation, sectionless fallback, safe system-only warning, and immutable-input policies, then return plain `messages` arguments usable with LiteLLM's completion call. Add a focused public SDK integration-harness test module that checks the package-root export inventory, coverage-map drift, complete retrieval-to-compilation-to-all-adapter journeys, public model behavior, and exception contracts using only mock transports.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Existing Pydantic v2 and httpx; standard-library `logging` and `typing`; no LiteLLM runtime dependency

**Storage**: N/A; all conversion and harness data is deterministic and in-memory

**Testing**: pytest, existing `unittest.TestCase` SDK unit style, Ruff, and MyPy strict mode

**Target Platform**: Python environments supported by the independently installable PromptKit core SDK

**Project Type**: Framework-agnostic Python library in a Django monorepo

**Performance Goals**: LiteLLM conversion of a valid 200-section prompt completes in under one second; the complete core SDK suite has zero failures

**Constraints**: Exact text and ordering fidelity; no LLM/provider/registry call beyond mock transport; no LiteLLM import; no model, credentials, settings, source metadata, or rendered prompt text in generated arguments/logs; every declared package-root export has a two-way checked harness mapping

**Scale/Scope**: One adapter class, two LiteLLM typed dictionary contracts, package-root exports, README usage, extension of adapter unit tests, and one integration-harness test module for the resulting 37-name public surface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-design | Post-design evidence |
|---|---|---|
| Prompt Registry Focus | PASS | Adapter maps a local compiled prompt to arguments only; it adds no LLM call, model selection, credential, token, or cost feature. |
| Framework-agnostic SDK Core | PASS | Changes stay under `packages/promptkit` and `tests/promptkit`; no Django, server, or LiteLLM package import is introduced. |
| Client-side compilation and adapters | PASS | The adapter consumes the existing completed prompt and never re-renders variables; output is plain invocation data only. |
| Lightweight/self-hosted | PASS | The design adds no runtime dependency, external service, cache, tracing, or provider execution path. |
| Language and public typing | PASS | Python 3.13+ typing is retained for the public adapter and argument contracts; Pydantic remains the input validation boundary. |
| Public API quality | PASS | A coverage map is checked in both directions against `promptkit.__all__`, and all public behavior is exercised through package-root imports. |
| Output integrity and minimum change | PASS | Existing shared conversion helpers are reused; only adapter exports, focused tests, documentation, and design artifacts change. |

No constitution violation requires an exception. The Phase 1 contracts preserve all gates.

## Project Structure

### Documentation (this feature)

```text
specs/013-litellm-sdk-harness/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── sdk-litellm-and-public-harness.md
└── tasks.md             # Created later by /speckit-tasks, not by this command
```

### Source Code (repository root)

```text
packages/promptkit/
├── README.md                              # LiteLLM conversion-only usage boundary
└── src/promptkit/
    ├── __init__.py                        # package-root public exports
    ├── adapters.py                        # shared policies plus LiteLLM conversion
    ├── exceptions.py                      # existing AdapterConversionError hierarchy
    └── models.py                          # existing immutable compiled prompt input

tests/promptkit/
├── integration/
│   └── test_public_sdk_harness.py         # export map and cross-component public journey
└── unit/
    └── test_adapters.py                   # LiteLLM exact mapping and shared adapter policies
```

**Structure Decision**: Keep LiteLLM in the existing small adapter module because it shares the same ordered role/content contract as existing conversion paths. Keep the public-surface harness in `tests/promptkit/integration` so it tests cross-component behavior without replacing focused unit coverage. A provider subpackage, adapter hierarchy, or live LiteLLM dependency would expand scope without adding value to this conversion-only increment.

## Complexity Tracking

No constitution violations or complexity exceptions require justification.
