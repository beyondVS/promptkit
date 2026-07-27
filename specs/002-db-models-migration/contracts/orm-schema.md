# Contract: Django ORM Schema and Relational Integrity Constraints

## Overview
This document specifies the ORM schema contracts and relational integrity rules exposed by the `prompts` app models in `apps/server`.

---

## 1. ORM Model Contracts

### Application Name
- Django App Name: `apps.server.prompts` (or `prompts` within `apps/server`)
- Module Path: `apps.server.prompts.models`

### Model Import Interface
```python
from apps.server.prompts.models import (
    Label,
    Prompt,
    Section,
    VariableDefinition,
    Version,
)
```

---

## 2. Integrity Contracts & Invariants

1. **Prompt Identity Uniqueness**:
   - `Prompt.slug` must be globally unique across all prompt records.
2. **Version Sequence Consistency**:
   - A `Version` belongs to exactly one `Prompt`.
   - `[prompt_id, version_number]` combination must be unique.
3. **Label Single-Target Constraint**:
   - `Label.name` must be unique for a given `Prompt`.
   - `production` label query on a prompt must return at most one `Version`.
4. **Variable Identity Constraint**:
   - `VariableDefinition.name` must be unique for a given `Version`.
5. **Section Sequence Constraint**:
   - `Section.order` must be unique for a given `Version`.

---

## 3. Cascading Behavior Contracts

- Deleting a `Prompt` cascades and purges:
  - All linked `Version` records.
  - All linked `Label` records.
- Deleting a `Version` cascades and purges:
  - All linked `VariableDefinition` records.
  - All linked `Section` records.
  - All linked `Label` records pointing to that version.
