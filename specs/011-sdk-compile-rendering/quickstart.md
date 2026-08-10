# Quickstart: Validate SDK Local Prompt Compilation

## Prerequisites

- Python 3.13+
- uv
- The Day 11 SDK implementation in the current working tree

## Run automated checks

From the repository root:

```powershell
uv sync
uv run pytest tests/promptkit/unit
uv run ruff check packages/promptkit tests/promptkit
uv run ruff format --check packages/promptkit tests/promptkit
uv run mypy packages/promptkit
```

Expected result: isolated SDK tests, lint, formatting, and strict type checks pass. The compile tests must cover each successful type, defaults, repeated and absent variables, all defined failures, one-pass rendering, and metadata preservation.

## Verify a successful local compilation

Create a retrieved-prompt fixture with `{{ customer_name }}` declared as a required string, then compile it with a text value.

Expected result: aggregate content and every section contain the value, no placeholder remains, and the result keeps the original slug, version, and label. The test must assert no request transport or LLM-provider call occurs.

## Verify validation and safety failures

Run fixtures that omit a required value, provide an undeclared key, provide a wrong strict type, contain malformed delimiters, and reference an undeclared variable.

Expected result: each fixture raises the matching typed error, does not include supplied values in its message, and returns no completed prompt. Add a fixture whose text value itself contains `{{ another_name }}`; expected output contains that literal text unchanged after a single render pass.

## Verify default behavior

Use variables with valid stored defaults for all four types and omit caller values. Then use an invalid stored default.

Expected result: valid defaults are rendered after type normalization; an invalid default raises an invalid-variable-type error and yields no result. A valid caller value overrides a default.

## Validation record

Validated on 2026-08-10 with the project virtual environment (Python 3.13.9):

- `uv run pytest` — 57 passed
- `uv run ruff check` — passed
- `uv run ruff format --check` — passed
- `uv run mypy .` — passed with no issues in 78 source files
