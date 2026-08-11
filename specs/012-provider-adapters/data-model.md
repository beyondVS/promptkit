# Data Model: Gemini and OpenAI Prompt Adapters

This feature adds no persistence and no mutable lifecycle. It transforms one existing immutable
input entity into one newly allocated provider argument mapping or raises a local typed error.

## Existing Input: Compiled Prompt

| Field | Type | Adapter rule |
|---|---|---|
| `slug` | non-empty string | Used only in the system-only WARNING. Never inserted into provider arguments. |
| `version` | positive integer | Used only in the system-only WARNING. |
| `label` | string or null | Used only in the system-only WARNING. Null remains an explicit logged identifier value. |
| `content` | string | Used unchanged as one synthetic user turn only when `sections` is empty. |
| `sections` | immutable tuple of compiled sections | Copied, validated, sorted, and mapped without mutation. |

## Existing Input: Compiled Prompt Section

| Field | Type | Validation / transformation |
|---|---|---|
| `role` | string | Must exactly equal `system`, `user`, or `assistant`. Blank, differently cased, and unknown values fail. |
| `order` | non-negative integer | Must be unique within the prompt. Sections are resolved in ascending order. |
| `content` | string | Preserved byte-for-byte as a Python string, including empty text, whitespace, line breaks, and Unicode. |

When `sections` is empty, normalization creates an internal user-role view of aggregate `content`.
This fallback is not written back to the source model.

## Gemini Invocation Arguments

The output is a plain dictionary accepted as the non-model keyword arguments of
`client.models.generate_content`.

| Key | Presence | Value |
|---|---|---|
| `contents` | Present when at least one user/assistant section exists | Ordered list of Gemini content dictionaries. |
| `config` | Present when at least one system section exists | Dictionary containing only `system_instruction` in this feature. |

Each conversation content contains `role` (`user` or `model`) and `parts`, a one-element list
containing `{"text": exact_content}`. All ordered system contents are joined with exactly `\n\n`.
For a system-only prompt, `contents` is omitted and only `config.system_instruction` remains.

## OpenAI Chat Completions Invocation Arguments

The output contains exactly one `messages` list. Every resolved source section remains a distinct
dictionary with its original supported role and exact string `content`. A sectionless prompt
produces one user message. A system-only prompt contains only ordered system messages.

## OpenAI Responses Invocation Arguments

| Key | Presence | Value |
|---|---|---|
| `instructions` | Present when at least one system section exists | Exact system contents joined in resolved order with `\n\n`. |
| `input` | Present when at least one user/assistant section exists | Ordered list of distinct role/content dictionaries. |

System items are excluded from `input`. A system-only prompt returns only `instructions`; a prompt
without system sections omits `instructions`.

## Adapter Conversion Failure

`AdapterConversionError` is a public `PromptKitError` subclass. It is raised before a provider
mapping is returned when any section role is unsupported/blank or any two sections share an
`order`. Its message identifies the invalid role or duplicate order and excludes compiled text.

## Conversion Flow

1. Copy sections, or create the internal aggregate-content fallback when none exist.
2. Validate all roles and order uniqueness before producing a public output.
3. Sort the copied normalized sections by ascending `order`.
4. Detect system-only input and emit one safe standard WARNING when applicable.
5. Map the entire normalized sequence to the selected provider contract and return a fresh dict.

There are no state transitions after return. Repeating a conversion with the same input and target
produces equal arguments; logging occurs once per system-only conversion invocation.
