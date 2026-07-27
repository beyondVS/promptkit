# Implementation Plan: DB Modeling and Migrations

**Branch**: `002-db-models-migration` | **Date**: 2026-07-27 | **Spec**: [spec.md](file:///D:/Projects/Private/promptkit/specs/002-db-models-migration/spec.md)

**Input**: Feature specification from `specs/002-db-models-migration/spec.md`

## Summary

Design and implement Django ORM models (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section`) within `apps/server`, establishing 1:N relational links, cascade behaviors, uniqueness constraints, and initial migration scripts.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework, PostgreSQL driver (`psycopg`)

**Storage**: PostgreSQL (with SQLite support for local dev/testing)

**Testing**: pytest (`pytest-django`)

**Target Platform**: Linux server / Self-hosted Python 3.13 runtime

**Project Type**: Web service (`apps/server`)

**Performance Goals**: Sub-10ms DB query resolution for prompt versions and label lookups

**Constraints**: Foreign key constraints for 1:N relations, unique constraints for labels per prompt and variables/sections per version

**Scale/Scope**: Thousands of prompt templates, dozens of versions per prompt

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I: Prompt Registry Focus**: PASS. DB models strictly store, version, and organize prompts without LLM gateway logic.
- **Principle II: SDK-First & Framework Agnostic SDK Core**: PASS. Models are isolated within `apps/server/prompts` (Django app).
- **Principle III: Prompt Compilation & Adapters**: PASS. Models store raw templates and variable specifications; rendering/compilation logic stays out of models.
- **Principle IV: Label-Driven Resolution**: PASS. `Label` entity maps environment tags (defaulting to `production`) to versions with per-prompt uniqueness constraints.
- **Principle V: Lightweight & Self-Hosted First**: PASS. Out-of-scope features (tracing, cost metrics) are excluded from the database schema.
- **Output Integrity**: PASS. Surgical updates and zero-tolerance for code summaries.
- **No Hardcoding**: PASS. Database credentials configured via environment variables.

## Project Structure

### Documentation (this feature)

```text
specs/002-db-models-migration/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── orm-schema.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code Layout

```text
apps/server/
├── config/
│   ├── settings.py
│   └── urls.py
└── prompts/             # New Django App for Prompt Registry
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── migrations/
    │   └── __init__.py
    ├── models.py        # Prompt, Version, Label, VariableDefinition, Section
    └── tests/
        └── test_models.py
```

**Structure Decision**: Selected Django App structure within `apps/server/prompts/` to encapsulate Prompt Registry ORM models, migrations, and model tests cleanly in accordance with Django best practices.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
