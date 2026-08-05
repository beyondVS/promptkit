# Prompt Server (Django)

Django REST Framework Prompt Registry Server with Staff Dashboard and Read-Only SDK Fetch API.

## Features & Policy

- **Read-Only SDK API**:
  - `GET /api/v1/prompts/<slug>/` authenticated via `X-PromptKit-Api-Key` header.
  - **Omitted label**: Resolves the on-live published version. Returns `404 no_deployable_version` if no version is on-live.
  - **Explicit label** (`?label=latest` or custom label): Resolves the published version targeted by that label.
  - **`production` label**: Prohibited and rejected with `400 invalid_label`.
- **Staff Session Dashboard**:
  - `/dashboard/`: Staff session-authenticated dashboard protected by CSRF.
  - Full CUD for Categories, Prompts, Draft Version Sections, and Draft Version Variables.
  - Atomic transactions for Publish, Clone to Draft, On-Live Target selection, and Custom Labels.

## Quickstart

```bash
# Sync environment & run migrations
uv sync
uv run python manage.py migrate

# Create superuser for dashboard access
uv run python manage.py createsuperuser

# Run server
uv run python manage.py runserver
```
