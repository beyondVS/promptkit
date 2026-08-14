# Public Python Contract: `promptkit-django`

## Installation and application registration

The distribution name is `promptkit-django`; its import package is
`promptkit_django`. A consuming Django project adds `"promptkit_django"` to
`INSTALLED_APPS` and declares a `PROMPTKIT` mapping in its active settings.

Initialization is eager: application startup validates the mapping and registers the
client. Importing `promptkit_django` alone does not create a client or mutate global
state.

## Settings contract

| Key | Required | Default | Meaning |
|---|---|---|---|
| `BASE_URL` | Yes | None | Prompt Registry base URL passed to the core client. |
| `API_KEY` | Yes | None | Read-only Prompt Registry credential passed to the core client. |
| `TIMEOUT` | No | `10.0` | Positive request timeout passed to the core client. |

`PROMPTKIT` must be a mapping containing only these uppercase keys. Missing, blank,
wrongly typed, unsafe, or unknown values cause application startup to raise the
package's public configuration exception. Error messages identify key names but never
include an API-key value.

## Public symbols

| Symbol | Contract |
|---|---|
| `PromptKitDjangoConfig` | Django application configuration whose startup hook performs eager validation and registration. |
| `get_client()` | Returns the `PromptKitClient` registered by the active `PromptKitDjangoConfig`. It raises the public uninitialized exception if the integration is absent or startup has not completed; it never creates a client. |
| `PromptKitDjangoConfigurationError` | Raised for invalid `PROMPTKIT` configuration during startup. |
| `PromptKitDjangoNotInitializedError` | Raised when `get_client()` cannot resolve a completed integration registration. |

The accessor returns the same `PromptKitClient` object for repeated calls within one
Django Apps registry. The integration exposes no prompt mutation, LLM invocation,
cache, retry, provider, or named-client API.
