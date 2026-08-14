"""Verify the Django integration installs from its Git subdirectory alone."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def run(command: list[str], *, cwd: Path) -> None:
    """Run a packaging command while preserving its useful failure output."""
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_installs_committed_git_subdirectory_in_isolated_environment(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    uv = shutil.which("uv")
    assert uv is not None, "uv is required for the isolated package-installation test"

    wheelhouse = tmp_path / "wheelhouse"
    run(
        [uv, "build", "--package", "promptkit", "--wheel", "--out-dir", str(wheelhouse)],
        cwd=repository_root,
    )

    snapshot = tmp_path / "repository-snapshot"
    package_snapshot = snapshot / "packages" / "promptkit-django"
    shutil.copytree(repository_root / "packages" / "promptkit-django", package_snapshot)
    run(["git", "init"], cwd=snapshot)
    run(["git", "add", "packages/promptkit-django"], cwd=snapshot)
    run(
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
    )

    environment = tmp_path / "promptkit-django-install"
    run([uv, "venv", "--seed", str(environment)], cwd=tmp_path)
    python = environment / "Scripts" / "python.exe"
    package_url = f"git+{snapshot.as_uri()}#subdirectory=packages/promptkit-django"
    # uv 0.9.12 on Windows panics for equivalent local ``git+file`` URLs.
    # The seeded interpreter's pip still exercises the required Git-subdirectory
    # installation contract in the temporary uv environment.
    run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--find-links",
            str(wheelhouse),
            package_url,
        ],
        cwd=tmp_path,
    )

    script = """
import importlib.metadata
from pathlib import Path

from django.conf import settings

environment = Path(r'__ENVIRONMENT__').resolve()
settings.configure(
    INSTALLED_APPS=['promptkit_django'],
    PROMPTKIT={
        'BASE_URL': 'https://registry.example.com',
        'API_KEY': 'isolated-test-key',
    },
)
import django
django.setup()

from promptkit_django import PromptKitDjangoConfig, get_client

assert PromptKitDjangoConfig.__name__ == 'PromptKitDjangoConfig'
assert get_client() is get_client()
for distribution_name in ('promptkit', 'promptkit-django', 'Django'):
    location = Path(importlib.metadata.distribution(distribution_name).locate_file('')).resolve()
    assert environment in location.parents, (distribution_name, location)
""".replace("__ENVIRONMENT__", str(environment))
    environment_variables = os.environ.copy()
    environment_variables.pop("PYTHONPATH", None)
    result = subprocess.run(
        [str(python), "-c", script],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=environment_variables,
    )

    assert result.returncode == 0
