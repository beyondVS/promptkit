# Data Model: SDK Remote Prompt Retrieval

## Client Configuration

Represents configuration fixed when creating a `PromptKitClient`.

| Field | Required | Rules |
|---|---:|---|
| `base_url` | Yes | HTTPS URL, or HTTP only when the hostname is loopback; normalized before request construction. |
| `api_key` | Yes | Non-empty caller-supplied secret; sent only as `X-PromptKit-Api-Key`; never included in model representation or error text. |
| `timeout` | No | Positive duration; defaults to 10 seconds; caller may override. |

## Prompt Retrieval Request

Represents one read-only lookup.

| Field | Required | Rules |
|---|---:|---|
| `slug` | Yes | Non-empty prompt identifier; encoded as one path segment. |
| `label` | No | Omitted to resolve on-live. `production` is rejected locally; other labels are sent to the registry unchanged. |

## Retrieved Prompt

Represents a valid 200 registry response.

| Field | Source field | Validation |
|---|---|---|
| `slug` | `slug` | Required non-empty string. |
| `name` | `name` | Required string. |
| `description` | `description` | Required string. |
| `category` | `category` | Required category name and slug. |
| `version` | `version` | Required positive integer. |
| `version_status` | `version_status` | Required string; expected published for this endpoint. |
| `is_on_live` | `is_on_live` | Required boolean. |
| `label` | `label` | Nullable selected label. |
| `template_text` | `template_text` | Required string. |
| `variables` | `variables` | Required ordered collection of variable definitions. |
| `sections` | `sections` | Required ordered collection of prompt sections. |
| `created_at` | `created_at` | Required timestamp. |

Unknown fields are ignored. Missing or structurally invalid required fields make the full response invalid and raise an invalid-response error.

## Nested Models

### Category

| Field | Rules |
|---|---|
| `name` | Required string. |
| `slug` | Required string. |

### Variable Definition

| Field | Rules |
|---|---|
| `name` | Required variable identifier. |
| `var_type` | Required declared type name. |
| `required` | Required boolean. |
| `default_value` | Nullable default value supplied by the registry. |
| `description` | Required string. |

### Prompt Section

| Field | Rules |
|---|---|
| `role` | Required message role. |
| `order` | Required non-negative ordering value. |
| `content` | Required template text. |

## Retrieval Outcome and Error States

| Outcome | Trigger |
|---|---|
| `AuthenticationError` | HTTP 401. |
| `PromptNotFoundError` | HTTP 404 for an unknown slug (the active server response has no named error code). |
| `NoDeployableVersionError` | HTTP 404 with `error: no_deployable_version`. |
| `LabelNotFoundError` | HTTP 404 with `error: label_not_found`. |
| `InvalidLabelError` | Local `production` preflight rejection or HTTP 400 `invalid_label`. |
| `RateLimitError` | HTTP 429. |
| `RedirectError` | Any 3xx response; no redirect is followed. |
| `CommunicationError` | Timeout, connection, or TLS transport failure; no automatic retry. |
| `InvalidResponseError` | Unexpected success status/body or Pydantic validation failure. |
