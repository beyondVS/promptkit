# Data Model: Django SDK Integration Setup

This feature persists no database data. Its model is configuration and lifecycle
state held in memory for one Django Apps registry.

## Integration settings

| Field | External key | Type | Required | Rules |
|---|---|---|---|---|
| Registry base URL | `BASE_URL` | string | Yes | Non-blank; the core SDK accepts HTTPS or loopback HTTP only and rejects credentials, query, and fragment. |
| Registry API key | `API_KEY` | secret string | Yes | Non-blank; never included in errors, representations, or logs. |
| Request timeout | `TIMEOUT` | number | No | Defaults to `10.0`; must be finite, positive, and not boolean. |

The enclosing `PROMPTKIT` value must be a mapping. It has no additional properties:
every unknown key is a startup configuration error. Validation reports all affected
key names without reporting their supplied values.

## Registered SDK client

| Attribute | Type | Lifecycle rule |
|---|---|---|
| Client | `PromptKitClient` | Created after valid settings are parsed during `AppConfig.ready()`. |
| Owner | `PromptKitDjangoConfig` instance | One owner exists per Django Apps registry. |
| Identity | Object identity | Re-entering `ready()` returns the existing client; all public accesses return that same object. |
| Disposal | Host process/application lifecycle | This increment does not add dynamic reconfiguration or explicit client replacement. |

## Lifecycle transitions

```text
uninstalled -> access error
installed / starting -> validate settings -> configuration error OR registered
registered -> repeated startup/access -> same registered client
fresh Django Apps registry -> independent starting state
```

No state is written to the database, Django cache, settings module, or core SDK.
