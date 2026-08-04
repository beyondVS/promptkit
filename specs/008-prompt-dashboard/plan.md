# Implementation Plan: Prompt Management Dashboard

**Branch**: `008-prompt-dashboard` | **Date**: 2026-08-04 | **Spec**: [spec.md](spec.md)

**Input**: Prompt management dashboard specification and branch-scoped documentation updates.

## Summary

Update the project constitution, agent guidance, and product/architecture documentation to make the dashboard policy authoritative: a draft can be edited, cloned, or deleted; publishing is irreversible; on-live is the sole default SDK resolution; `latest` denotes the last published version; and `production` is not a defined label. Then implement the schema, protected dashboard flows, and read-only SDK contract that enforce those rules.

The implementation must preserve completed Day 01–07 entries in `docs/project_plan.md`; only unfinished work from Day 08 onward is revised or expanded.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django 5.x, Django REST Framework, Pydantic v2, python-dotenv

**Storage**: PostgreSQL through Django ORM

**Testing**: pytest, Django `TestCase` for ORM/views, `unittest.TestCase` for isolated utilities; Ruff and MyPy

**Target Platform**: Self-hosted Django web service with server-rendered dashboard and read-only JSON API

**Project Type**: Django web application plus independently installable Python SDK packages

**Performance Goals**: No new numeric SLO is introduced; preserve deterministic single-prompt resolution and avoid server-side prompt compilation.

**Constraints**: Session-authenticated staff dashboard for CUD; API-key-authenticated SDK fetch is read-only; SDK performs compilation; no LLM execution; `production` is neither a system nor custom label.

**Scale/Scope**: One prompt registry service. This feature changes governance/product documents, prompt lifecycle, labels, dashboard CUD, and read-only SDK resolution. It does not add tracing, evaluation, workflows, analytics, cost management, or LLM gateway behavior.

## Constitution Check

### Pre-design gate: conditional pass

| Principle | Result | Required plan action |
|---|---|---|
| Prompt Registry Focus | Pass | Keep SDK API read-only and do not add LLM execution. |
| SDK-First & Framework Agnostic | Pass | Keep server lifecycle management separate from SDK compilation. |
| Prompt Compilation & Adapters | Pass | Validate template syntax on the server; render only in the SDK. |
| Label-Driven Resolution | Requires amendment | Amend the current `production` default rule before implementing on-live default resolution. |
| Lightweight & Self-Hosted First | Pass | Use Django ORM, templates, and existing auth without new platform services. |

### Post-design gate: pass after governance update

Implementation starts by updating `.specify/memory/constitution.md`, `AGENTS.md`, and the related documentation so the governing policy is on-live default lookup, published-only labels, and `latest` as the last published version. No application behavior may be changed ahead of that amendment.

## Project Structure

### Documentation (this feature)

```text
specs/008-prompt-dashboard/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── sdk-read-api.md
└── tasks.md                 # Generated later by /speckit-tasks
```

### Source and documentation impact

```text
.specify/memory/constitution.md       # Governance policy amendment
AGENTS.md                             # Branch/documentation workflow alignment
docs/
├── prompt-server-requirements.md     # PRD-level lifecycle and API boundary
├── project-spec.md                   # Product-level label and SDK policy
├── architecture.md                   # Lifecycle, routing, data, API architecture
├── project_plan.md                   # Day 08+ schedule only
└── sdk-read-api-contract.md          # New durable SDK fetch contract
apps/server/
├── prompts/models.py
├── prompts/serializers.py
├── prompts/views/api.py
├── prompts/views/dashboard.py
├── prompts/urls.py
├── config/urls.py
├── prompts/templates/prompts/
└── prompts/tests/
packages/promptkit/                  # SDK compile/fetch alignment if present
tests/                               # Contract and integration coverage
```

**Structure Decision**: Keep the existing Django server and package boundaries. Add only the durable documentation contract under `docs/`; feature-local contracts remain under `specs/008-prompt-dashboard/contracts/`.

## Implementation Phases

1. **Governance and documentation first**: Amend the constitution and `AGENTS.md`; replace obsolete production/fallback/rollback descriptions in `docs/*.md`; create `docs/sdk-read-api-contract.md`; update only Day 08+ milestones in `docs/project_plan.md`.
2. **Schema and migration safety**: Add version lifecycle, on-live, optimistic concurrency, category-scoped prompt-name uniqueness, published-only labels, and normalized variable/section constraints. Plan migrations so existing labels/data are explicitly transformed or rejected with a documented migration path.
3. **Dashboard lifecycle flows**: Build protected category, prompt, version, section, variable, label, and on-live management flows. Enforce draft-only mutation, clone-to-draft, publish immutability, conflict detection, and cascaded prompt deletion rules.
4. **Read-only SDK resolution and routing**: Normalize the public path to `/api/v1/prompts/<slug>/`; remove duplicated API/dashboard exposure; resolve omitted label by on-live only; allow explicit labels only for published versions; return a documented no-deployable-version response without fallback.
5. **Verification and documentation synchronization**: Add migration, model, dashboard, SDK contract, authorization, CSRF, conflict, and regression tests; run the project harness; cross-check final code against the amended core documents.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Governance amendment before application work | Current constitution mandates a `production` default, which conflicts with the approved feature specification. | Leaving the constitution unchanged would make the implementation non-governed and contradictory. |
