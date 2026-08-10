# SDK Public Contract: Local Prompt Compilation

## Public surface

```python
from typing import Mapping

from promptkit import CompiledPrompt, RetrievedPrompt

compiled: CompiledPrompt = prompt.compile(params={"customer_name": "Ada"})
```

`compile()` performs no network request, persistence, provider formatting, or LLM call. It returns one immutable completed prompt or raises a typed `PromptKitError` subclass.

## Placeholder contract

Only `{{ variable_name }}` placeholders are supported. Whitespace around the name is allowed. Names use the identifier grammar `[A-Za-z_][A-Za-z0-9_]*`. Expressions, filters, attributes, control structures, unclosed delimiters, and orphaned closing delimiters are invalid templates.

All template text and every section are validated before any result is returned. Each declared placeholder receives the single validated value for its name, including repeated occurrences. Rendered values are never parsed again.

## Input validation contract

| Declared type | Accepted caller value |
|---|---|
| `string` | string |
| `number` | integer or float, excluding boolean |
| `boolean` | boolean |
| `json` | object or array |

Every input key must be declared. A caller value overrides a declaration default. Defaults are parsed from the registry representation and validated before injection. Invalid defaults fail compilation rather than being rendered.

## Result contract

| Field | Meaning |
|---|---|
| `slug` | Source prompt identifier |
| `version` | Source version number |
| `label` | Source resolution label, if any |
| `content` | Fully rendered aggregate template |
| `sections` | Fully rendered ordered role sections |

## Error contract

| Condition | Public outcome |
|---|---|
| Missing required/referenced value | `MissingVariableError` |
| Invalid caller value or default | `InvalidVariableTypeError` |
| Undeclared input key | `UnexpectedVariableError` |
| Malformed or declaration-inconsistent template | `TemplateValidationError` |

Errors identify the affected name or template condition but do not include supplied values. No error outcome returns a partial `CompiledPrompt`.
