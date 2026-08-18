# Quickstart: Playground Compilation and Gemini E2E Validation

## Prerequisites

- From the repository root, run `uv sync`.
- Configure the local Django server using `.env`; keep real secrets only in the ignored `.env` file.
- Apply existing migrations and ensure a staff user can access the dashboard.
- Prepare one prompt with declared variables and ordered sections. For live E2E validation, publish it and mark it on-live through the dashboard.
- Obtain separate read-only PromptKit and Gemini API keys. Do not write either key into source, documentation, shell history arguments, or captured test output.

## Playground preview

1. Start the server with `uv run python apps/server/manage.py runserver`.
2. Sign in as staff, open a specific draft or published version, and enter its Playground.
3. Submit valid string, number, boolean, and JSON values. Confirm the response shows the same slug/version, aggregate compiled text, and ordered role sections within 2 seconds.
4. Confirm whitespace and Unicode are preserved, rendered HTML is escaped, and the page states that no LLM call occurred.
5. Submit a missing required value and each invalid type. Confirm values remain editable, the affected field is identified, and no partial preview appears.
6. Use a malformed or declaration-mismatched template. Confirm a safe template error appears without submitted values or prompt text in logs.
7. Compare database state before and after success/failure. Confirm no prompt, version, variable, section, or preview record changes.
8. Repeat POST without a valid CSRF token and as a non-staff user. Confirm Django rejects the requests.

## Non-live E2E example

Set these environment variables through the shell or secret manager:

```text
PROMPTKIT_BASE_URL
PROMPTKIT_API_KEY
PROMPTKIT_PROMPT_SLUG
PROMPTKIT_PROMPT_PARAMS   # optional JSON object
```

Run without the live flag:

```text
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py
```

Confirm the command reports registry, compilation, and adapter completion with safe slug/version identifiers, prints no compiled prompt, and makes zero Gemini calls. Removing on-live publication must stop at the registry stage without draft/latest fallback.

## Explicit live Gemini check

Additionally set `GEMINI_API_KEY` and `GEMINI_MODEL`, then opt in:

```text
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py --live
```

Confirm exactly one Gemini request is made, one non-empty text response is shown, and the client closes. This step can consume quota or incur cost and is never part of default automated validation.

## Automated verification

Run focused tests during implementation:

```text
uv run pytest apps/server/prompts/tests/test_dashboard_playground.py
uv run pytest tests/examples/test_gemini_e2e.py
```

Then run repository quality gates:

```text
uv run ruff check
uv run ruff format --check
uv run mypy .
uv run pytest
```

The automated suite must require no Gemini credentials or provider request and must assert zero non-live calls, exactly one fake live call, stop-on-failure ordering, redaction, CSRF/staff protection, no database writes, and no partial preview.
