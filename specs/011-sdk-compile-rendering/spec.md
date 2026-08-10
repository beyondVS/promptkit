# Feature Specification: SDK Local Prompt Compilation

**Feature Branch**: `011-sdk-compile-rendering`  
**Created**: 2026-08-10  
**Status**: Draft  
**Input**: User description: "Day 11 (1h): SDK compile() 로컬 렌더링 엔진 개발 — 프롬프트 내 동적 변수를 파싱하고 렌더링하는 compile() 메서드 개발. 헌법 규정에 명시된 Pydantic v2를 연동하여 주입될 변수의 구조 및 유효성(Validation) 검증 로직 및 유닛 테스트 작성."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Render a retrieved prompt locally (Priority: P1)

An application developer supplies values for a retrieved prompt's declared dynamic variables and receives the completed prompt locally, ready to pass to the developer's chosen LLM provider.

**Why this priority**: Local completion is the core SDK value: it lets applications use centrally managed prompt templates without moving rendering work or application data to the prompt registry.

**Independent Test**: Using a prompt with declared placeholders and valid values, a developer can invoke the public compilation operation and verify that every placeholder is replaced with the intended value.

**Acceptance Scenarios**:

1. **Given** a retrieved prompt declares two dynamic variables and contains both placeholders, **When** a developer supplies valid values for both, **Then** the SDK returns completed prompt content with both values rendered locally.
2. **Given** a retrieved prompt has no dynamic variables, **When** a developer compiles it without values, **Then** the SDK returns its content unchanged.

---

### User Story 2 - Receive clear validation feedback (Priority: P2)

An application developer receives a structured, actionable result when supplied values do not satisfy the prompt's declared variable requirements, so incorrect prompts are not sent onward accidentally.

**Why this priority**: Validating data before rendering prevents incomplete or invalid application context from producing misleading prompts.

**Independent Test**: Controlled inputs with a missing required value, an unexpected value, and a value of an invalid shape each produce a distinguishable validation failure and no completed prompt.

**Acceptance Scenarios**:

1. **Given** a prompt requires a dynamic variable, **When** a developer omits it, **Then** compilation reports that the required value is missing and returns no completed prompt.
2. **Given** a prompt declares a constrained variable structure, **When** a developer supplies data that violates the declaration, **Then** compilation reports the invalid field and reason without exposing unrelated supplied values.
3. **Given** a prompt declares its complete variable set, **When** a developer supplies an undeclared value, **Then** compilation rejects the input rather than silently ignoring it.

---

### User Story 3 - Preserve template safety and traceability (Priority: P3)

An application developer can distinguish a completed prompt from its original template and determine which prompt version was compiled, while malformed templates do not produce partially rendered content.

**Why this priority**: Traceability supports debugging, while refusing malformed templates avoids sending a mix of rendered and unresolved content to an LLM provider.

**Independent Test**: A controlled prompt with malformed, undeclared, or unresolved placeholders produces a structured compilation failure; a successful result retains the source prompt identity and version metadata.

**Acceptance Scenarios**:

1. **Given** a prompt contains a placeholder that is not declared by its variable definitions, **When** a developer compiles it, **Then** the SDK reports a template-definition mismatch and returns no partially completed content.
2. **Given** compilation succeeds, **When** the developer inspects the result, **Then** they can identify the source prompt and version used to create it.

### Edge Cases

- A template contains malformed placeholder syntax; compilation fails before any output is returned.
- A declared variable is absent from the template; compilation succeeds only if the declaration permits its omission; otherwise it fails with a declaration error.
- A supplied text value includes characters that resemble placeholder syntax; it is treated as supplied content and is not parsed a second time.
- A supplied value is null, empty, or nested; its acceptance follows the variable's declared requiredness and structure.
- The same declared variable appears multiple times; every occurrence is rendered consistently from the single validated value.
- A template resolves all placeholders but receives an unexpected extra input; compilation rejects the input rather than discarding it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The SDK MUST provide a documented public operation that creates a completed prompt from one retrieved prompt template and caller-supplied values, without sending the values to the prompt registry.
- **FR-002**: The operation MUST parse the template's dynamic placeholders and render every valid occurrence of each declared variable using the corresponding validated value.
- **FR-003**: The operation MUST validate the caller-supplied value set against the prompt's declared variable names, requiredness, and declared data structures before rendering.
- **FR-004**: The operation MUST reject missing required values, undeclared supplied values, malformed values, malformed placeholders, and mismatches between a placeholder and the prompt's declared variables.
- **FR-005**: When validation or template parsing fails, the SDK MUST provide a structured, actionable failure that identifies the affected variable or template condition and MUST NOT return partially rendered prompt content.
- **FR-006**: Values supplied for rendering MUST be treated as content and MUST NOT be recursively interpreted as additional template syntax.
- **FR-007**: A successful completed prompt MUST retain enough source identity and version information for a developer to determine which retrieved prompt was compiled.
- **FR-008**: Prompts with no declared dynamic variables MUST compile successfully without caller-supplied values and preserve their content exactly.
- **FR-009**: The public compilation behavior and validation outcomes MUST be covered by isolated automated tests, including successful rendering, repeated variables, no-variable prompts, missing values, unexpected values, invalid structures, and malformed or inconsistent templates.

### Key Entities *(include if feature involves data)*

- **Prompt template**: A retrieved prompt's content, declared dynamic-variable definitions, and source identity and version information.
- **Variable declaration**: The allowed name, requiredness, and expected value structure for a dynamic variable in a prompt template.
- **Compilation input**: The complete set of values supplied by the application developer for one compilation attempt.
- **Completed prompt**: The locally rendered prompt content together with the identity and version of its source template.
- **Compilation failure**: A structured outcome that explains why a template or compilation input could not be completed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In controlled valid-input scenarios, 100% of declared placeholder occurrences are rendered with their corresponding supplied values and no placeholder remains unresolved.
- **SC-002**: In controlled invalid-input and malformed-template scenarios, 100% of compilation attempts return no completed prompt and identify at least one actionable failure reason.
- **SC-003**: Automated isolated tests cover 100% of the public compilation success paths and the validation and template-failure categories defined in FR-009.
- **SC-004**: A developer can compile a valid template containing up to 50 declared variables and 200 placeholder occurrences in under one second on a standard development machine.

## Assumptions

- This feature extends the retrieved-prompt model introduced by the preceding SDK retrieval feature; it does not create, edit, or fetch prompts.
- Variable declarations supplied with a retrieved prompt are the authoritative contract for the names, requiredness, and data structures accepted during compilation.
- The first release supports deterministic text-template completion only; LLM invocation, provider-specific request formatting, server-side rendering, caching, and template authoring remain outside scope.
- Invalid compilation attempts return an exception or error outcome in the SDK's established public error style; they do not log or expose caller-supplied values by default.
- The project quality controls and supported runtime version apply to the SDK and its automated tests.
