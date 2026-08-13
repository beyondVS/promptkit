# Data Model: LiteLLM Adapter and SDK Harness

## Existing input entities

### CompiledPrompt

Immutable local render result consumed by every adapter.

| Field | Rules used by this feature |
|---|---|
| `slug` | Non-empty source identifier; may appear in the safe system-only warning. |
| `version` | Positive source version; may appear in the safe system-only warning. |
| `label` | Optional source label; may appear in the safe system-only warning. |
| `content` | Aggregate rendered text used as a single user message only when `sections` is empty. |
| `sections` | Immutable tuple of `CompiledPromptSection` values. |

### CompiledPromptSection

Immutable rendered section.

| Field | Validation and conversion rules |
|---|---|
| `role` | Must be exactly `system`, `user`, or `assistant` for conversion. Any other value raises `AdapterConversionError`. |
| `order` | Non-negative and unique within one conversion. Adapters sort ascending; duplicates raise `AdapterConversionError`. |
| `content` | String passed through exactly, including empty, whitespace, Unicode, and placeholder-shaped text. |

## New public argument contracts

### LiteLLMChatMessage

Plain typed dictionary representing one message supplied to LiteLLM completion.

| Field | Rule |
|---|---|
| `role` | Exact source role: `system`, `user`, or `assistant`. |
| `content` | Exact compiled section content. |

### LiteLLMCompletionArgs

Plain typed dictionary returned by the LiteLLM adapter.

| Field | Rule |
|---|---|
| `messages` | One `LiteLLMChatMessage` per resolved section, or one user message built from aggregate content when no sections exist. |

No persistent entities, database schema changes, lifecycle transitions, or migrations are part of this feature.

## Test-only entities

### Public API inventory

The exact `promptkit.__all__` set. It is compared with the coverage-map keys for equality. Every inventory item must have an import or behavior assertion through the package root.

### Public API coverage map

Test-local mapping keyed by public export name and valued with the named assertion(s) that prove the contract. It must contain no missing or stale keys. It is not a runtime SDK data structure.
