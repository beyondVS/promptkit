# Feature Specification: SDK Remote Prompt Retrieval

**Feature Branch**: `010-sdk-rest-client`  
**Created**: 2026-08-07  
**Status**: Draft  
**Input**: User description: "Day 10 (1h): Python SDK (`packages/promptkit`) 환경 셋업 및 REST Client 개발. 독자적인 패키지 디렉토리 구조 및 `pyproject.toml` 설정 후 즉시 Git subdirectory 독립 설치 테스트 실행. 서버 API와 통신하여 프롬프트를 원격 조회하는 REST Client 모듈 및 유닛 테스트 작성."

## Clarifications

### Session 2026-08-07

- Q: What information should remote retrieval return for a prompt? → A: Prompt content, version metadata, and declared variable definitions.
- Q: How should the SDK handle transient communication failures? → A: Return the communication failure immediately without automatic retry.
- Q: Which retrieval call styles should this feature provide? → A: Synchronous calls only.
- Q: What default wait limit should retrieval use? → A: 10 seconds, overridable by the caller.
- Q: How should the SDK represent a server request-limit response? → A: Return a distinct rate-limit error.
- Q: How should callers supply the API key? → A: Explicitly when creating the client.
- Q: How should the SDK handle additional information in a registry response? → A: Reject missing required information and ignore unrecognized additional information.
- Q: How should the SDK handle the forbidden production label? → A: Reject it before making a request.
- Q: How should the SDK handle redirects from the registry? → A: Return an error for every redirect.
- Q: Which registry URL schemes should the SDK accept? → A: HTTPS and HTTP only for loopback addresses.
- Q: Should missing prompts and prompts without a deployable version be distinct outcomes? → A: Return distinct errors.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Retrieve a publishable prompt (Priority: P1)

An application developer retrieves a named prompt from the shared prompt registry so that the application can use the currently deployable prompt without copying its content into the application.

**Why this priority**: Remote retrieval is the minimum usable value of the SDK and allows prompt changes to be managed centrally.

**Independent Test**: Using only the SDK's public interface and a controlled registry response, a developer can request a named prompt and receive its content and published version information.

**Acceptance Scenarios**:

1. **Given** a named prompt has an on-live published version, **When** a developer retrieves it without choosing a label, **Then** the SDK returns that on-live version's prompt content and identifying metadata.
2. **Given** a named prompt has a published version assigned to an allowed label, **When** a developer retrieves it with that label, **Then** the SDK returns the matching published version.

---

### User Story 2 - Receive actionable retrieval failures (Priority: P2)

An application developer receives a clear, structured failure when a prompt cannot be retrieved, allowing the application to decide how to recover without silently using unintended content.

**Why this priority**: Predictable failures prevent applications from unknowingly serving stale, unpublished, or inaccessible prompts.

**Independent Test**: Controlled responses for missing prompts, unauthorized access, invalid requests, and temporary service failures each produce a distinguishable SDK outcome.

**Acceptance Scenarios**:

1. **Given** the requested prompt does not exist, **When** a developer retrieves it, **Then** the SDK reports a missing-prompt failure and does not substitute another prompt.
2. **Given** the requested prompt exists but has no deployable version for the requested resolution, **When** a developer retrieves it, **Then** the SDK reports a no-deployable-version failure and does not substitute another version.
3. **Given** the developer's credentials are rejected, **When** a developer retrieves a prompt, **Then** the SDK reports an authorization failure without exposing credential values.
4. **Given** the registry cannot be reached or returns an invalid response, **When** a developer retrieves a prompt, **Then** the SDK reports a failure that distinguishes a transient communication problem from an invalid registry response.

---

### User Story 3 - Install the SDK independently (Priority: P3)

An application developer installs the SDK as a standalone dependency from its package directory in the monorepo, so that the SDK can be adopted without bringing in unrelated server or framework components.

**Why this priority**: Independent distribution preserves the SDK-first architecture and makes external adoption practical.

**Independent Test**: In a clean environment, the SDK is installed from the package's subdirectory and its public prompt-retrieval interface can be imported.

**Acceptance Scenarios**:

1. **Given** a clean environment, **When** a developer installs from the SDK package subdirectory, **Then** installation completes without requiring the server application or framework-specific integration package.
2. **Given** the SDK is installed independently, **When** a developer imports its public interface, **Then** the import succeeds and exposes the documented retrieval capability.

### Edge Cases

- A prompt name is empty, malformed, or otherwise invalid; the SDK rejects the request before attempting retrieval.
- A requested label is not assigned to a published version; the SDK does not fall back to on-live, latest, production, or a draft version.
- A caller requests the forbidden `production` label; the SDK rejects the input before making a registry request.
- The registry returns incomplete prompt data; the SDK rejects it rather than returning a partially usable prompt.
- The registry returns unrecognized additional prompt data; the SDK ignores that data while retaining all required retrieved-prompt information.
- A request exceeds its configured or default 10-second wait limit; the SDK immediately reports a recoverable communication failure without automatic retry.
- The registry rejects a request because of a request limit; the SDK returns a distinct rate-limit error without automatic retry.
- The registry returns a redirect; the SDK returns a distinct retrieval error and does not follow the redirect.
- A registry URL uses HTTP for a non-loopback address; the SDK rejects the configuration before making a request.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The SDK MUST provide a documented public interface for retrieving one named prompt from the remote prompt registry.
- **FR-001a**: The public retrieval interface for this feature MUST be synchronous only; asynchronous retrieval is outside scope.
- **FR-002**: The SDK MUST support retrieval with no label and return only the prompt version designated as on-live.
- **FR-003**: The SDK MUST support retrieval by an explicitly supplied allowed label and return only the matching published prompt version.
- **FR-004**: The SDK MUST never substitute latest, production, a fallback label, an unpublished version, or another prompt when the requested deployable version is unavailable.
- **FR-004a**: The SDK MUST reject the forbidden `production` label before making a registry request.
- **FR-005**: The SDK MUST return the retrieved prompt content, declared variable definitions, and sufficient identifying metadata for the caller to determine which prompt version was received.
- **FR-006**: The SDK MUST authenticate retrieval requests using an API key explicitly supplied when the caller creates the client and MUST not store or expose that key in returned values or error messages.
- **FR-007**: The SDK MUST provide distinguishable, actionable outcomes for invalid input, missing prompts, prompts without a deployable version, authorization failures, rate-limit responses, communication failures, and invalid registry responses; communication failures and rate-limit responses MUST be returned without automatic retry.
- **FR-007a**: The SDK MUST use a 10-second default wait limit and allow the caller to supply a different wait limit.
- **FR-007b**: The SDK MUST reject a registry response that omits required retrieved-prompt information and MUST ignore unrecognized additional information in an otherwise valid response.
- **FR-007c**: The SDK MUST return a distinct error for a registry redirect and MUST not follow redirects.
- **FR-007d**: The SDK MUST accept HTTPS registry URLs and HTTP registry URLs only when their host is a loopback address.
- **FR-008**: The SDK MUST be installable and importable as an independent package without requiring the prompt server or framework-specific extension package.
- **FR-009**: The SDK's public retrieval behavior and error outcomes MUST be covered by automated isolated tests, including successful labeled and unlabeled retrieval and each failure category in FR-007.

### Key Entities *(include if feature involves data)*

- **Prompt retrieval request**: A caller's request for a named prompt, optionally scoped to a label, with credentials supplied separately.
- **Retrieved prompt**: The deployable prompt content and declared variable definitions returned to the caller, with its name, version identity, and publication/label information.
- **Retrieval outcome**: Either a retrieved prompt or a structured failure category that tells the caller why retrieval did not succeed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In controlled successful retrieval scenarios, 100% of requests return the exact prompt content, declared variable definitions, and version metadata designated by the registry.
- **SC-002**: In controlled scenarios where no eligible version exists, 100% of requests return no prompt and never return a fallback or unpublished version.
- **SC-003**: Automated isolated tests cover 100% of the public retrieval success paths and the seven failure categories: invalid input, missing prompt, no deployable version, authorization failure, rate-limit response, communication failure, and invalid response.
- **SC-004**: A developer can install the package from its monorepo subdirectory and complete a public-interface import check in a clean environment without installing unrelated project packages.

## Assumptions

- The prompt registry already exposes a read-only retrieval contract compatible with the project's published-version and label rules.
- Callers supply their own registry location and API key explicitly when creating the client; credentials are not embedded in application source code.
- This feature is limited to reading one prompt at a time; prompt creation, editing, deletion, batch retrieval, caching, compilation, and LLM invocation remain outside scope.
- Asynchronous retrieval is outside scope for this feature.
- The package will use the project's supported Python version and existing quality controls.
