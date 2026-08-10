# Implementation Plan: SDK Local Prompt Compilation

**Branch**: `011-sdk-compile-rendering` | **Date**: 2026-08-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-sdk-compile-rendering/spec.md`

## Summary

Add `RetrievedPrompt.compile()` to render the registry's `{{ variable_name }}` placeholders
entirely in the framework-agnostic SDK. A constrained native parser validates every template
before one-pass rendering. A Pydantic v2 runtime model validates declared `string`, `number`,
`boolean`, and JSON object/array values, applies valid defaults, rejects unknown input, and
returns a traceable `CompiledPrompt`. The SDK does not call an LLM, transmit values, or add a
template-engine dependency.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Pydantic v2 (existing); standard library `re`, `json`, and typing

**Storage**: N/A; compilation input and output are in-memory only

**Testing**: pytest isolated SDK unit tests; Ruff; MyPy strict mode

**Target Platform**: Python application environments supported by the SDK

**Project Type**: framework-agnostic Python library

**Performance Goals**: compile a valid prompt with up to 50 variables and 200 placeholders in under one second

**Constraints**: local-only rendering; no LLM call, prompt CUD, server rendering, cache, adapter, or new runtime dependency; no partial output on failure; no supplied values in error messages

**Scale/Scope**: one retrieved prompt at a time; four declared types; one simple placeholder grammar; existing SDK package and unit-test suite only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|---|---|---|
| Prompt Registry Focus | PASS | The registry remains read-only; compilation uses only retrieved data and caller values locally. |
| Framework-agnostic SDK Core | PASS | Changes stay within `packages/promptkit`; no Django imports or server changes. |
| Client-side compilation and adapters | PASS | This delivers local `compile()` only; provider adapter conversion and LLM calls remain out of scope. |
| Lightweight/self-hosted | PASS | Uses existing Pydantic and the Python standard library; no additional dependency or service. |
| Public API quality | PASS | Typed public result/errors and isolated unit tests will cover the compile surface. |

## Project Structure

### Documentation (this feature)

```text
specs/011-sdk-compile-rendering/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
packages/promptkit/
└── src/promptkit/
    ├── __init__.py             # public result/error exports
    ├── compiler.py             # parser, schema construction, validation, rendering
    ├── exceptions.py           # compile-specific typed errors
    └── models.py               # RetrievedPrompt.compile and CompiledPrompt

tests/promptkit/unit/
├── conftest.py                 # retrieved-prompt fixtures
└── test_compiler.py            # public compile success/error coverage
```

**Structure Decision**: Keep compile orchestration at `RetrievedPrompt.compile()` so fetched prompts are directly usable. Isolate parsing and Pydantic model creation in one pure SDK module for fast unit testing; do not touch the Django server or add a package.

## Complexity Tracking

No constitution violations or complexity exceptions require justification.
