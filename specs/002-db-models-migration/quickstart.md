# Quickstart Validation Guide: DB Models & Migrations

## Overview

This guide provides runnable instructions to validate the database models (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section`) and migration execution for `apps/server`.

---

## Prerequisites

- Python 3.13 installed
- `uv` package manager installed
- Virtual environment synchronized (`uv sync`)

---

## 1. Migration Generation & Application

Run the following commands from the repository root:

```bash
# 1. Generate Django migration files for the prompts app
uv run python apps/server/manage.py makemigrations prompts

# 2. Apply migrations to local database (SQLite fallback or PostgreSQL)
uv run python apps/server/manage.py migrate
```

---

## 2. Automated Test Execution

Run the hybrid test suite via `pytest`:

```bash
# Run unit & ORM model tests for prompts app
uv run pytest tests/server/test_models.py
```

---

## 3. Manual Interactive Verification (Django Shell)

To quickly verify model relationships in interactive mode:

```bash
uv run python apps/server/manage.py shell
```

```python
from apps.server.prompts.models import (
    Label,
    Prompt,
    Section,
    VariableDefinition,
    Version,
)

# Create Prompt
prompt = Prompt.objects.create(slug="welcome-email", name="Welcome Email")

# Create Version
version = Version.objects.create(
    prompt=prompt, version_number=1, template_text="Hello {{ user_name }}"
)

# Assign Label
label = Label.objects.create(prompt=prompt, version=version, name="production")

# Add Variable Definition
var_def = VariableDefinition.objects.create(
    version=version, name="user_name", var_type="string", required=True
)

# Add Section
section = Section.objects.create(
    version=version, role="system", order=0, content="System context"
)

# Assert Relationships
assert prompt.versions.count() == 1
assert prompt.labels.get(name="production").version == version
assert version.variables.count() == 1
assert version.sections.count() == 1
print("Validation Passed!")
```
