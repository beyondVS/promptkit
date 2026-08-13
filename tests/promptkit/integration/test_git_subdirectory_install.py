import shutil
import subprocess
import sys
from pathlib import Path


def test_installs_committed_git_subdirectory_in_isolated_environment(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    snapshot = tmp_path / "repository-snapshot"
    package_snapshot = snapshot / "packages" / "promptkit"
    shutil.copytree(repository_root / "packages" / "promptkit", package_snapshot)
    subprocess.run(["git", "init"], cwd=snapshot, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "add", "packages/promptkit"],
        cwd=snapshot,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=PromptKit Tests",
            "-c",
            "user.email=tests@example.invalid",
            "commit",
            "-m",
            "Package snapshot",
        ],
        cwd=snapshot,
        check=True,
        capture_output=True,
        text=True,
    )
    environment = tmp_path / "promptkit-sdk-install"
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    python = environment / "Scripts" / "python.exe"
    package_url = f"git+{snapshot.as_uri()}#subdirectory=packages/promptkit"

    subprocess.run([str(python), "-m", "pip", "install", package_url], check=True)
    result = subprocess.run(
        [
            str(python),
            "-c",
            (
                "import importlib.util; "
                "from promptkit import (CompiledPrompt, CompiledPromptSection, "
                "GeminiAdapter, LiteLLMAdapter, OpenAIAdapter, PromptKitClient); "
                "assert PromptKitClient.__name__ == 'PromptKitClient'; "
                "prompt = CompiledPrompt(slug='demo', version=1, label=None, "
                "content='Hello', sections=(CompiledPromptSection(role='user', "
                "order=0, content='Hello'),)); "
                "assert GeminiAdapter.to_generate_content_args(prompt) == "
                "{'contents': [{'role': 'user', 'parts': [{'text': 'Hello'}]}]}; "
                "assert OpenAIAdapter.to_chat_completions_args(prompt) == "
                "{'messages': [{'role': 'user', 'content': 'Hello'}]}; "
                "assert OpenAIAdapter.to_responses_args(prompt) == "
                "{'input': [{'role': 'user', 'content': 'Hello'}]}; "
                "assert LiteLLMAdapter.to_completion_args(prompt) == "
                "{'messages': [{'role': 'user', 'content': 'Hello'}]}; "
                "assert importlib.util.find_spec('django') is None; "
                "assert importlib.util.find_spec('google') is None; "
                "assert importlib.util.find_spec('openai') is None; "
                "assert importlib.util.find_spec('litellm') is None"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
