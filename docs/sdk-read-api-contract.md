# PromptKit SDK Read API Contract

## Scope
SDK endpoint is API-key-authenticated and read-only; dashboard CUD is session-authenticated and CSRF-protected.

## Endpoint

`	ext
GET /api/v1/prompts/<slug>/
GET /api/v1/prompts/<slug>/?label=<published-label>
X-PromptKit-Api-Key: <api-key>
` 

## Resolution rules
- Omitted labels return only the on-live published version.
- Explicit latest or custom labels return published targets only.
- latest targets the last published version; production is rejected.
- Missing on-live never falls back to latest, custom labels, drafts, or local templates.

## Errors
| Condition | Result |
|---|---|
| Invalid API key | Authentication error; no prompt data |
| No on-live for omitted label | No-deployable-version; no fallback |
| Unknown, draft-targeting, or production label | Not-found or validation error |
| Non-GET | Method-not-allowed |
