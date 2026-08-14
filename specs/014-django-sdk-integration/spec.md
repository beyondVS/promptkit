# Feature Specification: Django SDK Integration Setup

**Feature Branch**: `014-django-sdk-integration`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Day 14 (1h): Django Integration 패키지 (`packages/promptkit-django`) 셋업 — Django 설정(`settings.py`) 파일과의 연동 매커니즘 구현 및 SDK 인스턴스 자동 등록. 패키지 생성 직후 Git subdirectory 독립 설치 가능 여부 즉시 검증."

## Clarifications

### Session 2026-08-14

- Q: How must an independent `promptkit-django` installation obtain the core SDK? → A: Depend on a compatible released `promptkit` distribution; use a local distribution artifact to reproduce package-index resolution when the core SDK is not yet published externally.
- Q: When must invalid integration settings fail? → A: Validate during startup and fail application initialization immediately.
- Q: How must unknown keys in the integration settings namespace be handled? → A: Reject them during startup and report each unknown key name.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure PromptKit through the host project (Priority: P1)

A Django application developer declares the PromptKit connection values in the project's normal settings and uses the integration without manually translating those values into a core SDK client.

**Why this priority**: Central configuration is the essential value of the integration package and prevents each application component from constructing the SDK differently.

**Independent Test**: A minimal host project can supply valid PromptKit settings, initialize the integration, and retrieve a configured SDK client whose observable configuration matches the declared values.

**Acceptance Scenarios**:

1. **Given** a host project declares all required PromptKit settings, **When** the integration initializes, **Then** a configured SDK client becomes available without manual client construction.
2. **Given** an optional PromptKit setting is omitted, **When** the integration initializes, **Then** the documented default is applied consistently.
3. **Given** a required setting is absent or invalid, or the settings namespace contains an unknown key, **When** the installed integration initializes during application startup, **Then** application initialization fails immediately with an actionable configuration error that identifies each affected or unknown setting without exposing secret values.

---

### User Story 2 - Reuse one automatically registered SDK instance (Priority: P1)

An application developer accesses PromptKit from multiple application components and receives the same configured SDK instance registered during application startup.

**Why this priority**: Predictable automatic registration removes repeated setup, prevents configuration drift, and aligns the integration with the host application's lifecycle.

**Independent Test**: Initialize a minimal host application, request the integration client from two independent components, and verify both receive the same ready-to-use instance without constructing it themselves.

**Acceptance Scenarios**:

1. **Given** valid settings and an installed integration application, **When** the host application finishes startup, **Then** exactly one SDK instance is registered for shared access.
2. **Given** the integration has already initialized, **When** startup initialization is invoked again, **Then** no duplicate client is created and the existing registration remains usable.
3. **Given** two application components request the client after startup, **When** each resolves the registration, **Then** both receive the same instance.
4. **Given** the integration has not been installed or initialized, **When** a component requests its client, **Then** it receives an actionable integration error rather than an unconfigured client.

---

### User Story 3 - Install the integration package independently (Priority: P1)

A package maintainer or adopter installs only the Django integration from the repository's package subdirectory and can import it in a clean environment.

**Why this priority**: Independent subdirectory installation is a constitutional packaging requirement and must be proven immediately so package scaffolding cannot accumulate hidden monorepo dependencies.

**Independent Test**: Build a clean isolated environment, install from the integration package's Git subdirectory reference, and import and initialize it in a minimal host project without adding repository-root or server sources to the import path.

**Acceptance Scenarios**:

1. **Given** a clean supported environment and repository access, **When** only the integration package's Git subdirectory is installed, **Then** installation completes with all declared runtime dependencies resolved.
2. **Given** that isolated installation, **When** the integration and its declared public entry points are imported, **Then** imports succeed without access to the monorepo checkout.
3. **Given** a minimal host project using the isolated installation, **When** it initializes with valid settings, **Then** automatic SDK registration succeeds.

### Edge Cases

- Settings are present but have the wrong type or contain a blank required value; startup fails and identifies each affected setting.
- The settings namespace contains one or more unknown keys; startup fails and identifies every unknown key rather than ignoring it or continuing with a warning.
- The API key contains whitespace or non-ASCII characters; validation does not disclose the value in errors or logs.
- The host settings are overridden between isolated test contexts; a new application lifecycle uses its own configuration without leaking the prior registration.
- Startup hooks run more than once because of development reload, test setup, or application-registry behavior.
- Client access occurs before application initialization has completed; access fails as uninitialized and does not bypass startup validation or construct a client lazily.
- The core SDK is absent, incompatible, or accidentally resolved from the monorepo root instead of the integration package's declared dependency.
- The Git subdirectory path is used from a clean clone with no editable install and no repository-root path injection.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The integration package MUST provide one documented host-project settings namespace for all PromptKit client configuration.
- **FR-002**: The settings contract MUST identify required values, optional values, their accepted types, and deterministic defaults.
- **FR-003**: The initial settings contract MUST support the registry base URL and API key required by the existing read-only core SDK client.
- **FR-004**: Configuration MUST be read from the host project's active settings, including supported test and deployment overrides, and MUST NOT modify the host settings file.
- **FR-005**: During application startup, missing, blank, wrongly typed, or otherwise invalid required configuration MUST immediately fail application initialization with an actionable integration-specific error that identifies each affected setting.
- **FR-006**: During application startup, every unknown key in the integration settings namespace MUST immediately fail application initialization and be identified by name; unknown keys MUST NOT be ignored or treated as warnings.
- **FR-007**: Errors, representations, and logs produced by the integration MUST NOT expose the API key or other credential values.
- **FR-008**: Installing the integration as a host application MUST automatically construct and register one configured core SDK client during the host application's normal startup lifecycle.
- **FR-009**: Automatic registration MUST be idempotent within one application lifecycle and MUST NOT create duplicate clients when initialization runs repeatedly.
- **FR-010**: The integration MUST expose a documented public access operation that returns the registered client to application code without requiring manual client construction.
- **FR-011**: Repeated access within one initialized application lifecycle MUST return the same registered client instance.
- **FR-012**: Access before successful installation or completed initialization MUST fail with an actionable integration-specific error and MUST NOT defer configuration validation, silently create an unconfigured client, or lazily construct a configured client.
- **FR-013**: The integration MUST preserve the core SDK's framework-agnostic package boundary; the core SDK MUST NOT acquire a dependency on the integration or host framework.
- **FR-014**: The integration package MUST declare a compatible released version range of the core `promptkit` distribution plus all other dependencies and package metadata needed for installation directly from its Git repository subdirectory in a clean supported environment.
- **FR-015**: Independent-install validation MUST prove dependency resolution, installation, package import, public entry-point import, and automatic registration in a minimal host project without editable installation, repository-root import paths, or Prompt Server source code; when the compatible core SDK is not yet published externally, the validation MUST supply its built distribution through a local package source that reproduces normal package-index resolution.
- **FR-016**: Independent-install validation MUST run immediately after the initial package scaffold is created and MUST fail the feature gate if packaging metadata, dependency resolution, imports, or startup registration are incomplete.
- **FR-017**: The package MUST remain limited to SDK integration concerns and MUST NOT add prompt creation, update, deletion, LLM invocation, provider selection, tracing, evaluation, analytics, or workflow behavior.
- **FR-018**: All new public integration behavior and failure paths MUST have repeatable automated contract coverage.

### Key Entities *(include if feature involves data)*

- **Integration settings**: The host-owned configuration values and defaults used to construct the read-only SDK client, including sensitive values that must remain undisclosed.
- **Registered SDK client**: The single configured core SDK instance shared within one initialized host application lifecycle.
- **Integration application**: The installable host-framework component that validates settings and performs lifecycle registration.
- **Independent installation artifact**: The integration package and declared dependencies as resolved solely from its repository subdirectory.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can configure and obtain a ready-to-use registered SDK client using one host-project settings block and no manual client construction.
- **SC-002**: 100% of repeated initialization and access checks within one application lifecycle resolve exactly one shared SDK instance.
- **SC-003**: 100% of tested missing, blank, wrongly typed, and unknown-setting cases fail application initialization during startup and produce an actionable error naming every affected or unknown setting with zero credential-value disclosure.
- **SC-004**: One clean Git subdirectory installation resolves the declared compatible core SDK distribution and completes successfully, and all documented public imports plus minimal application initialization pass without repository-root or server-source access.
- **SC-005**: The independent-install check is completed in the same package-creation increment and blocks completion on any installation, dependency, import, or registration failure.
- **SC-006**: 100% of newly documented public integration operations and failure categories pass repeatable automated contract checks.
- **SC-007**: Existing core SDK consumers continue to install and operate without installing the host framework or integration package.

## Assumptions

- This increment provides one default registered client per host application lifecycle; multiple named clients and runtime reconfiguration are outside scope.
- The integration consumes the existing read-only core SDK client and does not duplicate retrieval, compilation, or adapter logic.
- The integration depends on a compatible released `promptkit` distribution rather than a direct URL to a sibling source directory; before external publication, a locally built core distribution may act as the package source solely for independent-install validation.
- The registry base URL and API key are the only client-construction settings required by the current core SDK; additional configuration is added only when an existing core client contract requires it.
- The host project's established settings override mechanisms remain valid for tests and deployments; the integration does not edit or generate `settings.py`.
- Automatic registration and eager settings validation occur through the host framework's standard installed-application startup lifecycle; invalid settings prevent startup completion, and application code accesses the completed registration only after successful startup.
- Independent-install validation uses a clean isolated environment and the same supported runtime range declared by the project.
- Live registry connectivity and live credentials are unnecessary for package installation, imports, settings validation, and client registration tests.
- Prompt Server behavior, database schema, dashboard functionality, and core SDK public behavior are unchanged by this feature.
