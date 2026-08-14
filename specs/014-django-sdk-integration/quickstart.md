# Quickstart: Validate Django SDK Integration

## Prerequisites

- Python 3.13+ and `uv`.
- A checked-out repository on branch `014-django-sdk-integration`.
- No live Prompt Registry or production credential is required.

## Workspace validation

From the repository root, synchronize declared workspace dependencies and run the
focused Django-integration tests, then the project quality gates:

```powershell
uv sync
uv run pytest tests/promptkit_django
uv run ruff check
uv run ruff format --check
uv run mypy .
```

Expected outcomes:

- Valid `PROMPTKIT` settings create one shared client at application startup.
- Missing, malformed, or unknown settings fail startup while redacting API-key values.
- Access before completed registration raises the documented uninitialized error.

## Independent Git-subdirectory validation

The packaging integration test must perform these steps in temporary directories:

1. Build a wheel for `packages/promptkit` into a temporary wheelhouse with `uv`.
2. Create and commit a temporary Git snapshot containing only
   `packages/promptkit-django`.
3. Create a fresh `uv` virtual environment outside the repository.
4. Install the snapshot using its `#subdirectory=packages/promptkit-django` Git URL
   while supplying the temporary wheelhouse as a package source.
5. Run a subprocess with the fresh environment's Python. It must import only
   installed `promptkit` and `promptkit_django`, configure a minimal Django app,
   call `django.setup()`, and verify repeated `get_client()` identity.

Expected outcomes:

- Dependency resolution chooses the built `promptkit` distribution, not a repository
  path or editable workspace package.
- The Django integration imports and initializes without Prompt Server sources or a
  registry request.
- The subprocess confirms installed distribution locations are inside the temporary
  environment.

## Contract reference

Use [python-public-api.md](contracts/python-public-api.md) for settings and public
symbol expectations, and [data-model.md](data-model.md) for lifecycle and validation
state.
