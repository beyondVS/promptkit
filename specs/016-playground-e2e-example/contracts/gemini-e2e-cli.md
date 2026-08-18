# Contract: Gemini E2E Example CLI

## Location and dependency boundary

The example lives under `examples/gemini-e2e/` as an isolated `uv` project. It declares compatible `promptkit` and `google-genai>=2.18.1,<3` dependencies locally. No provider dependency is added to the root, server, core SDK, or core SDK extras.

## Invocation

```text
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py [--live]
```

Configuration is read from the environment contract in [data-model.md](../data-model.md). No secret may be supplied as a command-line value.

## Non-live behavior

Without `--live`, the command:

1. validates PromptKit configuration and parameter JSON;
2. fetches the omitted-label on-live prompt through `PromptKitClient`;
3. compiles locally through `RetrievedPrompt.compile()`;
4. converts through `GeminiAdapter.to_generate_content_args()`;
5. prints safe stage completion and source slug/version;
6. states how to opt into live execution and exits successfully;
7. imports/constructs no Gemini client and performs zero Gemini requests.

## Live behavior

With `--live`, the command performs the same first four stages, then validates `GEMINI_API_KEY` and `GEMINI_MODEL`, creates the example-owned synchronous client, expands the adapter result into one `generate_content` call, prints a non-empty text response, and closes the client. It performs exactly one Gemini request and no automatic retry.

The example never creates, modifies, publishes, labels, or deletes a prompt.

## Failure categories

| Category | Examples | Required behavior |
|----------|----------|-------------------|
| Configuration | missing/blank environment value, invalid parameter JSON | Stop before registry/provider calls; name the invalid setting without its value |
| Registry | authentication, not found, no on-live version, rate limit, communication, invalid response | Stop before compilation/provider call; identify `registry` stage |
| Compilation | missing/type/unexpected variable, invalid template | Stop before provider construction; identify `compilation` stage without values/content |
| Adapter | unsupported role/order | Stop before provider construction; identify `adapter` stage |
| Gemini | authentication, quota, communication, empty/unexpected response | Identify `gemini` stage without key, prompt, or full provider arguments |

All expected failures return a non-zero process status. Output must never contain either API key, the full parameter mapping, compiled prompt text in errors, or authorization headers.

## Automated contract

Default tests replace the registry and provider boundaries. They prove stage order, stop-on-failure behavior, zero non-live calls, exactly one live call, client closure, response handling, and secret-safe output without requiring network, provider package installation in the root environment, credentials, quota, or cost.
