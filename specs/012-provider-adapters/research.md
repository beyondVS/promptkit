# Research: Gemini and OpenAI Prompt Adapters

Research was verified on 2026-08-11 against the official
[Google Gen AI SDK documentation](https://googleapis.github.io/python-genai/) and
[OpenAI Responses migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses).

## Decision: Return plain provider keyword-argument dictionaries

- **Decision**: Each public conversion returns a newly allocated, precisely typed plain Python
  dictionary intended for keyword expansion into the corresponding provider method.
- **Rationale**: The Google SDK documents dictionary parameter support alongside Pydantic types,
  and the OpenAI Python SDK accepts dictionary-shaped message/input values. Plain core values keep
  `packages/promptkit` independently installable and allow contract tests without either provider
  package.
- **Alternatives considered**: Constructing provider SDK objects was rejected because it creates
  optional-dependency and version-coupling problems. Returning JSON text was rejected because the
  caller would need to deserialize it before an SDK call.

## Decision: Expose stateless provider classes with target-specific methods

- **Decision**: Add `GeminiAdapter.to_generate_content_args(compiled)` and one `OpenAIAdapter`
  exposing `to_chat_completions_args(compiled)` and `to_responses_args(compiled)` as static methods.
- **Rationale**: Method names identify the exact invocation target and make it clear that the
  result is an argument mapping, not a provider response. Static methods reflect that conversion
  owns no credentials, client, model, settings, or state.
- **Alternatives considered**: One OpenAI method with a format flag was rejected because it makes
  return typing conditional and permits invalid selector values. Top-level functions were viable
  but less discoverable as provider adapters. Stateful instances would imply configuration that
  is explicitly out of scope.

## Decision: Match the current `google-genai` content and config contract

- **Decision**: Return `contents` items shaped as
  `{"role": "user"|"model", "parts": [{"text": text}]}`. Map `assistant` to `model`.
  When system sections exist, join their exact text with `\n\n` under
  `config.system_instruction`; omit `config` when no system section exists.
- **Rationale**: Google documents `Content` as a role plus parts, restricts conversational roles
  to `user` and `model`, accepts dictionaries for API parameters, and places system guidance in
  the `generate_content` config. This shape also preserves every source conversation section as
  one content item rather than relying on SDK shorthand that can merge inputs.
- **Alternatives considered**: SDK-native `types.Content` and `GenerateContentConfig` were rejected
  to avoid the dependency. Converting assistant text to a user turn or merging consecutive turns
  was rejected because it changes intent or section identity.

## Decision: Support both OpenAI targets through explicit contracts

- **Decision**: Chat Completions returns ordered `messages` with unchanged
  `system`/`user`/`assistant` roles and string `content`. Responses returns conversation sections
  as ordered `input` items with `user`/`assistant` roles and string `content`, while joined system
  text is placed in top-level `instructions`.
- **Rationale**: Official OpenAI documentation says Chat Completions remains supported, while
  Responses is recommended for new projects. It maps Chat `messages` to Responses `input` items
  and supports top-level `instructions` for system guidance. Separate methods make both stable
  choices available without conflating their return shapes.
- **Alternatives considered**: Supporting only Responses was rejected by the clarified feature
  scope. Passing system sections as Responses input items is compatible but was rejected because
  the selected contract explicitly centralizes them in `instructions`.

## Decision: Normalize once, then map without mutation

- **Decision**: A private helper copies and sorts sections by ascending `order`, detects duplicate
  values, validates exact case-sensitive roles (`system`, `user`, `assistant`), and replaces an
  empty section tuple with one synthetic user section containing aggregate `content`.
- **Rationale**: One validation path keeps all three public methods behaviorally aligned. Sorting a
  copied list leaves the frozen `CompiledPrompt` unchanged, and validation before provider mapping
  prevents a partial result from escaping.
- **Alternatives considered**: Trusting source order was rejected because the specification makes
  `order` authoritative. Role normalization such as trimming or lowercasing was rejected because
  it guesses intent. Adding stricter text validation was rejected because empty, whitespace, and
  Unicode text must be preserved.

## Decision: Use one public conversion error

- **Decision**: Add `AdapterConversionError(PromptKitError)` for duplicate order values and blank
  or unsupported roles. Messages identify the offending order or role but never section content.
- **Rationale**: Both failures mean the completed prompt cannot be mapped without ambiguity. One
  typed public category is sufficient for caller handling while actionable messages retain the
  diagnostic detail.
- **Alternatives considered**: Raw `ValueError` would be inconsistent with the SDK error hierarchy.
  One subclass per invariant would expand a small public surface without a distinct recovery path.

## Decision: Centralize the system-only operational warning

- **Decision**: After successful normalization, each public conversion detects that every section
  is `system` and calls one shared logger helper exactly once at WARNING. The structured message
  includes source `slug`, `version`, and `label`, but no aggregate or section content. It emits no
  `warnings.warn` and still returns the provider-specific system-only mapping.
- **Rationale**: This implements the same observable policy across all targets while keeping call
  viability with the application. A shared helper prevents inconsistent severity or accidental
  prompt disclosure.
- **Alternatives considered**: Raising an error or injecting a synthetic user message contradicts
  the clarified policy. A runtime warning adds a second warning channel. Logging entire arguments
  risks exposing compiled prompt text.

## Decision: Test contracts without provider SDKs or network access

- **Decision**: Unit tests instantiate frozen `CompiledPrompt` fixtures directly, assert exact
  dictionary equality, use `assertLogs` and `warnings.catch_warnings`, compare source model dumps
  before/after, and time 200-section conversions. Tests do not install, import, or mock provider
  clients.
- **Rationale**: The feature is a pure conversion boundary. Exact output assertions prove SDK
  compatibility at the owned boundary, while absence of provider dependencies and calls is
  inherent and mechanically inspectable.
- **Alternatives considered**: Live API tests require credentials, cost, and network and would test
  provider behavior outside the feature. Provider-object construction tests would violate the
  dependency decision.
