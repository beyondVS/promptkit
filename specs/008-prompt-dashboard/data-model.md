# Data Model: Prompt Management Dashboard

## PromptCategory

- **Fields**: name, slug, description, active flag, timestamps.
- **Identity**: name and slug are globally unique.
- **Relationship**: has many Prompts; deletion is restricted while any Prompt is attached.

## Prompt

- **Fields**: global stable SDK slug, name, description, category, timestamps.
- **Identity**: slug is globally unique; `(category, name)` is unique.
- **Relationship**: has many Versions and Labels.
- **Lifecycle**: can be deleted only with no on-live Version; deletion cascades to associated versions, sections, variables, and labels.

## Version

- **Fields**: prompt, monotonically increasing version number, status (`draft` or `published`), template content, changelog, revision/timestamp for stale-write detection, timestamps.
- **Identity**: `(prompt, version_number)` is unique.
- **Lifecycle**: initial version is an empty draft; a draft can be edited, cloned, published, or deleted; publication is irreversible; both draft and published versions can be clone sources; clones are always drafts.
- **On-live invariant**: only a published version can be on-live; each Prompt has at most one on-live Version; staff can explicitly clear it.

## Section

- **Fields**: version, role, order, content, timestamps.
- **Role values**: `system`, `user`, `assistant`.
- **Identity**: `(version, order)` is unique.
- **Lifecycle**: draft-only CUD; content may reference declared variables only with `{{ variable_name }}` syntax.

## VariableDefinition

- **Fields**: version, name, type, required flag, type-compatible default value, description.
- **Type values**: `string`, `number`, `boolean`, `json`.
- **Identity**: `(version, name)` is unique.
- **Lifecycle**: draft-only CUD. Renaming updates matching references in the same draft atomically. A referenced variable cannot be deleted until all references are removed or changed.

## Label

- **Fields**: prompt, published version, name, timestamps.
- **Identity**: `(prompt, name)` is unique.
- **System rule**: `latest` is the only system label and points to the last published version. It is assigned on publish and removed from the prior published version. `production` is not a valid system or custom label.
- **Custom rule**: custom labels use English letters, digits, and hyphens; they may target published versions only; duplicate creation errors; target moves are explicit actions.

## Validation and concurrency

- Every mutable dashboard request carries the version revision/timestamp expected by the editor.
- A mismatch produces a conflict response and leaves stored content, labels, and lifecycle state unchanged.
- Publish, on-live reassignment/clear, label moves, clone, and delete operations run in transactions.
