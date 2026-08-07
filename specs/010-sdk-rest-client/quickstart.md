# Quickstart: SDK Remote Prompt Retrieval

## Prerequisites

- Python 3.13+
- uv
- A running PromptKit server with a published prompt and a configured API key
- The Day 10 package implementation committed before performing the Git-subdirectory check

## Workspace validation

From the repository root, synchronize the workspace after the package member and its dependencies are added:

```powershell
uv sync
uv run pytest tests/promptkit/unit
uv run ruff check packages/promptkit tests/promptkit
uv run ruff format --check packages/promptkit tests/promptkit
uv run mypy packages/promptkit
```

Expected result: the client unit tests pass; lint, formatting, and type checks report no errors.

## Retrieve an on-live prompt

Supply the key from your own secret/configuration system and pass it explicitly to the client. Do not put the key in source code or shell history.

```python
import os

from promptkit import PromptKitClient

client = PromptKitClient(
    base_url="http://127.0.0.1:8000",
    api_key=os.environ["PROMPTKIT_API_KEY"],
)
prompt = client.fetch("greeting-prompt")
print(prompt.version)
```

Expected result: the returned object contains the on-live published version, its sections, and declared variables. Calling `fetch("greeting-prompt", label="staging")` resolves that explicit published label. `production` fails locally; an absent on-live version, unknown slug, and unavailable label raise distinct errors.

## Verify independent Git-subdirectory installation

Run this only after committing the package implementation. Create an empty temporary virtual environment, then install from the current committed repository through the package subdirectory:

```powershell
$temporaryEnvironment = Join-Path $env:TEMP "promptkit-sdk-install-check"
uv venv $temporaryEnvironment --python 3.13 --seed
$commit = git rev-parse HEAD
& "$temporaryEnvironment\Scripts\python.exe" -m pip install "git+file:///D:/Projects/Private/promptkit@$commit#subdirectory=packages/promptkit"
& "$temporaryEnvironment\Scripts\python.exe" -c "from promptkit import PromptKitClient; print(PromptKitClient.__name__)"
Remove-Item -LiteralPath $temporaryEnvironment -Recurse
```

Expected result: installation succeeds without installing the Django server or `promptkit-django`, and the public client import succeeds. The temporary environment is removed after the check.
