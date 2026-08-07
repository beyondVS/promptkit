# SDK Public Contract: `promptkit`

## Public surface

```python
from promptkit import PromptKitClient

client = PromptKitClient(base_url, api_key, timeout=10.0)
prompt = client.fetch(slug, label=None)
```

`PromptKitClient` is synchronous. It exposes read-only retrieval only. `fetch()` returns a typed `RetrievedPrompt` or raises a typed `PromptKitError` subclass. It does not call an LLM, compile variables, cache responses, retry, or follow redirects.

## Request contract

| Item | Value |
|---|---|
| Method | `GET` |
| Path | `/api/v1/prompts/{slug}/` |
| Optional query | `label={label}` only when a label is supplied |
| Required header | `X-PromptKit-Api-Key: <caller-supplied key>` |
| Default timeout | 10 seconds, caller-overridable |
| Redirect policy | Disabled; any 3xx is a `RedirectError` |
| URL policy | HTTPS, plus HTTP only for loopback addresses |

## Success response contract

The SDK accepts the active server serializer fields below and ignores additional fields:

```json
{
  "slug": "greeting-prompt",
  "name": "Greeting Prompt",
  "description": "",
  "category": {"name": "General", "slug": "general"},
  "version": 1,
  "version_status": "published",
  "is_on_live": true,
  "label": null,
  "template_text": "Hello {{ user_name }}!",
  "variables": [{"name": "user_name", "var_type": "string", "required": true, "default_value": null, "description": ""}],
  "sections": [{"role": "user", "order": 0, "content": "Hello {{ user_name }}!"}],
  "created_at": "2026-08-07T00:00:00Z"
}
```

## Error mapping contract

| Condition | Public outcome |
|---|---|
| Empty/malformed input, forbidden `production`, unsafe registry URL | Local typed validation error; no request is sent. |
| 401 | `AuthenticationError` |
| 404 with `error: no_deployable_version` | `NoDeployableVersionError` |
| 404 with `error: label_not_found` | `LabelNotFoundError` |
| 404 without that named error (unknown slug from active server) | `PromptNotFoundError` |
| 400 with `error: invalid_label` | `InvalidLabelError` |
| 429 | `RateLimitError` |
| 3xx | `RedirectError` |
| Timeout/connection/TLS failure | `CommunicationError` |
| Malformed 200 body or unsupported response | `InvalidResponseError` |

No error path returns another label, draft, latest value, cached content, or a locally supplied fallback prompt.
