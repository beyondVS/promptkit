# Quickstart: Validate Playground Variable Form

## Prerequisites

- Use branch `009-playground-variable-form`.
- Run commands through `uv`.
- Prepare a staff user and a prompt with a draft or published version.

## Automated validation

```powershell
uv run pytest apps/server/prompts/tests/test_dashboard_playground.py
uv run ruff check apps/server/prompts
uv run mypy apps/server/prompts
uv run pytest
```

## Manual scenarios

1. Sign in as staff and open a prompt detail page with a selected draft version.
2. Use the Playground link in its toolbar. Confirm the selected prompt/version is identified and no picker appears.
3. Confirm the schema response follows [dashboard-variable-schema.md](contracts/dashboard-variable-schema.md), includes only selected-version variables, and includes no template or section content.
4. Enter string, number, boolean, and JSON values. Confirm type errors and missing required values display inline.
5. Refresh the page and confirm entered values are not restored or saved.
6. Repeat with a published version, then a version without variables; confirm schema access and an explicit empty state.
7. As unauthenticated and non-staff users, attempt both routes and confirm no schema is disclosed.

## Scope guard

The screen must not offer compile, preview, submit, save, or LLM invocation controls.
