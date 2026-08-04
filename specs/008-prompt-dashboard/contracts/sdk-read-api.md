# SDK Read API Contract

## Scope

This contract covers the API-key-authenticated read-only SDK endpoint. Dashboard CUD is session-authenticated and is intentionally excluded.

## Endpoint

`GET /api/v1/prompts/<slug>/`

### Authentication

Send `X-PromptKit-Api-Key`. Mutating methods are not supported by this endpoint.

### Query parameter

`label` is optional.

- Omitted: return the prompt's on-live published Version.
- Explicit custom label or `latest`: return the published Version that label targets.
- `production`: reject because it is not a defined label.

### Successful response

Return JSON containing the stable prompt slug, prompt display metadata, selected version number, selected label when explicitly requested, template content, variable definitions, sections, and creation metadata. Do not render or execute the prompt.

### Failure responses

| Condition | Result |
|---|---|
| Missing or invalid API key | Authentication error; no prompt data. |
| Unknown prompt slug | Not-found error. |
| Omitted label with no on-live version | No-deployable-version error; do not fall back. |
| Explicit unknown, draft-targeting, or `production` label | Not-found/validation error; no draft fallback. |
| Non-GET method | Method-not-allowed error. |

## Dashboard boundary

All creation, editing, publish, clone, delete, on-live, category, section, variable, and label actions are staff-session dashboard operations protected by CSRF. They are not exposed through this SDK contract.
