# Feature Specification: LiteLLM Adapter and SDK Harness

**Feature Branch**: `013-litellm-sdk-harness`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Day 13 (1h): LiteLLM Adapter 구현 및 SDK 전체 하네스 통합 검증 — LiteLLM 규격에 대응하는 어댑터 추가 구현. SDK core의 모든 Public API에 대해 pytest 100% 통합 하네스 검증 구동."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a compiled prompt for LiteLLM (Priority: P1)

An application developer converts a provider-neutral compiled prompt into LiteLLM-compatible completion arguments, then adds the model and other invocation settings owned by the application.

**Why this priority**: LiteLLM support is the new user-facing capability and lets one compiled prompt cross an additional provider boundary without coupling PromptKit to provider execution.

**Independent Test**: A developer can convert a compiled prompt containing system, user, and assistant sections and verify the exact ordered LiteLLM message arguments without installing or calling LiteLLM.

**Acceptance Scenarios**:

1. **Given** a compiled prompt contains ordered system, user, and assistant sections, **When** it is converted for LiteLLM, **Then** every section appears as one ordered role/content message with unchanged text.
2. **Given** a compiled prompt has no sections but has aggregate content, **When** it is converted for LiteLLM, **Then** the aggregate content appears as one user message.
3. **Given** a valid compiled prompt, **When** it is converted, **Then** no model, credentials, generation settings, provider dependency, or external request is introduced by PromptKit.

---

### User Story 2 - Validate the complete public SDK journey (Priority: P1)

An SDK maintainer runs one repeatable harness that proves every documented core SDK public symbol participates in a valid user journey or a defined failure path.

**Why this priority**: Existing isolated tests do not by themselves prove that the exported package surface works coherently from retrieval through compilation and provider conversion.

**Independent Test**: The harness inventories the package's declared public exports, maps every export to at least one assertion, and completes a local retrieval-to-compilation-to-conversion journey using controlled registry responses.

**Acceptance Scenarios**:

1. **Given** the SDK's declared public export list, **When** the harness runs, **Then** every exported client, model, adapter, argument contract, and exception is importable from the package root and covered by at least one public-contract assertion.
2. **Given** a successful controlled registry response, **When** the harness retrieves, compiles, and converts the prompt through every supported adapter target, **Then** metadata, rendered content, roles, and ordering remain consistent across the complete journey.
3. **Given** each defined configuration, request, transport, response, compilation, and adapter failure category, **When** the harness exercises its public path, **Then** the documented public exception is observable without exposing credentials or rendered secret values.

---

### User Story 3 - Detect public surface drift (Priority: P2)

An SDK maintainer receives an immediate, actionable failure when a public export is added or removed without corresponding harness coverage.

**Why this priority**: An explicit drift guard keeps the promise of complete public API validation true as the SDK evolves.

**Independent Test**: Add an unmapped public export in an isolated test change and confirm that the public-surface coverage check fails and identifies the unmapped name.

**Acceptance Scenarios**:

1. **Given** a public symbol is added without a harness mapping, **When** validation runs, **Then** it fails and names the uncovered symbol.
2. **Given** a stale mapping references a symbol no longer exported, **When** validation runs, **Then** it fails and names the stale entry.

### Edge Cases

- Sections arrive out of sequence; conversion resolves them by ascending order.
- Two sections have the same order; conversion fails without returning partial arguments.
- A section has an unsupported, blank, or differently cased role; conversion rejects it rather than guessing.
- A prompt contains only system sections; LiteLLM receives ordered system messages and the same safe system-only warning policy as existing adapters applies.
- Text is empty, whitespace-only, multiline, Unicode, or resembles a template placeholder; conversion preserves it exactly.
- A sectionless prompt contains empty aggregate content; it is still represented as one user message and content acceptance remains the caller's responsibility.
- The controlled registry returns every documented HTTP failure, malformed data, or a transport failure; the public error mapping remains stable and no real registry is contacted.
- An exported typed argument contract has no runtime constructor behavior beyond its dictionary contract; the harness validates its root import and its use in the corresponding adapter result.
- A future export changes the public inventory; the harness cannot continue to report complete coverage until the coverage map is updated.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The core SDK MUST expose a documented LiteLLM conversion operation that accepts a completed provider-neutral prompt and returns completion arguments containing an ordered `messages` collection.
- **FR-002**: Each LiteLLM message MUST contain exactly the applicable provider-neutral role (`system`, `user`, or `assistant`) and unchanged string content from one resolved prompt section.
- **FR-003**: LiteLLM conversion MUST sort sections by ascending order, preserve repeated roles as separate messages, and reject duplicate order values or unsupported roles without a partial result.
- **FR-004**: When a compiled prompt contains no sections, LiteLLM conversion MUST represent its aggregate content as one user-role message.
- **FR-005**: When a compiled prompt contains only system sections, LiteLLM conversion MUST preserve them as ordered system messages and record exactly one standard warning containing source slug, version, and label but no compiled prompt text.
- **FR-006**: LiteLLM conversion MUST NOT mutate or re-render the compiled prompt, select or add a model, add credentials or generation settings, import a provider package, initiate a provider request, or add source metadata to message content.
- **FR-007**: LiteLLM conversion MUST preserve empty strings, whitespace, line breaks, Unicode characters, and placeholder-shaped text exactly.
- **FR-008**: The LiteLLM adapter, its message contract, its completion-argument contract, and its conversion failure MUST be available through the same package-root public surface used by existing adapters.
- **FR-009**: The integration harness MUST derive the expected public inventory from the SDK's declared package-root exports and MUST fail for both unmapped current exports and stale coverage-map entries.
- **FR-010**: Every current package-root public export MUST have at least one harness assertion covering its documented public contract; import-only checks are sufficient only for type-only argument contracts whose produced values are behaviorally validated through their adapter.
- **FR-011**: The harness MUST validate a complete local journey from authenticated read-only retrieval through prompt compilation to every supported provider conversion target, including LiteLLM, with no real network or provider call.
- **FR-012**: The harness MUST validate the public data contracts for retrieved prompts, categories, variables, source sections, compiled prompts, and compiled sections, including validation boundaries, immutability where promised, and metadata preservation.
- **FR-013**: The harness MUST exercise every public exception through its documented public failure path where one exists, and MUST otherwise validate its public hierarchy and import contract.
- **FR-014**: Failure-path validation MUST cover invalid client configuration, invalid request and label input, authentication, rate limiting, redirects, missing prompts, missing labels, absent deployable versions, transport failures, invalid registry responses, compilation variable/template failures, and adapter conversion failures.
- **FR-015**: Harness failures MUST identify the public symbol or user journey that violated its contract and MUST NOT disclose API keys, caller-supplied secret values, or rendered prompt text prohibited from logs.
- **FR-016**: Existing independently installable, framework-agnostic, read-only SDK behavior MUST remain intact; the feature MUST NOT require the Prompt Server, Django integration, or LiteLLM package at runtime merely to convert arguments.
- **FR-017**: Existing isolated tests and the full public integration harness MUST complete successfully together under the project's standard SDK validation command.

### Key Entities *(include if feature involves data)*

- **Compiled prompt**: An immutable, provider-neutral rendered prompt carrying source traceability and ordered role sections.
- **LiteLLM message**: One plain role/content item corresponding to exactly one resolved compiled section.
- **LiteLLM completion arguments**: Plain invocation data containing ordered messages while excluding caller-owned model and execution settings.
- **Public API inventory**: The authoritative set of names intentionally exported from the SDK package root.
- **Public API coverage map**: A verifiable mapping from every inventory entry to one or more assertions of its documented contract.
- **Integration journey**: A controlled end-to-end SDK flow joining retrieval, local compilation, and all provider conversions without external side effects.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of LiteLLM conversion cases preserve source message text, applicable role, and resolved ordering exactly.
- **SC-002**: 100% of names in the declared public SDK inventory are importable from the package root and mapped to at least one passing public-contract assertion, with zero stale mappings.
- **SC-003**: One repeatable local validation run completes the retrieval-to-compilation-to-conversion journey for every supported adapter target with zero real external requests.
- **SC-004**: 100% of documented public failure categories produce their expected public error or warning contract without credential, secret value, or prohibited prompt-text disclosure.
- **SC-005**: Adding one intentionally unmapped public name causes validation to fail and identify that exact name on the next run.
- **SC-006**: The complete core SDK validation suite finishes with zero failures and no regression in any previously supported public journey.

## Assumptions

- "100%" means 100% coverage of the declared package-root public API inventory, not a requirement for 100% line or branch coverage of private implementation details.
- LiteLLM compatibility targets its common text completion message contract: an ordered `messages` list of role/content dictionaries. Model selection and all other completion parameters remain caller-owned.
- The LiteLLM adapter is conversion-only, matching the existing adapter boundary; it neither depends on LiteLLM at runtime nor calls an LLM.
- Provider-neutral roles remain exactly `system`, `user`, and `assistant`; tool calls, developer roles, multimodal content, function messages, and provider-specific extensions are outside this increment.
- Existing shared rules for section ordering, duplicate orders, unsupported roles, sectionless fallback, immutability, text fidelity, and safe system-only warnings apply to LiteLLM.
- Integration means public components are exercised together with controlled local substitutes at external boundaries; it does not authorize contact with a live registry or LLM provider.
- The declared package-root export list is the source of truth for public inventory. Internal modules, private helpers, and undeclared transitive imports are outside the 100% target.
- Existing unit tests remain valuable and are retained; the new harness adds cross-component and public-surface guarantees rather than replacing isolated tests.
