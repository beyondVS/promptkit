# Quickstart Validation: Prompt Management Dashboard

## Prerequisites

- Configure the Django environment and database.
- Run `uv sync`.
- Supply the required SDK API key through the project environment configuration.
- Create a staff user for dashboard validation.

## Run the validation harness

From the repository root:

```powershell
uv run ruff check
uv run ruff format --check
uv run mypy .
uv run pytest
```

## End-to-end acceptance flow

1. Sign in to the dashboard as a staff user; verify an unauthenticated visitor is redirected to login.
2. Create or select a category, then create a prompt. Confirm it has an empty first draft and that duplicate names are rejected only inside the same category.
3. Add `system`, `user`, and `assistant` sections, declare variables, and use `{{ variable_name }}` references. Verify unsupported roles, missing references, invalid defaults, and referenced-variable deletion are rejected.
4. Rename a variable and verify every matching reference in the same draft changes atomically.
5. Publish the draft. Verify contents and lifecycle state cannot be edited or reverted, `latest` targets that published version, and custom labels can target it.
6. Clone both a published version and a draft. Verify each resulting version is a separate draft with independent sections and variables.
7. Set one published version on-live, fetch it through `GET /api/v1/prompts/<slug>/` without a label, then switch and clear on-live. Verify only the selected published version is returned and clearing returns the documented no-deployable-version result.
8. Fetch an explicitly labeled published version. Verify `production`, unknown labels, and any attempt to reach drafts do not return prompt content.
9. Attempt concurrent updates with a stale revision. Verify the second write is rejected without overwriting the newer data.
10. Verify a prompt cannot be deleted while on-live, then clear on-live and confirm prompt deletion removes its related lifecycle records. Verify a category containing prompts cannot be deleted.

## Documentation verification

Confirm `.specify/memory/constitution.md`, `AGENTS.md`, `docs/prompt-server-requirements.md`, `docs/project-spec.md`, `docs/architecture.md`, `docs/project_plan.md`, and `docs/sdk-read-api-contract.md` all state the same on-live, latest, label, and SDK-read-only policies.
