# SDK Public Contract: Provider Prompt Adapters

## Public surface

```python
from promptkit import GeminiAdapter, OpenAIAdapter

gemini_args = GeminiAdapter.to_generate_content_args(compiled)
chat_args = OpenAIAdapter.to_chat_completions_args(compiled)
responses_args = OpenAIAdapter.to_responses_args(compiled)
```

All methods accept one immutable `CompiledPrompt`, perform no I/O, and return a new plain Python
dictionary. They do not accept or infer a model, client, credentials, generation settings, tools,
streaming behavior, or retry behavior.

The public return annotations are provider-specific `TypedDict` contracts composed only of core
values. The SDK exports the adapters, return contract types, and `AdapterConversionError` from the
top-level `promptkit` package.

## Gemini `generate_content` arguments

For resolved system, user, and assistant sections:

```python
{
    "contents": [
        {"role": "user", "parts": [{"text": "Question"}]},
        {"role": "model", "parts": [{"text": "Prior answer"}]},
    ],
    "config": {"system_instruction": "Policy one\n\nPolicy two"},
}
```

- `system` sections are excluded from `contents` and joined with exactly `\n\n`.
- `user` maps to `user`; `assistant` maps to `model`.
- Each conversation section remains one content containing one text part.
- Without system sections, `config` is omitted.
- With only system sections, `contents` is omitted.

The caller supplies the model separately, for example by expanding this mapping into the official
Google Gen AI SDK call. PromptKit does not import or call that SDK.

## OpenAI Chat Completions arguments

```python
{
    "messages": [
        {"role": "system", "content": "Policy"},
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Prior answer"},
    ]
}
```

All supported sections remain distinct messages in ascending order. System-only input returns a
`messages` list containing only the ordered system messages.

## OpenAI Responses arguments

```python
{
    "instructions": "Policy one\n\nPolicy two",
    "input": [
        {"role": "user", "content": "Question"},
        {"role": "assistant", "content": "Prior answer"},
    ],
}
```

- System sections are joined with exactly `\n\n` under `instructions` and excluded from `input`.
- User and assistant sections remain distinct ordered input items.
- Without system sections, `instructions` is omitted.
- With only system sections, `input` is omitted.

## Shared ordering and fallback contract

- Section `order` is authoritative; input tuples may be unordered and are sorted ascending.
- Duplicate order values raise `AdapterConversionError` before any result is returned.
- Exact case-sensitive roles are `system`, `user`, and `assistant`; all others raise
  `AdapterConversionError` without a partial result.
- When there are no sections, aggregate `CompiledPrompt.content` becomes one exact user item.
- Empty, whitespace-only, multiline, and Unicode content is never normalized.
- Source `slug`, `version`, and `label` never appear in provider arguments.

## System-only warning contract

Each conversion of a prompt whose resolved sections are all `system`:

- returns the target-specific system-only mapping described above;
- writes exactly one record at WARNING through the adapter module's standard logger;
- includes source slug, version, and label in that record;
- excludes aggregate content, section content, and converted arguments;
- emits no runtime warning and raises no error solely because the prompt is system-only.

The caller decides whether those system-only arguments are viable for a provider invocation.

## Error and side-effect contract

`AdapterConversionError` is the only new expected conversion failure type. No failure returns a
partial mapping. Successful and failed conversions do not mutate `CompiledPrompt`, render
variables, access the network, create provider clients, or invoke provider methods.
