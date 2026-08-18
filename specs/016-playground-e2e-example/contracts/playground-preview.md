# Contract: Playground Compiled Preview

## Resource

The existing version-scoped Playground resource remains:

```text
/dashboard/versions/{version_id}/playground/
```

No JSON compilation endpoint is added.

## Authorization and request protection

- GET and POST require an authenticated staff or superuser session through the existing mixins.
- POST requires Django's normal CSRF token and middleware validation.
- An unknown version returns 404; an unauthenticated or non-staff request follows the existing dashboard denial behavior.

## GET

GET renders prompt/version identity and one input control for every selected-version variable. Every generated control uses `variable__<variable-name>` as its submitted name and is initialized from the declaration default when present.

No compilation, database write, or provider request occurs.

## POST

POST accepts only generated `variable__<name>` controls plus the CSRF token. The server reloads the version from the URL, builds the form from that version, parses supported types, maps the same snapshot to `RetrievedPrompt`, and invokes `compile()` once after form validity.

| Variable type | Accepted submitted form | Compiler value |
|---------------|-------------------------|----------------|
| `string` | text, with original whitespace retained | `str` |
| `number` | integer or finite decimal/exponent syntax | `int` or `float` |
| `boolean` | explicit `true` or `false` | `bool` |
| `json` | JSON object or array | `dict` or `list` |

Blank optional values are omitted so SDK default/optional semantics apply. Blank required values fail validation.

## Successful response

- Status: `200 OK`
- Template: existing `prompts/playground.html`
- Contains source slug/version, aggregate compiled content, and all compiled sections ordered by `order` with their roles.
- Content uses Django auto-escaping and whitespace-preserving markup; empty output is distinguished from failure.
- Shows that the result is local and no LLM request occurred.
- Performs zero database writes and zero provider calls.

## Validation response

- Status: `200 OK`
- Preserves safe submitted controls and displays field-specific parsing errors.
- SDK missing/unexpected/type/template failures are mapped to actionable field or non-field errors without input values or prompt text.
- Contains no partial compiled preview.
- Performs zero database writes and zero provider calls.

## Error safety

Logs and user-visible generic failures may include safe prompt slug/version and error category. They must not include submitted parameter values, compiled content, API keys, authorization headers, or full provider arguments.
