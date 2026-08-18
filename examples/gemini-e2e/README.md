# PromptKit Gemini E2E Example

This isolated consumer example demonstrates the full application-owned journey:

1. fetch an on-live prompt from Prompt Server with the read-only SDK;
2. compile variables locally with `RetrievedPrompt.compile()`;
3. convert the immutable result with `GeminiAdapter`;
4. optionally make one Gemini request from this example application.

Prompt Server remains a registry, the SDK never calls an LLM, and the adapter only converts arguments.

## Prerequisites

- Python 3.13+ and `uv`
- A running Prompt Server
- A read-only PromptKit API key
- A published prompt marked on-live; omitted-label fetch deliberately has no draft, `latest`, or custom-label fallback
- For `--live` only: a Gemini API key, an accessible model, quota, and explicit consent to send the compiled prompt

Copy `examples/gemini-e2e/.env.example` to `examples/gemini-e2e/.env` and replace its placeholders. The script automatically loads that file from its own directory, regardless of the current working directory. Existing shell environment variables take precedence over `.env` values. Do not commit the populated `.env` file or pass secrets as command-line arguments.

```text
Copy-Item examples/gemini-e2e/.env.example examples/gemini-e2e/.env
```

Required for every run:

```text
PROMPTKIT_BASE_URL
PROMPTKIT_API_KEY
PROMPTKIT_PROMPT_SLUG
PROMPTKIT_PROMPT_PARAMS   # optional JSON object; defaults to {}
```

Required only for a live call:

```text
GEMINI_API_KEY
GEMINI_MODEL
```

## Safe non-live run

From the repository root:

```text
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py
```

This still contacts the configured Prompt Server, compiles locally, and runs the adapter. It does not import or construct the Gemini client and makes zero Gemini requests. Output contains only stage status and the safe prompt slug/version, never the compiled prompt or credentials.

## Explicit live run

Only after reviewing the compiled prompt's intended destination and accepting possible quota use or cost:

```text
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py --live
```

The live path performs exactly one synchronous `generate_content` call and does not retry. The context-managed Gemini client closes after success or failure.

## Expected output and failures

A non-live success reports `configuration`, `registry`, `compilation`, and `adapter` completion, then `gemini: skipped`. A live success additionally reports `gemini: complete` and prints the non-empty Gemini response.

Failures return non-zero status and identify one safe stage:

- `configuration`: missing settings or invalid parameter JSON
- `registry`: authentication, connectivity, rate limit, missing prompt/on-live version, or invalid response
- `compilation`: missing/invalid/unexpected variables or template mismatch
- `adapter`: unsupported section role/order
- `gemini`: authentication, model access, quota, connectivity, or empty response

Failure output excludes API keys, parameter mappings, compiled prompt text, authorization headers, and full provider arguments. Fix the named stage and rerun; no automatic retry occurs.

## Offline automated verification

The repository test replaces both external boundaries and requires no provider package in the root environment, credentials, network, quota, or cost:

```text
uv run pytest tests/examples/test_gemini_e2e.py
```
