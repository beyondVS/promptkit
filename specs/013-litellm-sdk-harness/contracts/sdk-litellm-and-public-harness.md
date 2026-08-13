# SDK Contract: LiteLLM Conversion and Public Harness

## Public import contract

The following additions are importable from `promptkit`:

- `LiteLLMAdapter`
- `LiteLLMChatMessage`
- `LiteLLMCompletionArgs`

`AdapterConversionError` remains the public failure type for invalid compiled section roles or duplicate section order values.

## LiteLLM conversion contract

`LiteLLMAdapter.to_completion_args(compiled_prompt)` returns plain call keyword arguments:

```python
{
    "messages": [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
    ]
}
```

Rules:

1. Input sections are validated and sorted by ascending `order`.
2. Each section becomes exactly one message with the same allowed role and exactly the same text.
3. Repeated roles remain separate messages.
4. An empty section tuple produces exactly one `{"role": "user", "content": compiled.content}` message.
5. Duplicate orders or a role other than `system`, `user`, or `assistant` raise `AdapterConversionError` before a result is returned.
6. A system-only input returns ordered system messages and emits one existing safe WARNING that includes only source slug, version, and label.
7. The operation does not mutate input, re-render values, import LiteLLM, select a model, include credentials or settings, or invoke any provider.

## Public-harness contract

The integration harness is a pytest test module. It must:

1. Import all public symbols through `promptkit`, never internal-only paths for public assertions.
2. Assert equality between the package-root `__all__` set and the coverage-map key set.
3. Include at least one explicit assertion for each public export; type-only argument contracts are proved by root import plus inspection of the corresponding adapter result.
4. Execute a fully local successful journey: mock registry response → `PromptKitClient.fetch()` → `RetrievedPrompt.compile()` → Gemini, OpenAI Chat Completions, OpenAI Responses, and LiteLLM conversions.
5. Exercise the public exception hierarchy and each available public failure path without leaking test API keys or supplied secret values into assertion messages.
