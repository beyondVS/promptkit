# Data Model: Playground Compilation and Gemini E2E Example

This feature adds no persistent database model or migration. The entities below are request-local or process-local contracts assembled from existing prompt registry records.

## Playground compile form

| Field | Source | Parsed value | Validation |
|-------|--------|--------------|------------|
| `variable__<name>` | One selected version variable | `str`, `int`/finite `float`, `bool`, `dict`, or `list` | Generated only from declared variables; required blanks fail; optional blanks are omitted; JSON must be object/array |
| CSRF token | Django form middleware | framework token | Required for POST; never passed to the compiler |

Generated controls preserve the existing variable order by name and redisplay safe submitted values after validation failure. Field names are prefixed so request metadata cannot collide with prompt variables.

## Playground compilation request

| Field | Type | Relationship / rule |
|-------|------|---------------------|
| `version` | existing `Version` snapshot | Selected exclusively by the URL identifier and reloaded with prompt/category, variables, and sections |
| `params` | mapping of variable name to parsed value | Contains declared non-blank inputs only; never persisted |

Lifecycle: `GET display` → `POST bind` → `form invalid` or `SDK compile` → `preview/error render` → discarded at response completion.

## SDK source representation

The dashboard service maps the existing ORM snapshot into public `RetrievedPrompt` fields:

| SDK field | ORM source / rule |
|-----------|-------------------|
| `slug`, `name`, `description` | selected version's prompt |
| `category` | prompt category name and slug |
| `version`, `version_status`, `is_on_live` | selected version number, status, and deployment flag |
| `label` | `None`; Playground selects a version directly |
| `template_text`, `created_at` | selected version snapshot |
| `variables` | all selected-version declarations ordered by name |
| `sections` | all selected-version sections ordered by `order` |

The mapped model is transient. It is not fetched through the read-only API and does not change draft/published lifecycle state.

## Compiled preview

| Field | Type | Validation / display rule |
|-------|------|---------------------------|
| `slug` | non-empty string | Safe source identifier |
| `version` | positive integer | Exact selected version |
| `label` | null | Direct-version Playground source |
| `content` | string | Aggregate template output; whitespace and Unicode preserved and HTML-escaped |
| `sections` | ordered immutable collection | Role, non-negative order, and rendered content preserved and HTML-escaped |

A preview exists only after full compiler success. Expected failures produce no partial `CompiledPrompt`.

## E2E example configuration

| Input | Required | Secret | Rule |
|-------|----------|--------|------|
| `PROMPTKIT_BASE_URL` | Yes | No | HTTPS or loopback HTTP, per SDK validation |
| `PROMPTKIT_API_KEY` | Yes | Yes | Non-blank; never printed or interpolated into errors |
| `PROMPTKIT_PROMPT_SLUG` | Yes | No | Fetches omitted-label on-live version only |
| `PROMPTKIT_PROMPT_PARAMS` | No | Potentially | JSON object; values pass to strict local compilation; never logged as a whole |
| `GEMINI_API_KEY` | Live only | Yes | Required only after `--live` consent |
| `GEMINI_MODEL` | Live only | No | Non-blank model identifier supplied by the operator |
| `--live` | No | No | Sole authorization for one provider request |

## E2E execution state

```text
configuration validated
        ↓
registry prompt fetched
        ↓
prompt compiled locally
        ↓
Gemini arguments converted
        ↓
no --live: stop with 0 provider calls
        └── --live: create client → exactly 1 request → validate text response → close client
```

Failures are terminal at their stage. No failure transitions to a later network stage, and no retry transition exists.
