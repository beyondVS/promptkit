# Research: Playground Variable Form

## Dashboard-only schema interface

- **Decision**: Add session- and staff-authenticated `GET /dashboard/api/versions/{version_id}/variables/`.
- **Rationale**: Staff may inspect draft and published versions. The SDK endpoint is API-key protected and intentionally exposes only published on-live or labeled versions.
- **Alternatives considered**: Extending `/api/v1/prompts/{slug}/` was rejected because it would violate the SDK boundary; rendering schema without an endpoint was rejected because the feature requires schema retrieval.

## Selected-version navigation

- **Decision**: Add `GET /dashboard/versions/{version_id}/playground/`, linked from the selected version toolbar.
- **Rationale**: A version primary key identifies one target and satisfies the clarified no-picker flow.
- **Alternatives considered**: A standalone selector was rejected as out of scope; a query-string-only selector duplicates the current flow.

## No new persisted data

- **Decision**: Reuse `VariableDefinition(name, var_type, required, default_value, description)` ordered by name.
- **Rationale**: It already defines all fields and uniqueness needed for the form. Input state is browser-only.
- **Alternatives considered**: Persisting values or copying schema into another model was rejected as unnecessary and out of scope.

## Local input validation

- **Decision**: Use text, number, boolean, and JSON controls; validate locally and never submit.
- **Rationale**: Day 09 is input preparation only; compilation is explicitly deferred.
- **Alternatives considered**: A server validation endpoint, compile action, preview, or LLM call were rejected as scope expansion.

## Authorization and failures

- **Decision**: Apply `LoginRequiredMixin` and `DashboardStaffRequiredMixin` to both routes; unknown versions are not found, and non-GET requests are rejected.
- **Rationale**: This matches existing dashboard access controls and prevents schema disclosure through the SDK boundary.
