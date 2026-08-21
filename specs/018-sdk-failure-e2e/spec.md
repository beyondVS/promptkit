# Feature Specification: SDK Failure Resilience E2E Validation

**Feature Branch**: `018-sdk-failure-e2e`

**Created**: 2026-08-21

**Status**: Draft

**Input**: User description: "Day 18 (1h): E2E 통합 테스트 및 예외 시나리오 정밀 점검. 서버 다운, 잘못된 변수 주입, 인증 오류 발생 시 SDK의 예외 처리와 로깅 구조의 복원성 검증."

## Clarifications

### Session 2026-08-21

- Q: 서버 다운, 인증 오류, 변수 검증 오류가 발생할 때 SDK 자체가 진단 로그를 생성해야 합니까? → A: SDK는 로그를 생성하지 않고 안전한 예외만 제공하며, 호출 애플리케이션이 예외를 로깅한다.
- Q: 인증 오류 테스트에서 실행 중인 registry는 어느 수준까지 실제 서버여야 합니까? → A: 테스트가 관리하는 로컬 HTTP 서버를 실제 SDK client로 호출한다.
- Q: API key가 비어 있거나 형식상 사용할 수 없는 경우도 서버 인증 오류와 같은 예외로 처리해야 합니까? → A: 빈 값·잘못된 구성은 configuration failure, 서버가 non-empty key를 거부하면 authentication failure로 구분한다.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Distinguish registry availability and authentication failures (Priority: P1)

An application developer can distinguish an unavailable prompt registry from rejected credentials, allowing the application to choose an appropriate recovery action without guessing from raw transport details.

**Why this priority**: Registry and authentication failures occur before a prompt can be used and require different operational responses.

**Independent Test**: Run the public SDK retrieval flow once against a controlled unused loopback endpoint and once through HTTP against a test-managed local Prompt Server with a rejected API key, then verify that each produces its documented public failure category and no prompt result.

**Acceptance Scenarios**:

1. **Given** a valid SDK configuration points to a registry endpoint that is unavailable, **When** a developer retrieves a prompt, **Then** the call ends with a communication failure that remains distinguishable from authentication, response, and prompt-resolution failures.
2. **Given** the registry is running and the supplied API key is rejected, **When** a developer retrieves a prompt, **Then** the call ends with an authentication failure that remains distinguishable from registry unavailability.
3. **Given** either retrieval fails, **When** the developer inspects the outcome, **Then** no prompt or substitute version is returned and the original public failure remains available to application recovery logic.
4. **Given** the API key is empty or unusable as client configuration, **When** a developer creates the SDK client, **Then** the SDK reports a configuration failure before making any HTTP request rather than reporting a server authentication failure.

---

### User Story 2 - Reject invalid variables without partial output (Priority: P1)

An application developer receives an actionable compilation failure when retrieved prompt variables are missing, unexpected, or invalid, while no partially compiled prompt escapes to downstream consumers.

**Why this priority**: Incorrect variable injection can silently corrupt an LLM request unless compilation fails atomically and identifies the input problem.

**Independent Test**: Retrieve a controlled published prompt and compile it separately with a missing required variable, an unexpected variable, and an invalid variable type; every case must produce the expected public validation failure and no compiled result.

**Acceptance Scenarios**:

1. **Given** a retrieved prompt requires a variable, **When** compilation omits that variable, **Then** the SDK reports the missing variable and returns no compiled prompt.
2. **Given** a retrieved prompt declares a complete variable set, **When** compilation includes an undeclared variable, **Then** the SDK reports the unexpected variable and returns no compiled prompt.
3. **Given** a retrieved prompt constrains a variable's accepted type, **When** compilation receives an incompatible value, **Then** the SDK reports the invalid variable and returns no compiled prompt.
4. **Given** one invalid value accompanies otherwise valid values, **When** compilation fails, **Then** no partially substituted section or aggregate prompt is exposed as a successful result.

---

### User Story 3 - Log SDK failures safely in the calling application (Priority: P2)

An application developer can catch a safe, distinguishable SDK exception and apply the application's own logging policy without exposing credentials, supplied variable values, or full prompt content.

**Why this priority**: Safe diagnostics shorten incident response while preserving the SDK's role as a library and protecting secrets and application data.

**Independent Test**: Capture each public exception without application logging and then log only safe exception metadata through an application-selected configuration, verifying exception usefulness, redaction, and the absence of SDK-emitted records or global logging changes.

**Acceptance Scenarios**:

1. **Given** registry availability, authentication, or compilation validation fails, **When** the application catches the SDK exception, **Then** its public category and safe message provide enough context for the application to identify and log the failed stage.
2. **Given** an API key, distinctive variable value, and distinctive prompt text are used in a failure scenario, **When** all exception renderings and application-created log records are inspected, **Then** none contains those protected values.
3. **Given** the application has selected its own handlers, levels, and output destinations, **When** the SDK is imported and failure scenarios run, **Then** the SDK emits no records and does not add, replace, or reconfigure the application's logging setup.
4. **Given** the application performs no logging, **When** any failure occurs, **Then** the public exception category and message semantics remain observable to the caller unchanged.

### Edge Cases

- The selected unavailable endpoint refuses a connection immediately or exceeds the configured wait limit; both remain communication failures and do not become authentication failures.
- A server becomes unavailable after a connection starts; the SDK still returns a communication failure without a partial prompt.
- An API key contains characters that would be conspicuous in a log; neither the key nor an authorization header representation appears in diagnostics or exception text.
- An API key is empty or unusable as local client configuration; it produces a configuration failure before any HTTP request and is not treated as a server authentication rejection.
- The registry rejects a non-empty expired, revoked, or unknown API key; it produces the established authentication failure without disclosing the credential or the server's credential-management detail.
- Multiple variable defects occur together; the outcome remains a validation failure, names only fields needed for correction, and does not include supplied values.
- A variable value contains newlines, Unicode, or placeholder-like text; redaction checks compare the complete value and no secondary rendering occurs.
- An application logging handler fails or rejects a record after catching an SDK exception; that application-owned logging failure does not alter the SDK exception that was already delivered.
- Failure scenarios run repeatedly in one process; the SDK emits no records, installs no handlers, and protected data from an earlier run does not appear in later application-created records.
- The test-managed local Prompt Server fails to start or become ready; the E2E setup fails explicitly instead of reclassifying setup failure as an SDK communication result.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The validation suite MUST manage a local HTTP Prompt Server and exercise the public SDK client across that real HTTP boundary for successful setup and authentication rejection, while using a separate controlled unused loopback endpoint for the server-down scenario.
- **FR-001a**: The validation suite MUST start, confirm readiness of, and stop its local Prompt Server without requiring a separately running developer service; server setup failure MUST remain distinguishable from an asserted SDK failure scenario.
- **FR-002**: Registry unavailability MUST produce the established public communication failure and MUST NOT return a prompt, follow a substitute source, or be misclassified as authentication or invalid response failure.
- **FR-003**: A running registry's rejection of a non-empty supplied credential MUST produce the established public authentication failure and MUST NOT expose the credential in the exception or application-created diagnostics.
- **FR-003a**: An empty or otherwise unusable API key configuration MUST produce the established public configuration failure before any HTTP request and MUST remain distinguishable from server authentication rejection.
- **FR-004**: The validation suite MUST retrieve a controlled published prompt before exercising compilation validation so that variable failures prove the combined retrieval-to-compilation consumer journey.
- **FR-005**: Missing required variables, unexpected variables, and incompatible variable values MUST each produce their established distinguishable public validation failure.
- **FR-006**: Every compilation validation failure MUST be atomic: no role section, aggregate prompt, or provider-ready value may be returned as a successful or partial compilation result.
- **FR-007**: Public exception categories and safe messages MUST allow the calling application to identify whether failure occurred during registry communication, authentication, or local compilation and MUST remain the caller's authoritative outcome.
- **FR-008**: Exception text and application-created diagnostic records based on that text MUST NOT contain API keys, authorization header values, supplied variable values, full template content, or full compiled prompt content.
- **FR-009**: Importing or using the SDK MUST NOT emit log records, install handlers, change logger or root levels, or select an output destination; the calling application owns all logging decisions.
- **FR-010**: Application logging being disabled, filtered, or failed after exception delivery MUST NOT change the SDK's public exception category or message semantics.
- **FR-011**: The automated scenarios MUST be repeatable without external LLM calls, paid operations, production credentials, or modification of shared or production prompt data.
- **FR-012**: The failure checks MUST assert both the expected exception and prohibited side effects, including no fallback prompt, no downstream provider invocation, no secret disclosure, no SDK-emitted log record, and no SDK-installed logging handler.
- **FR-013**: The validation scope MUST remain limited to server unavailability, registry authentication rejection, invalid compilation variables, and their diagnostic behavior; retry policy, telemetry backends, dashboards, tracing, and new recovery mechanisms are outside scope.
- **FR-014**: Existing successful retrieval and compilation contract checks MUST continue to pass, demonstrating that failure-path validation does not alter normal SDK outcomes.

### Key Entities

- **Failure scenario**: A controlled arrangement of registry availability, credential validity, prompt contract, and supplied variables with one expected public outcome and explicitly prohibited side effects.
- **Public failure outcome**: The SDK exception category and safe explanatory context available to application recovery logic.
- **Application diagnostic record**: Metadata the calling application chooses to record after catching a safe SDK exception, excluding credentials, variable values, and prompt bodies.
- **Protected value sentinel**: A distinctive test-only credential, variable value, or prompt fragment used to prove that exception and logging output do not leak protected data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of server-down, local credential-configuration, and server authentication-rejection runs produce their correct, mutually distinguishable public failure category and return zero prompt results; local configuration failures issue zero HTTP requests.
- **SC-002**: 100% of missing, unexpected, and incompatible variable scenarios return no compiled or partially compiled prompt and identify the affected input field or validation reason.
- **SC-003**: Across all failure scenarios, searches of captured exception text and application-created diagnostic records find zero occurrences of the API key, authorization header value, supplied variable values, full template content, or full compiled content.
- **SC-004**: 100% of failure scenarios provide a public exception category and safe message from which the calling application can identify the failed stage, regardless of whether the application logs it.
- **SC-005**: Repeating the complete failure suite at least three times in one process produces zero SDK-emitted log records, installs zero SDK logging handlers, and causes zero cross-run disclosure of protected values.
- **SC-006**: The full automated validation completes within the Day 18 one-hour work session, requires zero external LLM requests and zero production credentials, and leaves shared prompt data unchanged.
- **SC-007**: 100% of the existing successful public retrieval and compilation regression checks selected for this scope continue to pass.

## Assumptions

- The established public exception categories from the retrieval and compilation features remain authoritative; this feature validates their integration and only permits minimal corrections where the tests expose a contract defect.
- The automated suite owns a disposable local HTTP Prompt Server and test-owned prompt/API-key fixtures, so no separately running developer service or shared or production data is required.
- Server-down behavior is verified with a controlled unreachable local endpoint rather than by stopping a developer's or shared registry process.
- The SDK remains synchronous and performs no automatic retry, consistent with the existing retrieval contract.
- The SDK emits no diagnostic logs; the consuming application may log safe exception category and message information under its own policy.
- Exact exception message wording is not a compatibility guarantee, but failure category, safe field identification, and absence of protected values are required.
- External LLM invocation, provider response handling, performance/load testing, new retry or fallback behavior, and observability infrastructure are outside scope.
