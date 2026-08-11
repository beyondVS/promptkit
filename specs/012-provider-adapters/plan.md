# Implementation Plan: Gemini and OpenAI Prompt Adapters

**Branch**: `012-provider-adapters` | **Date**: 2026-08-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-provider-adapters/spec.md`

## Summary

Add stateless Gemini and OpenAI adapters to the framework-agnostic core SDK. Each adapter
validates and sorts an immutable `CompiledPrompt`, then returns provider-call keyword arguments
as plain Python dictionaries. Gemini targets `google-genai` `generate_content`; one OpenAI
adapter exposes separate Chat Completions and Responses conversions. Shared internal helpers
enforce role validation, duplicate-order rejection, sectionless fallback, and the unified
system-only WARNING without importing provider SDKs or making a request.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Pydantic v2 (existing input models); standard library `logging` and
`typing`; no Gemini or OpenAI runtime dependency

**Storage**: N/A; conversion is deterministic and in-memory only

**Testing**: `unittest.TestCase`-based isolated SDK unit tests executed by pytest; Ruff; MyPy
strict mode

**Target Platform**: Python application environments supported by the independently installable
PromptKit core SDK

**Project Type**: framework-agnostic Python library

**Performance Goals**: in the project test environment, each of the three public methods converts
a valid 200-section prompt in under one second when timed individually with `time.perf_counter()`

**Constraints**: conversion only; exact text preservation; ascending unique order; no source
mutation, provider request, SDK object, provider dependency, model/settings inference, or prompt
text in logs; system-only conversions emit exactly one standard WARNING

**Scale/Scope**: two adapter classes, three public conversion methods, three provider argument
contracts, one conversion error category, and isolated unit tests in the existing core SDK

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-design | Post-design evidence |
|---|---|---|
| Prompt Registry Focus | PASS | Adapters only reshape a local `CompiledPrompt`; no LLM request, model selection, credentials, token, or cost behavior is introduced. |
| Framework-agnostic SDK Core | PASS | All implementation remains under `packages/promptkit` and uses no Django, Prompt Server, or provider SDK import. |
| Client-side compilation and adapters | PASS | The input is the existing completed prompt and outputs are provider argument dictionaries only; rendering is not repeated. |
| Lightweight/self-hosted | PASS | The design adds only standard-library helpers and typed dictionaries, with no service or runtime dependency. |
| Language and public typing | PASS | Python 3.13+ is retained; public adapters, argument shapes, and error are typed. Existing Pydantic v2 models remain the validated input boundary. |
| Public API quality | PASS | Every public method and all FR-012 paths have isolated unit-test coverage, including fidelity, failures, warnings, immutability, and performance. |
| Output integrity and minimum change | PASS | One adapter module, one error addition, public exports, tests, and focused README documentation are sufficient; server and Django packages are untouched. |

No gate violation requires an exception. The Phase 1 contracts preserve all pre-design gates.

## Project Structure

### Documentation (this feature)

```text
specs/012-provider-adapters/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── sdk-provider-adapters.md
└── tasks.md             # Created later by /speckit-tasks, not by this command
```

### Source Code (repository root)

```text
packages/promptkit/
├── README.md                         # public adapter usage and conversion-only boundary
└── src/promptkit/
    ├── __init__.py                   # public adapter, argument type, and error exports
    ├── adapters.py                   # shared validation plus Gemini/OpenAI conversions
    ├── exceptions.py                 # AdapterConversionError
    └── models.py                     # existing immutable CompiledPrompt input models

tests/promptkit/unit/
└── test_adapters.py                  # exact contracts, failures, logging, safety, performance
```

**Structure Decision**: Keep both small, stateless provider mappings in one core SDK module.
Provider-specific classes make the public boundary discoverable, while private shared helpers
prevent the ordering, role, fallback, and logging policies from drifting. A provider subpackage
or abstraction hierarchy is unnecessary for three conversion methods and would add complexity
without current behavior.

## Complexity Tracking

No constitution violations or complexity exceptions require justification.
