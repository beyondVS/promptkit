# Phase 0 Research: Django SDK Integration Setup

## Decision: Use one `PROMPTKIT` settings mapping

The integration accepts `PROMPTKIT = {"BASE_URL": ..., "API_KEY": ...,
"TIMEOUT": ...}`. `BASE_URL` and `API_KEY` are required; `TIMEOUT` defaults to
`10.0` and must be a positive finite number.

**Rationale**: A single namespace prevents global-settings pollution, maps directly
to the current `PromptKitClient` constructor, and permits strict unknown-key
validation.

**Alternatives considered**:

- Flat `PROMPTKIT_*` settings: rejected because it weakens namespace validation and
  leaves future settings ownership ambiguous.
- Cache and ETag settings from older planning material: rejected as outside the
  Day 14 specification and the lightweight scope.

## Decision: Validate with Pydantic and normalize failures

A Pydantic v2 model accepts only the three known mapping keys. It validates mapping
shape, required keys, blank values, types, and timeout; the core client then remains
the authority for URL safety validation. Integration code converts either validation
source into an integration-specific Django configuration error containing field names
only.

**Rationale**: This meets the project Pydantic standard, aggregates settings errors,
and prevents a `ValidationError` or client exception from including a credential
value in its rendered text.

**Alternatives considered**:

- Hand-written dictionary checks: rejected because it duplicates schema behavior and
  makes aggregated, typed validation harder to maintain.
- Passing Pydantic/core exception text through unchanged: rejected because error
  rendering can include caller input.

## Decision: Keep the registered client on `PromptKitDjangoConfig`

`PromptKitDjangoConfig.ready()` validates settings and constructs a `PromptKitClient`
only when its own registration slot is empty. The public accessor resolves the active
Django AppConfig and returns that stored object; it never constructs a client.

**Rationale**: One AppConfig instance represents one Django Apps registry/lifecycle.
This supplies eager startup failure, repeated-startup idempotence, and isolation
between fresh test registries without a process-global client.

**Alternatives considered**:

- Module-global singleton: rejected because it can leak configuration across test
  registries and application lifecycles.
- Lazy accessor construction: rejected by the clarified startup-failure requirement.
- Django cache/database registration: rejected because no persisted state is needed.

## Decision: Depend on released-compatible `promptkit` and verify from a wheelhouse

`promptkit-django` declares a bounded compatible `promptkit` distribution version
range, not a sibling path or direct Git dependency. The packaging integration test
builds the current core SDK into a temporary wheelhouse, snapshots only the Django
package into a temporary Git repository, and installs its Git subdirectory into a
fresh environment with that wheelhouse supplied as a package source.

**Rationale**: The installed integration resolves the core package exactly as it
would from a package index while proving the Django package has no repository-root or
server import dependency.

**Alternatives considered**:

- Editable workspace install: rejected because it masks package metadata and path
  leaks.
- Direct sibling source dependency: rejected because it prevents independent
  deployment and couples package sources.
- A live registry or production credential: rejected because installation and
  registration require neither.

## Decision: Use only Django, promptkit, and Pydantic runtime dependencies

The package declares Django 5.x, a bounded promptkit 0.1.x compatible range, and
Pydantic v2 directly because it imports Pydantic validation types.

**Rationale**: This is the smallest dependency set that supports the requested
integration; no third-party registration or configuration package is needed.

**Alternatives considered**:

- Adding a configuration library: rejected as unnecessary abstraction and dependency
  weight.
