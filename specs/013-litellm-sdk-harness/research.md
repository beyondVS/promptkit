# Research: LiteLLM Adapter and SDK Harness

## Decision: Return only LiteLLM `messages` arguments

**Rationale**: LiteLLM's completion interface takes a caller-selected `model` and ordered `messages` role/content values. PromptKit owns only provider-neutral prompt conversion; omitting the model and all execution settings preserves the project rule that the SDK never calls LLMs or selects models. The adapter can therefore remain dependency-free and return a plain dictionary.

**Alternatives considered**:

- Include a model field or model default: rejected because a prompt registry does not own model selection and the spec expressly assigns it to the caller.
- Import LiteLLM and return its SDK model types: rejected because conversion must be usable without a provider dependency or provider call.
- Expose a generic OpenAI adapter alias instead of a LiteLLM adapter: rejected because the feature requires an explicit, discoverable LiteLLM public boundary and contract.

## Decision: Reuse the existing shared section-resolution policy

**Rationale**: `_resolve_sections()` already validates the three provider-neutral roles, detects duplicate orders, applies ascending order, and supplies the aggregate-content fallback. Calling it from the new adapter guarantees LiteLLM follows the tested semantics of Gemini and OpenAI without duplicating policy.

**Alternatives considered**:

- Reimplement validation inside LiteLLM conversion: rejected because two independent policies can drift and produce inconsistent failures.
- Preserve original tuple order: rejected because the existing public adapter contract resolves section order numerically.

## Decision: Preserve each system section as an ordered LiteLLM message

**Rationale**: LiteLLM accepts OpenAI-style chat messages and supports the `system`, `user`, and `assistant` roles used by the compiled prompt. Unlike Gemini and OpenAI Responses conversions, its message contract does not require PromptKit to merge system text. The result keeps every section boundary and ordering intact. A system-only prompt retains the shared safe warning policy.

**Alternatives considered**:

- Merge system sections: rejected because it changes section boundaries without a LiteLLM contract requirement.
- Disallow system-only prompts: rejected because all existing adapters return their target-specific system representation and leave call viability to the caller.

## Decision: Use an explicit two-way public-export coverage map in one integration test module

**Rationale**: `promptkit.__all__` is the declared public inventory. A test-local map from each export to an assertion identifier can compare set equality in both directions, making additions and stale mappings actionable while exercising the package through root imports. It gives a stable meaning to the feature's 100% API-harness requirement without requiring private line coverage.

**Alternatives considered**:

- Rely on test coverage reporting: rejected because line coverage cannot prove all declared exports were intentionally covered.
- Infer coverage by introspecting test functions: rejected because implicit naming conventions are fragile and produce unclear failures.
- Add runtime registration to the SDK: rejected because test coverage metadata is not production behavior.

## Decision: Keep all integration boundaries local and controlled

**Rationale**: `httpx.MockTransport` already lets the SDK client perform its normal request and response handling without a network connection. The full journey can retrieve a fixed payload, compile caller values, and pass the resulting immutable object to Gemini, OpenAI, and LiteLLM adapters. This verifies component composition while respecting security and read-only constraints.

**Alternatives considered**:

- Contact a running Prompt Server: rejected because it makes the harness environment-dependent and does not improve public-contract coverage.
- Call LiteLLM: rejected because PromptKit must not invoke providers and this feature needs no provider credential.
