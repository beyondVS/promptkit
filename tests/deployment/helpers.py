"""Utilities for validating installable PromptKit deployment artifacts."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPOSITORY_ROOT: Final = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class DeploymentUnit:
    """A separately installable project distribution."""

    identifier: str
    package_name: str
    source_subdirectory: str
    runtime_dependencies: tuple[str, ...]


PROMPTKIT = DeploymentUnit(
    identifier="promptkit",
    package_name="promptkit",
    source_subdirectory="packages/promptkit",
    runtime_dependencies=("httpx>=0.27,<1", "pydantic>=2,<3"),
)
PROMPTKIT_DJANGO = DeploymentUnit(
    identifier="promptkit-django",
    package_name="promptkit-django",
    source_subdirectory="packages/promptkit-django",
    runtime_dependencies=("Django>=5,<6", "pydantic>=2,<3"),
)
SERVER = DeploymentUnit(
    identifier="server",
    package_name="server",
    source_subdirectory="apps/server",
    runtime_dependencies=(
        "Django>=5,<6",
        "djangorestframework>=3.15.0",
        "psycopg[binary]>=3.1.0",
        "python-dotenv>=1.0.0",
    ),
)
UNITS: Final = (PROMPTKIT, PROMPTKIT_DJANGO, SERVER)


class DeploymentCommandError(AssertionError):
    """Report a subprocess failure with a stable scenario and stage prefix."""


@dataclass(frozen=True)
class ReleaseResult:
    """One compact release-decision row for an isolated scenario."""

    scenario: str
    unit: str
    installation_kind: str
    stage: str
    verdict: str


def render_release_summary(results: tuple[ReleaseResult, ...]) -> str:
    """Render deterministic, one-row-per-scenario release output."""
    header = "scenario | unit | installation | failed_stage | verdict"
    rows = [
        f"{result.scenario} | {result.unit} | {result.installation_kind} | "
        f"{result.stage} | {result.verdict}"
        for result in results
    ]
    return "\n".join((header, *rows))


def windows_python(environment: Path) -> Path:
    """Return the interpreter path for an isolated virtual environment."""
    return environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def command_environment() -> dict[str, str]:
    """Return a child environment that cannot import repository sources."""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    return environment


def run(
    scenario: str,
    stage: str,
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and preserve diagnostics behind a stable failure prefix."""
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise DeploymentCommandError(
            f"{scenario}:{stage}\ncommand={' '.join(command)}\n{result.stdout}{result.stderr}"
        )
    return result


def build_wheels(wheelhouse: Path) -> dict[str, Path]:
    """Build new wheels for every deployment unit into one temporary wheelhouse."""
    wheelhouse.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Path] = {}
    for unit in UNITS:
        run(
            unit.identifier,
            "build",
            [
                "uv",
                "build",
                "--package",
                unit.package_name,
                "--wheel",
                "--out-dir",
                str(wheelhouse),
            ],
            cwd=REPOSITORY_ROOT,
            env=command_environment(),
        )
        matches = sorted(wheelhouse.glob(f"{unit.package_name.replace('-', '_')}-*.whl"))
        if len(matches) != 1:
            raise AssertionError(f"{unit.identifier}:build expected one wheel, found {matches!r}")
        artifacts[unit.identifier] = matches[0]
    return artifacts


def create_snapshot(unit: DeploymentUnit, destination: Path) -> str:
    """Create a committed local Git snapshot and return its subdirectory URL."""
    package_destination = destination / Path(unit.source_subdirectory)
    package_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPOSITORY_ROOT / unit.source_subdirectory, package_destination)
    run(unit.identifier, "snapshot", ["git", "init"], cwd=destination, env=command_environment())
    run(
        unit.identifier,
        "snapshot",
        ["git", "add", unit.source_subdirectory],
        cwd=destination,
        env=command_environment(),
    )
    run(
        unit.identifier,
        "snapshot",
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
        cwd=destination,
        env=command_environment(),
    )
    return f"git+{destination.as_uri()}#subdirectory={unit.source_subdirectory}"


def create_environment(scenario: str, destination: Path) -> Path:
    """Create a dedicated uv-managed environment for one scenario."""
    run(
        scenario,
        "environment",
        ["uv", "venv", "--seed", str(destination)],
        cwd=destination.parent,
        env=command_environment(),
    )
    return windows_python(destination)


def install_runtime_dependencies(scenario: str, python: Path, unit: DeploymentUnit) -> None:
    """Acquire only third-party runtime dependencies before offline artifact validation."""
    if not unit.runtime_dependencies:
        return
    run(
        scenario,
        "dependencies",
        ["uv", "pip", "install", "--python", str(python), *unit.runtime_dependencies],
        cwd=python.parent.parent,
        env=command_environment(),
    )


def install_artifact(
    scenario: str,
    python: Path,
    artifact: str | Path,
    wheelhouse: Path,
    *,
    no_build_isolation: bool = False,
) -> None:
    """Install one target artifact without index resolution or source-path leakage."""
    command = [
        "uv",
        "pip",
        "install",
        "--python",
        str(python),
        "--no-index",
        "--find-links",
        str(wheelhouse),
        "--no-deps",
    ]
    if no_build_isolation:
        command.append("--no-build-isolation")
    command.append(str(artifact))
    run(
        scenario,
        "install",
        command,
        cwd=python.parent.parent,
        env=command_environment(),
    )


def assert_installed_from_environment(
    scenario: str, python: Path, distributions: tuple[str, ...]
) -> None:
    """Ensure imported distributions are installed in, never alongside, the repository."""
    distribution_literals = repr(distributions)
    script = (
        "import importlib.metadata; from pathlib import Path; "
        f"environment = Path(r'{python.parent.parent}').resolve(); "
        f"repository = Path(r'{REPOSITORY_ROOT}').resolve(); "
        f"names = {distribution_literals}; "
        "locations = [Path(importlib.metadata.distribution(name).locate_file('')).resolve() "
        "for name in names]; "
        "assert all(environment in location.parents for location in locations), locations; "
        "assert all(repository not in location.parents for location in locations), locations"
    )
    run(
        scenario,
        "import",
        [str(python), "-c", script],
        cwd=python.parent.parent,
        env=command_environment(),
    )


def run_python(
    scenario: str, python: Path, script: str, *, extra_environment: dict[str, str] | None = None
) -> None:
    """Run an installed-artifact smoke script outside the repository."""
    environment = command_environment()
    if extra_environment:
        environment.update(extra_environment)
    run(scenario, "smoke", [str(python), "-c", script], cwd=python.parent.parent, env=environment)
