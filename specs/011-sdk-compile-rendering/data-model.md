# Data Model: SDK Local Prompt Compilation

## Existing Input: Retrieved Prompt

The existing `RetrievedPrompt` supplies immutable source information and three compilation inputs: aggregate template text, ordered role sections, and variable declarations. Compilation adds no persistence or lifecycle.

## Variable Declaration

| Field | Rules during compilation |
|---|---|
| `name` | Unique identifier; must match the supported placeholder grammar when referenced. |
| `var_type` | Exactly `string`, `number`, `boolean`, or `json`. |
| `required` | A referenced required value must be supplied or have a valid default. An unreferenced required declaration is invalid. |
| `default_value` | Optional registry value. It is normalized and validated by declared type before use. |

`string` accepts text; `number` accepts a non-boolean integer or float; `boolean` accepts a boolean; `json` accepts an object or array. Caller input uses strict types. Stored defaults are parsed to those types before validation.

## Compilation Input

| Field | Rules |
|---|---|
| `params` | Optional mapping of caller-supplied values. Every key must be declared. |

Caller values override valid defaults. A missing required value without a valid default fails. Optional absent values are permitted only when unreferenced; a referenced optional variable must have a supplied or default value to render.

## Compiled Prompt

| Field | Source / rule |
|---|---|
| `slug` | Copied from the retrieved prompt. |
| `version` | Copied from the retrieved prompt. |
| `label` | Copied from the retrieved prompt; may be null. |
| `content` | Fully rendered aggregate template text. |
| `sections` | Ordered sections with role/order retained and content fully rendered. |

No result is created on validation or template failure.

## Failure Categories

| Category | Trigger |
|---|---|
| Missing variable | A required or referenced value has no caller value or valid default. |
| Invalid variable type | Caller input or normalized default does not satisfy the declared type. |
| Unexpected variable | Caller supplies an undeclared name. |
| Invalid template | Delimiters are malformed, placeholder syntax is unsupported, a placeholder is undeclared, or a required declaration is not referenced. |
