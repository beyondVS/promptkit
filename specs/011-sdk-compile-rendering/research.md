# Research: SDK Local Prompt Compilation

## Decision: Use a constrained native placeholder parser

- **Decision**: Accept only `{{ identifier }}` placeholders, where an identifier begins with a letter or underscore and continues with letters, numbers, or underscores. Scan each template fully and reject unclosed, orphaned, or expression-like delimiters before rendering.
- **Rationale**: Existing registry content and SDK requirements use that exact Jinja2-style notation. A native constrained parser prevents template expressions, attribute access, filters, and control structures from expanding the execution or security surface.
- **Alternatives considered**: Adding Jinja2 was rejected because it is not an existing SDK dependency and supports far more behavior than the feature requires. Regex replacement alone was rejected because it can leave malformed or unsupported syntax unresolved.

## Decision: Compile from `RetrievedPrompt`

- **Decision**: Add `RetrievedPrompt.compile(params: Mapping[str, object] | None = None) -> CompiledPrompt`.
- **Rationale**: The retrieved model already owns the template text, sections, declared variables, slug, version, and label. The result is directly traceable to the fetched version without a second public entry point.
- **Alternatives considered**: A client-level method duplicates prompt data ownership. A standalone public function is less discoverable and adds an unnecessary API shape.

## Decision: Build a Pydantic v2 runtime validation model from declarations

- **Decision**: Build one Pydantic v2 model per compilation with forbidden extra fields and strict declared types: string, numeric (excluding booleans), boolean, and JSON object/array.
- **Rationale**: It validates the complete caller input set against the registry declaration and makes undeclared values a deterministic failure. Strict caller input avoids implicit conversion that could alter prompt meaning.
- **Alternatives considered**: Per-field ad hoc validation duplicates rules and weakens error consistency. Permissive Pydantic conversion was rejected because values such as text representations of booleans or numbers should not silently change type.

## Decision: Normalize defaults before the same validation pass

- **Decision**: When a caller omits a variable with a registry default, parse the stored default according to its declared type, then pass it through the same validation model; a valid caller value takes precedence.
- **Rationale**: Registry defaults are transported as strings or null and must be made type-safe before use. One validation path avoids trusting malformed remote data.
- **Alternatives considered**: Treating defaults as raw text bypasses declared types. Requiring callers to restate defaults contradicts the variable contract.

## Decision: One-pass rendering and typed public errors

- **Decision**: Render only validated values in a single pass. Add typed SDK errors for missing variables, invalid variable type/default, unexpected values, and invalid template structure or declaration consistency; do not expose raw inputs in messages.
- **Rationale**: One pass prevents caller content containing placeholder-looking text from executing as a second template. Typed SDK errors preserve the existing public exception style and make failures testable.
- **Alternatives considered**: Recursive rendering is unsafe and violates the specification. Exposing Pydantic's raw exception is unstable and may disclose supplied values.

## Decision: Preserve renderable sections in the result

- **Decision**: `CompiledPrompt` carries source slug, version, selected label, rendered aggregate content, and ordered rendered sections.
- **Rationale**: Source traceability is required now, and preserving sections lets a later adapter map roles without re-parsing the template.
- **Alternatives considered**: Returning only a text string loses version identity. Deferring sections forces later adapters to duplicate compilation logic.
