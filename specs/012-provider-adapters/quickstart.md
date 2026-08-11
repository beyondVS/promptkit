# Quickstart: Validate Gemini and OpenAI Prompt Adapters

## Prerequisites

- Python 3.13+
- uv
- The Day 11 `CompiledPrompt` implementation in the current working tree
- No Gemini/OpenAI package, API key, or network access is required

## Run focused automated checks

From the repository root:

```powershell
uv sync
uv run pytest tests/promptkit/unit/test_adapters.py
uv run ruff check packages/promptkit tests/promptkit
uv run ruff format --check packages/promptkit tests/promptkit
uv run mypy packages/promptkit tests/promptkit
```

Expected result: all adapter contract tests, lint, formatting, and strict type checks pass without a
provider SDK import or external request. Run `uv run pytest` afterward for full regression coverage.

## Validate the three public mappings

Create an immutable `CompiledPrompt` whose deliberately unordered sections contain two system
items plus user and assistant items. Call all three methods documented in
[contracts/sdk-provider-adapters.md](contracts/sdk-provider-adapters.md).

Expected result:

- every output follows the exact target dictionary shape;
- sections resolve by ascending `order`;
- Gemini maps assistant to `model` and wraps every text in one `parts` item;
- Chat Completions preserves all four sections as separate messages;
- Responses and Gemini join the two system texts with exactly `\n\n`;
- input text, source metadata, and the source model remain unchanged.

## Validate fallback, fidelity, and failures

Run parameterized fixtures for an empty section tuple, consecutive equal roles, empty/whitespace/
multiline/Unicode text, a duplicate order, and blank/differently-cased/unknown roles.

Expected result: sectionless input becomes one exact user item; valid text and repeated role
boundaries remain unchanged; each invalid prompt raises `AdapterConversionError`, identifies the
offending role or order without including content, and produces no mapping.

## Validate the unified system-only policy

For each public method, convert a prompt containing only multiple system sections while capturing
the adapter logger and Python runtime warnings.

Expected result: the provider-specific system-only mapping is returned, exactly one WARNING record
contains slug/version/label but none of the compiled texts, no `warnings.warn` record exists, and
no exception or provider request occurs.

## Validate performance and local-only behavior

Build a valid 200-section prompt and time each conversion independently using
`time.perf_counter()`.

Expected result: each method completes in under one second. The test module must not configure
provider clients or credentials; successful execution with only core SDK dependencies confirms the
conversion boundary remains local and independently installable.
