# Quickstart: 배포 격리 검증

## Prerequisites

- Python 3.13+ and `uv` are available.
- Git is available for local committed-snapshot scenarios.
- Run from repository root. No external Prompt Server, package publication, or database service is required.

## Run the focused matrix

```powershell
uv run pytest tests/deployment/test_isolated_installation.py
```

Expected result: every wheel and Git-subdirectory scenario reports success. Output identifies the deployment unit and stage for any failure.

## Run standard quality checks

```powershell
uv run ruff check
uv run ruff format --check
uv run mypy .
uv run pytest
```

## Interpret failures

- `*:build`: metadata or package layout cannot produce a new artifact.
- `*:install`: dependencies cannot resolve from isolated wheelhouse or Git source.
- `*:import`: public modules are unavailable or load from outside the environment.
- `*:smoke`: installed artifact cannot perform documented minimal local behavior.
- `*:interoperability`: the two requested core/Django installation orders differ.

The harness deletes temporary artifacts after the test. Investigate a failure by rerunning the focused test with pytest verbosity, not by reusing a prior virtual environment.
