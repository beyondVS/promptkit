# Phase 1 Data Model: SDK Failure Resilience E2E Validation

This feature adds no persistent application entity. The following entities describe disposable test state and observable contracts.

## ManagedRegistry

| Field | Meaning | Validation |
|---|---|---|
| base_url | Ephemeral loopback HTTP URL supplied by `live_server` | HTTP is accepted only because the host is loopback |
| api_key | Test-only accepted credential | Non-empty and never written to exception/application-log output |
| readiness | Health response observed before SDK scenarios | HTTP 200 with the established service identity |
| lifecycle | Fixture-owned start and stop state | Setup/teardown failure is not an SDK scenario result |

## PublishedPromptFixture

| Field | Meaning | Validation |
|---|---|---|
| slug | Test-owned registry lookup identity | Unique in the test database |
| version | Published version exposed to the SDK | Positive version and designated on-live |
| template_text | Aggregate template containing declared placeholders | Contains a protected sentinel fragment for disclosure checks |
| variables | Required variable declarations | Includes inputs for missing, unexpected, and incompatible-type cases |
| sections | Ordered role content returned by the registry | Uses the same declarations as aggregate content |

## FailureScenario

| Field | Meaning | Validation |
|---|---|---|
| identifier | Stable scenario name | Unique within the matrix |
| stage | `configuration`, `communication`, `authentication`, or `compilation` | Exactly one authoritative stage |
| trigger | Controlled invalid state or action | Changes one failure cause at a time |
| expected_error | Public PromptKit exception class | Distinguishable from every other scoped class |
| expected_http_calls | Network requests allowed by the scenario | Zero for local configuration; one for communication/authentication |
| repetitions | Number of same-process executions | Three for the resilience matrix |

## ProtectedValueSet

| Field | Meaning | Validation |
|---|---|---|
| api_key | Distinctive invalid or accepted test credential | Absent from all inspected outputs |
| authorization_value | Complete test authorization-header representation | Absent from all inspected outputs |
| variable_value | Distinctive invalid supplied value | Absent from exception and application records |
| template_fragment | Distinctive full/template sentinel | Absent from failure diagnostics |

## FailureObservation

| Field | Meaning | Validation |
|---|---|---|
| exception_type | Public exception caught by the application | Equals `expected_error` |
| safe_message | Exception message available for caller diagnostics | Identifies stage/field without protected values |
| sdk_records | Captured `promptkit` namespace records from the scoped operation | Exactly zero |
| application_records | Records deliberately created after catching the exception | Contain only safe type/message information |
| compiled_result | Result assigned only on successful compilation | Absent for every validation failure |
| downstream_calls | Provider/downstream spy count | Exactly zero on every failure |

## Relationships and lifecycle

1. `ManagedRegistry` starts and passes readiness before a `PublishedPromptFixture` is retrieved.
2. One successful real-HTTP retrieval supplies the immutable prompt used by compilation `FailureScenario` values.
3. Each `FailureScenario` produces exactly one `FailureObservation`; no fallback or partial result is shared between scenarios.
4. The application may convert the safe exception type/message into an application record, but the SDK creates no record on these failure paths.
5. The complete scenario matrix runs three times in one process while logger configuration and prior protected values remain isolated.
6. Fixture teardown closes SDK clients and sockets, stops the managed server, and rolls back/deletes all test database state.
