# Phase 0 Research: DB Modeling and Migrations

## Overview

This research document analyzes and resolves key implementation decisions for designing Django ORM models (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section`) and their 1:N relational architecture in `apps/server`.

---

## 1. Entity Cascade & Foreign Key Rules

### Decision
- `Prompt` -> `Version`: `models.CASCADE`. Deleting a prompt removes all associated historical versions.
- `Version` -> `Label`: `models.CASCADE` on `Version` and `models.CASCADE` on `Prompt`. If a prompt or specific version is deleted, associated label references are cleaned up.
- `Version` -> `VariableDefinition`: `models.CASCADE`. Deleting a version removes its variable specifications.
- `Version` -> `Section`: `models.CASCADE`. Deleting a version removes its section definitions.

### Rationale
In PromptKit's registry domain, `Version`, `VariableDefinition`, and `Section` entities are strictly owned children of their parent `Prompt`/`Version`. They have no independent lifecycle outside their parent container. Using `models.CASCADE` ensures relational integrity and prevents orphan records without complex soft-delete triggers.

### Alternatives Considered
- `models.PROTECT`: Rejected for version-child entities because versions are immutable child objects; protecting parents from deletion complicates clean administrative purges when explicitly requested.

---

## 2. Label Uniqueness & Resolution Strategy

### Decision
Use Django's `UniqueConstraint(fields=['prompt', 'name'], name='unique_label_per_prompt')`.

### Rationale
According to PromptKit Constitution Principle IV (Label-Driven Resolution), a prompt query without a version defaults to the `production` label. A label such as `production` or `draft` must point to at most one `Version` per `Prompt`. Placing a composite unique constraint on `[prompt, name]` enforces at the database level that no prompt can have two `production` labels simultaneously.

### Alternatives Considered
- Global label uniqueness (`name` unique across all prompts): Rejected, because multiple different prompts can each have their own `production` label.

---

## 3. Variable Definition Schema & Type Choices

### Decision
Define standard parameter type choices for `VariableDefinition.var_type`:
- `string`: Standard text replacement
- `integer`: Numeric integer parameter
- `float`: Floating point parameter
- `boolean`: True/False flag
- `json`: Structured JSON payload / object

Include fields:
- `name` (CharField, max_length=100)
- `var_type` (CharField with Choices, max_length=20, default='string')
- `required` (BooleanField, default=True)
- `default_value` (TextField, blank=True, null=True)
- `description` (TextField, blank=True)

Constraint: `UniqueConstraint(fields=['version', 'name'], name='unique_variable_per_version')`.

---

## 4. Section Role Choices & Ordering Index

### Decision
Define `Section` attributes:
- `role` (CharField choices: `system`, `user`, `assistant`, `tool`, default=`user`)
- `order` (PositiveIntegerField, default=0)
- `content` (TextField)

Constraint: `UniqueConstraint(fields=['version', 'order'], name='unique_section_order_per_version')`.

### Rationale
Multi-turn or modular prompts require deterministic ordering when compiled by the SDK. Enforcing an explicit integer order index with a unique constraint per version guarantees stable sequence rendering.
