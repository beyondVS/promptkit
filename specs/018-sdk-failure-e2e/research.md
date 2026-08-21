# Phase 0 Research: SDK Failure Resilience E2E Validation

## Decision 1: Use pytest-django `live_server` for the actual registry boundary

**Rationale**: The repository already depends on pytest-django and configures the Prompt Server settings for root pytest. `live_server` supplies a real loopback HTTP server on an ephemeral port, manages thread startup and teardown, and works on Windows without subprocess signal handling. A direct health request explicitly proves readiness before SDK assertions begin.

**Alternatives considered**:

- Django's in-process test client: rejected because it does not exercise the SDK's real HTTP transport.
- A `manage.py runserver` subprocess: rejected because environment setup, migrations, readiness polling, output capture, and Windows cleanup exceed the feature's scope.
- A custom WSGI server thread: rejected because pytest-django already owns the required lifecycle safely.

## Decision 2: Seed a published on-live prompt through existing lifecycle services

**Rationale**: The E2E journey must retrieve through the actual serializer before testing local compilation. Existing model and lifecycle helpers already encode prompt creation, publication, and on-live constraints. Transactional pytest-django access makes committed fixture data visible to the live-server thread while keeping it isolated in the test database.

**Alternatives considered**:

- Hard-code a registry response with `httpx.MockTransport`: rejected because existing tests already cover it and it bypasses the server boundary.
- Add a test-only API endpoint to seed data: rejected because it changes production routing and CUD scope unnecessarily.
- Depend on a developer database: rejected because it is non-repeatable and risks shared data.

## Decision 3: Prove readiness with the existing public health endpoint

**Rationale**: A successful `GET /api/v1/health/` separates server setup failure from the SDK communication-failure scenario. If readiness fails, the fixture/setup assertion fails directly rather than being caught as `CommunicationError`.

**Alternatives considered**:

- Treat the first SDK fetch as readiness: rejected because startup failures would be misclassified as the behavior under test.
- Add polling infrastructure: rejected because `live_server` already waits for startup; one health assertion is sufficient evidence.

## Decision 4: Use controlled loopback sockets for refused and mid-request-disconnect failures

**Rationale**: Binding an ephemeral loopback port while leaving the socket non-listening prevents another process from claiming it and makes connection refusal deterministic. A companion test-owned socket listener accepts one SDK connection and closes it before a response to model a mid-request disconnect. Both paths produce a real network error mapped to `CommunicationError` without retry. Sockets and clients are closed in fixture/finally cleanup.

**Alternatives considered**:

- Use a fixed closed port: rejected because it can collide with a local service or parallel test.
- Allocate and immediately release an unused port: rejected because the release introduces a time-of-check/time-of-use race.
- Stop the live Prompt Server and reuse its port: rejected because fixture internals should not be manipulated and teardown timing would be platform-sensitive.

## Decision 5: Keep the existing public exception hierarchy unchanged

**Rationale**: Current code already maps nonblank credential rejection over HTTP 401 to `AuthenticationError`, request/connection errors to `CommunicationError`, blank credentials to `InvalidConfigurationError` before transport creation, and invalid variables to distinct missing/unexpected/type errors. Compilation validates before rendering, so no partial `CompiledPrompt` exists. The implementation should add evidence first and change production code only if that evidence fails.

**Alternatives considered**:

- Add a new E2E-specific exception: rejected because the public categories already express recovery decisions.
- Collapse configuration and authentication errors: rejected by the clarification and existing client contract.
- Add retry/fallback: rejected by the feature scope and earlier SDK specification.

## Decision 6: Scope the zero-log assertion to the selected fetch/compile failure paths

**Rationale**: `client.py` and `compiler.py` currently emit no logs or configure logging. The adapter module has an existing, tested safe warning for a separate successful conversion edge case. Therefore, the E2E suite filters captured records to the `promptkit` namespace during the scoped communication, authentication, configuration, and variable-validation failures, and asserts zero SDK records and no logging-configuration mutation only for those scenarios. The calling application may log the safe exception type/message through a dedicated test logger.

**Alternatives considered**:

- Assert zero records from every logger: rejected because Django may legitimately log the HTTP 401.
- Remove all SDK logging, including the adapter warning: rejected because that changes an established contract outside this feature.
- Add structured logs to the client/compiler: rejected by clarification; logging belongs to the caller.

## Decision 7: Use sentinel scanning and a downstream zero-call spy for prohibited side effects

**Rationale**: Distinctive test-only API key, variable value, and template text make disclosure assertions deterministic across exception strings, formatted tracebacks where relevant, and application-created records. A simple provider/downstream spy remains at zero when compilation fails, demonstrating that no partial output escapes.

**Alternatives considered**:

- Inspect exceptions only: rejected because the feature also requires safe application logging.
- Invoke a real provider to prove it was not called: rejected because an in-memory counter proves the boundary without external cost or credentials.

## Decision 8: Add no new dependency and validate in increasing scope

**Rationale**: pytest, pytest-django, httpx, Django, and the SDK already provide every required capability. Run the focused E2E module first, then selected SDK/server regressions, static quality gates, and finally the full suite. This gives fast attribution while preserving the repository-wide harness.

**Alternatives considered**:

- Add a server-process or port-management package: rejected because standard fixtures and sockets are sufficient.
- Run only the new module: rejected because normal retrieval/compilation behavior must remain unchanged.
