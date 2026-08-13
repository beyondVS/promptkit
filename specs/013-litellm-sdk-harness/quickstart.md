# Quickstart: Validate LiteLLM Conversion and the Public SDK Harness

## Prerequisites

- Run commands from the repository root.
- Use the project-managed environment; do not install LiteLLM for this feature.

## Validate the LiteLLM adapter contract

```powershell
uv run pytest tests/promptkit/unit/test_adapters.py
```

Expected outcome: the LiteLLM adapter's ordered role/content mapping, sectionless fallback, duplicate-order and invalid-role failure behavior, safe system-only warning, immutability, text fidelity, provider-import exclusion, and 200-section performance boundary all pass alongside the existing adapter contracts.

## Validate the public SDK integration harness

```powershell
uv run pytest tests/promptkit/integration/test_public_sdk_harness.py
```

Expected outcome: the complete package-root public inventory is mapped with no stale entries, and a controlled registry response completes retrieval, local compilation, and every provider conversion without a network or provider request. See [the contract](contracts/sdk-litellm-and-public-harness.md) for the public behavior being checked.

## Run the core SDK suite and quality checks

```powershell
uv run pytest tests/promptkit
uv run ruff check packages/promptkit tests/promptkit
uv run mypy packages/promptkit tests/promptkit
```

Expected outcome: all commands exit successfully. A failure reporting missing or stale coverage-map names means a public export changed without a corresponding harness assertion; update the mapping and its explicit assertion before accepting the change.
