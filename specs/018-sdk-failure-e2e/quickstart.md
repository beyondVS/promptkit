# Quickstart: SDK Failure Resilience E2E Validation

## Prerequisites

- Python 3.13+ and `uv` are available.
- Project dependencies are already synchronized.
- Run commands from the repository root.
- No separately running Prompt Server, PostgreSQL service, external LLM, or production credential is required.

## Run the focused E2E validation

```powershell
uv run pytest tests/promptkit/integration/test_sdk_failure_e2e.py -q
```

Expected outcomes:

- the managed local HTTP server passes its health readiness check;
- a test-owned published on-live prompt is retrieved with the public SDK;
- server unavailability, local credential configuration, and server authentication rejection produce distinct public exceptions;
- missing, unexpected, and incompatible variables produce no compiled result or downstream call;
- scoped SDK failure paths emit no PromptKit records and do not change logging configuration;
- protected credential, variable, and prompt sentinels occur zero times in inspected diagnostics;
- the matrix passes three same-process repetitions.

## Run focused regressions

```powershell
uv run pytest tests/promptkit/unit tests/promptkit/integration apps/server/prompts/tests/test_read_only_api.py -q
```

Expected result: existing public retrieval, compilation, exception, adapter, authentication, and read-only registry contracts remain green.

## Run repository quality gates

```powershell
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

## Interpret failures

- **Readiness failure**: investigate the pytest-django server/test-database setup; do not treat it as an SDK communication result.
- **Wrong exception class**: compare the scenario with [failure-resilience-contract.md](./contracts/failure-resilience-contract.md).
- **Protected sentinel found**: treat as a security-blocking failure and inspect exception chaining and application log formatting.
- **SDK record or logger mutation found**: isolate records to `promptkit` namespaces and verify the operation is one of the scoped fetch/compile failure paths.
- **Port-related failure**: ensure the test uses an ephemeral bind-only loopback socket and closes it deterministically; do not substitute a fixed port.
- **Full-suite-only failure**: check for shared logger, socket, client, or database state leaking between tests.
