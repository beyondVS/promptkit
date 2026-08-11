# Feature Specification: Gemini and OpenAI Prompt Adapters

**Feature Branch**: `012-provider-adapters`
**Created**: 2026-08-11
**Status**: Draft
**Input**: User description: "Day 12 (1h): Gemini Adapter 및 OpenAI Adapter 구현 — 컴파일된 `CompiledPrompt`를 각 공급자 SDK(Gemini 및 OpenAI) 형식에 맞는 호출 인자 규격으로 치환하는 어댑터들 개발 및 어댑터 유닛 테스트 작성."

## Clarifications

### Session 2026-08-11

- Q: How should adapters handle section ordering conflicts or duplicate order values? → A: Sort by ascending `order` and reject duplicate `order` values.
- Q: How should Gemini conversion represent multiple system sections? → A: Join them in ascending `order` with exactly `\n\n` into one `system_instruction` string.
- Q: What final argument structure should Gemini conversion return? → A: Return call-ready plain data with `contents` and nested `config.system_instruction`.
- Q: What should Gemini conversion return when there is no system section? → A: Omit `config` entirely and return only `contents`.
- Q: How should Gemini conversion handle a prompt containing only system sections? → A: Return only `config.system_instruction`, emit one WARNING without compiled prompt text, and leave call viability to the caller.
- Q: Through which channel should the system-only WARNING be emitted? → A: Record it exactly once at WARNING level through the standard logger, without emitting a runtime warning.
- Q: Which source identifiers should the system-only WARNING include? → A: Include source `slug`, `version`, and `label`, but no compiled prompt text.
- Q: Which `google-genai` dictionary shape should each Gemini conversation content use? → A: Use `{"role": "user"|"model", "parts": [{"text": "..."}]}` for every section.
- Q: Which official OpenAI input API should the adapter support? → A: Support both Chat Completions `messages` and Responses API `input`/`instructions` formats.
- Q: How should callers select between the two OpenAI formats? → A: One `OpenAIAdapter` exposes separate Chat Completions and Responses conversion methods.
- Q: How should Responses conversion represent multiple system sections? → A: Join them in ascending `order` with exactly `\n\n` into one `instructions` string.
- Q: How should all adapters handle system-only prompts? → A: Return the provider-specific system-only arguments, emit the same standard WARNING, and leave call viability to the caller.
- Q: Which dictionary shape should each Responses conversation `input` item use? → A: Use `{"role": "user"|"assistant", "content": "..."}` for every conversation section.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare a compiled prompt for Gemini (Priority: P1)

An application developer converts a provider-neutral compiled prompt into Gemini-compatible invocation arguments, allowing the application to use its selected provider without reconstructing prompt roles or message ordering.

**Why this priority**: Gemini conversion is one of the two core deliverables and proves that a compiled prompt can cross the provider boundary without provider logic entering the registry or compilation process.

**Independent Test**: Given compiled prompts containing system, user, and assistant sections, a developer can convert each prompt and verify that system instructions, conversation contents, roles, text, and ordering are represented in the Gemini-compatible result without any provider call.

**Acceptance Scenarios**:

1. **Given** a compiled prompt contains one system section followed by user and assistant sections, **When** a developer converts it for Gemini, **Then** the system text appears under `config.system_instruction` and each remaining section appears under `contents` as `{"role": "user"|"model", "parts": [{"text": "..."}]}` in resolved order.
2. **Given** a compiled prompt contains multiple system sections interleaved with conversation sections, **When** it is converted for Gemini, **Then** their exact texts are joined in ascending section order with `\n\n` into one system-instruction string and excluded from conversation contents, while all non-system sections retain their resolved order.
3. **Given** a compiled prompt contains an assistant section, **When** it is converted for Gemini, **Then** the section is represented using Gemini's provider-facing model role without changing its text.

---

### User Story 2 - Prepare a compiled prompt for either OpenAI API (Priority: P1)

An application developer converts the same provider-neutral compiled prompt into either Chat Completions or Responses API invocation arguments, preserving prompt intent without writing API-specific mapping code.

**Why this priority**: OpenAI conversion is the second core deliverable and must provide equivalent coverage so applications can switch providers at the conversion boundary.

**Independent Test**: Given compiled prompts containing system, user, and assistant sections, a developer can call the corresponding method on one OpenAI adapter and verify exact Chat Completions `messages` or Responses API `input`/`instructions` arguments without making an OpenAI request.

**Acceptance Scenarios**:

1. **Given** a compiled prompt contains system, user, and assistant sections, **When** a developer converts it for OpenAI Chat Completions, **Then** the result contains ordered `messages` with corresponding roles and unchanged text.
2. **Given** the same compiled prompt, **When** a developer converts it for the OpenAI Responses API, **Then** system texts are joined in ascending section order with exactly `\n\n` under one `instructions` string and each remaining section is represented under `input` as `{"role": "user"|"assistant", "content": "..."}` with unchanged text.
3. **Given** repeated or consecutive sections use the same conversation role, **When** the prompt is converted for either OpenAI target, **Then** each section remains a distinct input item in ascending section order.

---

### User Story 3 - Detect prompts that cannot be converted safely (Priority: P2)

An application developer receives a clear local failure when a compiled prompt contains an unsupported or ambiguous role, rather than receiving invocation arguments whose meaning has silently changed.

**Why this priority**: Explicit failure protects prompt intent and makes provider integration problems diagnosable before an application attempts an external request.

**Independent Test**: A compiled prompt containing an unsupported or blank role is converted with either adapter and produces an actionable failure with no partial invocation arguments.

**Acceptance Scenarios**:

1. **Given** a compiled prompt contains a section with a role outside system, user, and assistant, **When** either adapter attempts conversion, **Then** conversion fails locally, identifies the unsupported role, and returns no partial arguments.
2. **Given** a compiled prompt has no role sections but has aggregate compiled content, **When** either adapter converts it, **Then** the content is represented as one user message so a valid Day 11 compilation remains usable.
3. **Given** a valid compiled prompt, **When** either adapter converts it, **Then** the source object remains unchanged and no network request is made.
4. **Given** a compiled prompt contains only system sections, **When** it is converted for any supported target, **Then** the result preserves only that target's system arguments, records exactly one standard WARNING containing source slug, version, and label but no compiled prompt text, and leaves the caller responsible for deciding whether to invoke the provider.

### Edge Cases

- A compiled prompt has no sections; its aggregate content becomes a single user message or content block.
- A compiled prompt contains only system sections; Gemini returns only `config.system_instruction`, Chat Completions returns ordered system `messages`, and Responses returns only `instructions`; each records exactly one standard WARNING with source slug, version, and label but no compiled prompt text, and provider-call viability remains the caller's responsibility.
- A compiled prompt contains conversation sections but no system section; Gemini conversion omits the `config` key entirely.
- Multiple system sections occur before, after, or between conversation sections; their exact texts are joined in ascending section order with `\n\n` into one system-instruction string without disturbing the resolved order of conversation sections.
- Responses conversion applies the same ascending-order and `\n\n` joining rule to produce one `instructions` string from multiple system sections.
- Consecutive user or assistant sections remain separate ordered items rather than being silently merged.
- Sections supplied out of sequence are converted in ascending `order`; duplicate `order` values cause conversion to fail without partial arguments.
- A section contains empty text or Unicode text; conversion preserves the text exactly and leaves provider-side content acceptance to the caller and provider.
- A section has a blank, differently cased, or unknown role; conversion rejects it rather than guessing its meaning.
- Source traceability fields such as slug, version, and label are not inserted into provider prompt content or invocation arguments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The SDK MUST provide a documented Gemini conversion operation and one documented `OpenAIAdapter` exposing separate Chat Completions and Responses API conversion methods, each accepting a completed provider-neutral prompt.
- **FR-002**: Each conversion operation MUST return provider-compatible invocation arguments composed only of core data values, MUST NOT construct provider SDK objects, and MUST NOT initiate an external provider request.
- **FR-003**: For prompts with conversation sections, Gemini conversion MUST return call-ready `google-genai` dictionary arguments with one `{"role": "user"|"model", "parts": [{"text": "..."}]}` item per section under `contents`; when system sections exist, it MUST include one string under `config.system_instruction`, joining multiple system sections in ascending `order` with exactly `\n\n`, and when none exist, it MUST omit `config` entirely.
- **FR-004**: Gemini conversion MUST map a provider-neutral user role to `user`, MUST map an assistant role to `model`, and MUST preserve each section as one text part without changing its text.
- **FR-005**: OpenAI Chat Completions conversion MUST return ordered `messages` containing one role/content item per source section, while Responses API conversion MUST join system sections in ascending `order` with exactly `\n\n` under one `instructions` string and return one `{"role": "user"|"assistant", "content": "..."}` item per conversation section under `input`; both targets MUST preserve applicable roles, text, and resolved order.
- **FR-006**: All three conversion operations (Gemini, OpenAI Chat Completions, and OpenAI Responses) MUST sort sections by ascending `order`, MUST reject duplicate `order` values with no partial result, and MUST preserve that resolved order in all applicable provider arguments.
- **FR-007**: When a compiled prompt contains no sections, all three conversion operations MUST use its aggregate content as one user-role input.
- **FR-008**: All three conversion operations MUST reject blank or unsupported section roles with an actionable local failure and MUST NOT return partial invocation arguments.
- **FR-009**: When any conversion receives only system sections, it MUST preserve them in the target's system-only arguments, MUST record exactly one standard log at WARNING level containing source `slug`, `version`, and `label` but no compiled prompt text, MUST NOT emit a runtime warning or error, and MUST leave provider-call viability to the caller; Gemini MUST return only `config.system_instruction`, Chat Completions MUST return ordered system `messages`, and Responses MUST return only `instructions`.
- **FR-010**: Conversion MUST NOT mutate the completed prompt, re-render template variables, add source metadata to provider prompt content, or infer model and generation settings.
- **FR-011**: Conversion MUST preserve empty strings, whitespace, line breaks, Unicode characters, and other already-compiled text exactly.
- **FR-012**: The public adapter behavior MUST be covered by isolated automated tests for each provider and each OpenAI adapter method, including all supported roles, exact Gemini role/parts/text dictionary shape, exact OpenAI Chat Completions role/content messages, exact Responses instructions and role/content input items, method-specific return contracts, role ordering, repeated roles, multiple system sections and separator behavior, sectionless fallback, provider-specific system-only output, one standard WARNING with source identifiers and prompt-text exclusion, absence of runtime warnings or errors, text fidelity, unsupported roles, immutability, and absence of provider calls.
- **FR-013**: The adapter feature MUST remain usable as part of the independently installable core SDK and MUST NOT require the Prompt Server or a Django integration at conversion time.

### Key Entities *(include if feature involves data)*

- **Compiled prompt**: Provider-neutral, locally rendered prompt content with ordered role sections and source traceability metadata.
- **Compiled prompt section**: One unit of rendered text associated with a provider-neutral system, user, or assistant role and a unique non-negative `order` value within its compiled prompt.
- **Gemini invocation arguments**: `google-genai`-compatible core data normally containing ordered `contents` items shaped as role plus a single text part and, when present, a nested `config.system_instruction` string; multiple source system sections use the defined `\n\n` separator, while the documented system-only exception contains only `config.system_instruction`.
- **OpenAI Chat Completions invocation arguments**: Core data containing the converted ordered `messages` collection.
- **OpenAI Responses invocation arguments**: Core data containing optional system `instructions` and an ordered `input` collection of user/assistant role plus string content items.
- **OpenAI adapter**: One public conversion boundary with separate, explicitly named methods for producing the two OpenAI invocation-argument entities.
- **Adapter conversion failure**: A local, actionable outcome indicating that the prompt cannot be mapped without changing its meaning.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across the supported-role test matrix, 100% of source section text and applicable ordering is preserved in all three target-specific results.
- **SC-002**: In all unsupported-role scenarios, 100% of conversions fail before producing partial invocation arguments and identify the offending role.
- **SC-003**: A developer can convert the same valid compiled prompt for Gemini, OpenAI Chat Completions, or the OpenAI Responses API through a documented public operation without manually reshaping its content.
- **SC-004**: Automated isolated tests cover 100% of the conversion paths and edge-case categories listed in FR-012, with no external provider request required.
- **SC-005**: In the project test environment, each of the three public conversion methods converts a valid compiled prompt containing 200 ordered sections in under one second when timed individually with `time.perf_counter()`.
- **SC-006**: In 100% of system-only test scenarios across all supported targets, conversion returns the provider-specific system arguments, records exactly one standard WARNING containing source slug, version, and label but no compiled prompt text, emits no runtime warning or error, and makes no provider request.

## Assumptions

- The completed prompt contract from Day 11 is the sole adapter input; retrieval, validation, variable rendering, and prompt authoring are already complete before conversion begins.
- The provider-neutral roles supported in this increment are exactly `system`, `user`, and `assistant`; additional provider roles, multimodal parts, tool calls, and function messages are outside scope.
- Gemini conversion deliberately flattens multiple ordered system sections into one string using `\n\n`; preserving system-section boundaries as a list is outside scope.
- Responses API conversion uses the same `\n\n` system-section separator as Gemini for cross-provider consistency.
- When no sections exist, aggregate compiled content represents a user request and is therefore converted as one user-role input.
- A caller receiving system-only arguments from any adapter method is responsible for deciding whether and how to supply conversation content before invoking the provider.
- Source slug, version, and label are intentionally considered safe operational identifiers for the unified system-only WARNING; rendered system and conversation text remain prohibited from logs.
- Provider model selection, credentials, temperature, token limits, safety controls, tools, streaming, request execution, retries, response parsing, and usage tracking remain the application developer's responsibility.
- Supporting both OpenAI targets covers text prompt conversion only; Responses API state, built-in tools, reasoning items, and response handling remain outside scope.
- Provider source metadata is retained on the original compiled prompt for application-side traceability but is not part of provider invocation arguments.
- Adapter conversion is deterministic and local, returns only core data values suitable for keyword-argument expansion, and does not require either provider SDK to be installed merely to reshape prompt data.
- Gemini compatibility targets the current `google-genai` package's dictionary input contract rather than its provider-native model classes.
