# Research: Playground Compilation and Gemini E2E Example

## Playground request boundary

**Decision**: Extend the existing `DashboardPlaygroundView` and URL with a normal HTML POST. Preserve `LoginRequiredMixin` and `DashboardStaffRequiredMixin`, rely on Django's standard CSRF middleware/token, and return the same template with submitted values plus either preview or errors.

**Rationale**: The feature already has one version-scoped page and explicitly rejects a separate internal API or browser compiler. A same-resource GET/POST flow retains the selected version, uses established session authorization, and lets Django auto-escape submitted and compiled text.

**Alternatives considered**:

- A new JSON compilation endpoint: rejected by clarification and because it expands the exposed surface without user value.
- Browser-side rendering: rejected because it would duplicate the strict SDK compiler and drift from its validation contract.
- Redirect-after-POST: rejected because transient input, field errors, and compiled output must be shown without persistence.

## Browser-string conversion and SDK validation

**Decision**: Build a request-scoped Django form from the selected version's declarations. Prefix generated field names, retain string whitespace, parse numbers into strict `int`/finite `float`, booleans into `bool`, and JSON into object/array values. Omit blank optional values so SDK defaults and missing-value rules remain authoritative. After form cleaning, call the public SDK compiler and translate only expected PromptKit exceptions into safe non-field or field errors.

**Rationale**: Browser controls submit strings while `compile()` deliberately accepts strict typed values. Django forms are the existing framework boundary for CSRF-safe validation; the SDK remains the sole authority for declaration/template consistency and final compilation.

**Alternatives considered**:

- Pass raw strings to `compile()`: rejected because number, boolean, and JSON inputs would violate the strict public contract.
- Reimplement compiler validation in the form: rejected because duplicate rules would drift and could produce a preview the SDK rejects.
- Coerce types inside the core compiler: rejected because it would weaken the framework-agnostic public API for one dashboard transport.

## ORM-to-SDK mapping

**Decision**: Add one dashboard service that eagerly loads the selected `Version` with prompt/category, ordered variables, and ordered sections; maps it to the public `RetrievedPrompt` model; and invokes `compile()` once. Playground source label is `None` because navigation identifies an explicit version rather than a label resolution.

**Rationale**: Draft versions are intentionally unavailable through the read-only registry API, yet staff may preview drafts. Mapping the selected snapshot into the same public SDK model reuses compilation without an internal HTTP round trip or fallback resolution.

**Alternatives considered**:

- Fetch the prompt back through `PromptKitClient`: rejected because draft preview would be impossible and the selected version could be replaced by on-live resolution.
- Import private compiler helpers: rejected because it bypasses the public `RetrievedPrompt.compile()` contract.
- Add compilation methods to ORM models: rejected because it couples persistence entities directly to SDK behavior.

## Error, output, and persistence policy

**Decision**: Successful POST returns ordered compiled sections and aggregate content in an auto-escaped, whitespace-preserving result region. Expected input/template failures return no partial preview and preserve safe submitted values. The request performs no model save, messages containing values, or prompt-text logging.

**Rationale**: This satisfies the zero-write/zero-provider-call contract and prevents secrets or rendered prompt content from leaking through logs. Django template auto-escaping protects the HTML boundary without marking content safe.

**Alternatives considered**:

- Log full compiler exceptions with parameters: rejected because exceptions and input can contain sensitive business context.
- Persist preview sessions: rejected by scope and because it creates a new data lifecycle.
- Show partially rendered sections: rejected because users could mistake invalid content for a valid prompt.

## Gemini client and dependency isolation

**Decision**: Use the official `google-genai` distribution at `>=2.18.1,<3` only in `examples/gemini-e2e/pyproject.toml`. Use the synchronous context-managed client and existing `GeminiAdapter.to_generate_content_args()` dictionary output. Keep the model configurable rather than embedding a model name as a behavioral guarantee.

**Rationale**: PyPI reports `google-genai` 2.18.1 (released 2026-08-13), Python `>=3.10`, and Apache-2.0. The official package documentation supports dictionary arguments and recommends pinning below 3.0.0 to avoid upcoming breaking behavior. A context manager closes HTTP resources. Sources: [PyPI metadata](https://pypi.org/pypi/google-genai/json), [official SDK documentation](https://googleapis.github.io/python-genai/).

**Alternatives considered**:

- Legacy `google-generativeai`: rejected because current Google documentation directs Python consumers to `google-genai`.
- Core SDK optional extra or runtime dependency: rejected by clarification and the constitutional lightweight adapter boundary.
- Unbounded latest dependency: rejected because the official package metadata warns of a breaking next major version.

## Example execution and live-call guard

**Decision**: The example validates environment configuration, retrieves and compiles before importing/constructing the provider client, prints stage names and safe source identifiers, and requires `--live` before exactly one `generate_content` call. Without `--live`, it exits successfully after explaining the live command and performs zero Gemini calls.

**Rationale**: The guard prevents accidental cost and data transmission while leaving the real E2E journey directly runnable. Delaying provider construction ensures registry or compile failures cannot trigger a provider request and lets automated tests run without credentials or provider network access.

**Alternatives considered**:

- Call whenever a Gemini key is present: rejected because ambient credentials must not imply consent to cost or data transfer.
- Interactive confirmation: rejected because it is harder to automate and less explicit in CI/shell history.
- Automatic retries: rejected because they could violate the exactly-one-call contract and obscure cost.

## Automated versus live validation

**Decision**: Django preview tests use `django.test.TestCase` and `setUpTestData`. Example orchestration tests inject or patch registry and Gemini boundaries, assert call counts and safe outputs, and never require `google-genai` or live secrets in the root test environment. The documented live smoke check is manual/opt-in.

**Rationale**: The project constitution requires database-backed dashboard tests to use `TestCase`, while external calls must remain deterministic and free in default validation. Explicit live verification proves integration without making CI depend on quota or network availability.

**Alternatives considered**:

- Run live Gemini in the default suite: rejected because it is non-deterministic, costly, and secret-dependent.
- Test only the happy path manually: rejected because flag, error boundary, call count, and redaction regressions require repeatable coverage.
