# Implementation Plan: Playground Variable Form

**Branch**: `009-playground-variable-form` | **Date**: 2026-08-06 | **Spec**: [spec.md](spec.md)

## Summary

Add a staff-only Playground screen for the version selected in the prompt detail dashboard. It retrieves the version's dynamic-variable schema through a dashboard-scoped read-only JSON endpoint, renders type-specific transient inputs, and validates values in the browser. It does not persist values, compile prompts, preview output, or call an LLM.

## Technical Context

**Language/Version**: Python 3.13+, HTML, CSS, browser JavaScript  
**Primary Dependencies**: Django 5.x, Django REST Framework 3.15+, PostgreSQL, Django session authentication  
**Storage**: Existing `VariableDefinition` records only; input values have no server-side storage  
**Testing**: pytest with `django.test.TestCase`; Ruff and MyPy  
**Target Platform**: Self-hosted Django web server and modern desktop browsers  
**Project Type**: Server-rendered Django web application with a dashboard-scoped JSON interface  
**Performance Goals**: A staff user can open the selected version's Playground and identify every variable within 1 minute  
**Constraints**: Reuse session/staff authorization; do not extend the API-key SDK endpoint; no migration, POST endpoint, persistence, compilation, preview, or LLM invocation  
**Scale/Scope**: One screen, one read-only schema endpoint, and four input types (`string`, `number`, `boolean`, `json`)

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design: passed.*

- **Prompt Registry Focus**: Reads prompt metadata only; no LLM proxy or execution.
- **SDK-First & Framework Agnostic Core**: Changes are confined to the Django dashboard, with no SDK capability added.
- **Prompt Compilation & Adapters**: No compilation, rendered preview, or adapter behavior is added.
- **Label-Driven Resolution**: Administrator-selected version access does not change SDK on-live or label resolution.
- **Lightweight & Self-Hosted First**: No external service, workflow, tracing product, or persistence layer is introduced.
- **Security and quality controls**: Existing session/staff authorization protects both routes; tests use `django.test.TestCase`; no credentials are introduced.

## Project Structure

### Documentation (this feature)

```text
specs/009-playground-variable-form/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── dashboard-variable-schema.md
```

### Source Code (repository root)

```text
apps/server/
└── prompts/
    ├── urls.py
    ├── views/dashboard.py
    ├── templates/prompts/
    │   ├── prompt_detail.html
    │   └── playground.html
    └── tests/
        └── test_dashboard_playground.py
```

**Structure Decision**: Extend the existing server-rendered dashboard. Add a protected page and JSON GET route alongside current dashboard routes, reuse `VariableDefinition` unchanged, and add focused tests in the existing app test package.
