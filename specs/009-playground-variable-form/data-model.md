# Data Model: Playground Variable Form

## Persisted entities reused unchanged

### Prompt

Identifies the displayed prompt (`id`, `slug`, `name`) and has many versions.

### Version

Identifies the Playground target (`id`, `version_number`, `status`). Both `draft` and `published` versions are readable by an authorized staff user and have many variable definitions.

### VariableDefinition

- Schema fields: `name`, `var_type`, `required`, `default_value`, `description`.
- Types: `string`, `number`, `boolean`, `json`.
- A name is unique within its version.
- A nullable `default_value` distinguishes no default from an empty-string default.

## Transient client-side state

**Playground Input State** is keyed by version and variable name; it holds a browser-entered value and validation state. It is never posted, stored, or restored after refresh or navigation.

```text
Prompt 1 ── * Version 1 ── * VariableDefinition
                         └── * transient Playground Input State
```

The schema endpoint returns one Version and only its variables. Required blanks, invalid numbers, invalid JSON, and unselected booleans are marked in the browser. No model lifecycle or database migration is introduced.
