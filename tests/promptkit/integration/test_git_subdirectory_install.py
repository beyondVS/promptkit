import subprocess
import sys
from pathlib import Path


def test_installs_committed_git_subdirectory_in_isolated_environment(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    environment = tmp_path / "promptkit-sdk-install"
    subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    python = environment / "Scripts" / "python.exe"
    package_url = f"git+{repository_root.as_uri()}@{head}#subdirectory=packages/promptkit"

    subprocess.run([str(python), "-m", "pip", "install", package_url], check=True)
    result = subprocess.run(
        [
            str(python),
            "-c",
            (
                "import importlib.util; "
                "from promptkit import PromptKitClient; "
                "assert PromptKitClient.__name__ == 'PromptKitClient'; "
                "assert importlib.util.find_spec('django') is None"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
