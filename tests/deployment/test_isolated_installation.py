"""Consumer-environment contract tests for PromptKit deployment artifacts."""

from __future__ import annotations

import sys
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path
from typing import Callable

import pytest

from tests.deployment.helpers import (
    PROMPTKIT,
    PROMPTKIT_DJANGO,
    SERVER,
    DeploymentCommandError,
    DeploymentUnit,
    ReleaseResult,
    assert_installed_from_environment,
    build_wheels,
    create_environment,
    create_snapshot,
    install_artifact,
    install_runtime_dependencies,
    render_release_summary,
    run,
    run_python,
)

REQUIRED_SCENARIOS = (
    "promptkit-wheel",
    "promptkit-git",
    "promptkit-django-wheel",
    "promptkit-django-git",
    "server-wheel",
    "server-git",
    "sdk-django-promptkit-then-promptkit-django",
    "sdk-django-promptkit-django-then-promptkit",
)

EXPECTED_REQUIREMENTS = {
    "promptkit": {"httpx<1,>=0.27", "pydantic<3,>=2"},
    "promptkit-django": {"django<6,>=5", "promptkit<0.2,>=0.1", "pydantic<3,>=2"},
    "server": {
        "django<6.0,>=5.0",
        "djangorestframework>=3.15.0",
        "promptkit<0.2,>=0.1",
        "psycopg[binary]>=3.1.0",
        "python-dotenv>=1.0.0",
    },
}


def wheel_metadata(wheel: Path) -> tuple[Message, set[str]]:
    """Read distribution metadata and archived file names from a wheel."""
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
        return metadata, set(archive.namelist())


def normalized_requirements(metadata: Message) -> set[str]:
    """Normalize wheel runtime dependencies for contract comparison."""
    return {
        requirement.lower().replace(" ", "")
        for requirement in metadata.get_all("Requires-Dist", [])
    }


def assert_metadata_contract(scenario: str, metadata: Message, package_name: str) -> None:
    """Fail at the owning artifact stage when declared dependencies drift."""
    actual = normalized_requirements(metadata)
    missing = EXPECTED_REQUIREMENTS[package_name] - actual
    if missing:
        raise DeploymentCommandError(
            f"{scenario}:build\nmissing Requires-Dist: {sorted(missing)!r}"
        )


def assert_server_package_data(scenario: str, files: set[str]) -> None:
    """Fail at artifact validation when server resources are absent."""
    required = ("core/templates/core/landing.html", "prompts/migrations/0001_initial.py")
    missing = [path for path in required if not any(name.endswith(path) for name in files)]
    if missing:
        raise DeploymentCommandError(f"{scenario}:build\nmissing package data: {missing!r}")


def rewrite_wheel(
    source: Path, destination: Path, transform: Callable[[str, bytes], bytes | None]
) -> Path:
    """Create an actual altered wheel used only by a negative installation scenario."""
    with (
        zipfile.ZipFile(source) as input_archive,
        zipfile.ZipFile(destination, "w") as output_archive,
    ):
        for name in input_archive.namelist():
            content = input_archive.read(name)
            replacement = transform(name, content)
            if replacement is not None:
                output_archive.writestr(name, replacement)
    return destination


@pytest.fixture(scope="module")
def artifact_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create one immutable wheelhouse used by all consumer scenarios."""
    root = tmp_path_factory.mktemp("deployment-artifacts")
    build_wheels(root / "wheelhouse")
    return root


def test_builds_three_new_artifacts_with_server_namespace_and_package_data(
    artifact_root: Path,
) -> None:
    """Define the artifact contract before changing server packaging."""
    artifacts = build_wheels(artifact_root / "wheelhouse")

    server_metadata, server_files = wheel_metadata(artifacts[SERVER.identifier])

    assert server_metadata["Name"] == "server"
    assert server_metadata["Requires-Python"] == ">=3.13"
    assert any(name.startswith("apps/server/config/") for name in server_files)
    assert any(name.startswith("apps/server/core/") for name in server_files)
    assert any(name.startswith("apps/server/prompts/") for name in server_files)
    assert_server_package_data("server-wheel", server_files)


@pytest.mark.parametrize("package_name", ("promptkit", "promptkit-django", "server"))
def test_built_artifact_metadata_declares_name_version_and_runtime(
    package_name: str, artifact_root: Path
) -> None:
    """Require every package wheel to expose its consumer-facing metadata."""
    artifacts = build_wheels(artifact_root / "wheelhouse")
    metadata, _ = wheel_metadata(artifacts[package_name])

    assert metadata["Name"] == package_name
    assert metadata["Version"] == "0.1.0"
    assert metadata["Requires-Python"] == ">=3.13"
    assert_metadata_contract(f"{package_name}-wheel", metadata, package_name)


def install_unit(
    unit: DeploymentUnit,
    installation_kind: str,
    artifact_root: Path,
    tmp_path: Path,
) -> tuple[str, Path]:
    """Install one unit from its built wheel or local committed Git snapshot."""
    scenario = f"{unit.identifier}-{installation_kind}"
    wheelhouse = artifact_root / "wheelhouse"
    tmp_path.mkdir(parents=True, exist_ok=True)
    python = create_environment(scenario, tmp_path / "environment")
    install_runtime_dependencies(scenario, python, unit)
    artifacts = build_wheels(wheelhouse)
    if unit is not PROMPTKIT:
        install_runtime_dependencies(scenario, python, PROMPTKIT)
        install_artifact(scenario, python, artifacts[PROMPTKIT.identifier], wheelhouse)
    if installation_kind == "wheel":
        artifact: str | Path = artifacts[unit.identifier]
    else:
        install_runtime_dependencies(
            scenario,
            python,
            DeploymentUnit("build", "build", "", ("hatchling",)),
        )
        artifact = create_snapshot(unit, tmp_path / "snapshot")
    install_artifact(
        scenario,
        python,
        artifact,
        wheelhouse,
        no_build_isolation=installation_kind == "git",
    )
    return scenario, python


def test_promptkit_wheel_installs_and_compiles(artifact_root: Path, tmp_path: Path) -> None:
    """Install the core wheel without Django or provider SDKs."""
    scenario, python = install_unit(PROMPTKIT, "wheel", artifact_root, tmp_path)
    assert_installed_from_environment(scenario, python, ("promptkit",))
    run_python(
        scenario,
        python,
        "import importlib.util; from promptkit import CompiledPrompt, CompiledPromptSection; "
        "prompt = CompiledPrompt(slug='demo', version=1, label=None, content='Hello', "
        "sections=(CompiledPromptSection(role='user', order=0, content='Hello'),)); "
        "assert prompt.content == 'Hello'; assert importlib.util.find_spec('django') is None",
    )


def test_promptkit_git_installs_and_compiles(artifact_root: Path, tmp_path: Path) -> None:
    """Install the core package from a committed local Git subdirectory."""
    scenario, python = install_unit(PROMPTKIT, "git", artifact_root, tmp_path)
    assert_installed_from_environment(scenario, python, ("promptkit",))
    script = "\n".join(
        (
            "from promptkit import PromptKitClient",
            "assert PromptKitClient.__name__ == 'PromptKitClient'",
        )
    )
    run_python(scenario, python, script)


@pytest.mark.parametrize("installation_kind", ("wheel", "git"))
def test_promptkit_django_installs_and_initializes(
    installation_kind: str, artifact_root: Path, tmp_path: Path
) -> None:
    """Install the Django integration with only the matching core artifact."""
    scenario, python = install_unit(PROMPTKIT_DJANGO, installation_kind, artifact_root, tmp_path)
    assert_installed_from_environment(scenario, python, ("promptkit", "promptkit-django", "Django"))
    run_python(
        scenario,
        python,
        "from django.conf import settings; settings.configure(INSTALLED_APPS=['promptkit_django'], "
        "PROMPTKIT={'BASE_URL': 'https://registry.example.com', 'API_KEY': 'test-key'}); "
        "import django; django.setup(); from promptkit_django import get_client; "
        "assert get_client() is get_client(); get_client().close()",
    )


@pytest.mark.parametrize("installation_kind", ("wheel", "git"))
def test_server_installs_and_serves_health_check(
    installation_kind: str, artifact_root: Path, tmp_path: Path
) -> None:
    """Run the database-free health endpoint from an installed server artifact."""
    scenario, python = install_unit(SERVER, installation_kind, artifact_root, tmp_path)
    assert_installed_from_environment(scenario, python, ("promptkit", "server", "Django"))
    script = "\n".join(
        (
            "import django",
            "from django.test import Client",
            "django.setup()",
            "response = Client().get('/api/v1/health/')",
            "assert response.status_code == 200",
            "assert response.json() == {'status': 'ok', 'service': 'promptkit-server'}",
        )
    )
    run_python(
        scenario,
        python,
        script,
        extra_environment={
            "DJANGO_SETTINGS_MODULE": "apps.server.config.settings",
            "PROMPTKIT_API_KEY": "isolated-test-key",
            "ALLOWED_HOSTS": "testserver",
        },
    )


@pytest.mark.parametrize(
    "requested_order", (("promptkit", "promptkit-django"), ("promptkit-django", "promptkit"))
)
def test_sdk_and_django_wheels_interoperate_in_both_requested_orders(
    requested_order: tuple[str, str], artifact_root: Path, tmp_path: Path
) -> None:
    """Keep the installed core/Django public contract independent of request order."""
    scenario = f"sdk-django-{'-then-'.join(requested_order)}"
    wheelhouse = artifact_root / "wheelhouse"
    artifacts = build_wheels(wheelhouse)
    tmp_path.mkdir(parents=True, exist_ok=True)
    python = create_environment(scenario, tmp_path / "environment")
    install_runtime_dependencies(scenario, python, PROMPTKIT)
    install_runtime_dependencies(scenario, python, PROMPTKIT_DJANGO)

    units = {PROMPTKIT.identifier: PROMPTKIT, PROMPTKIT_DJANGO.identifier: PROMPTKIT_DJANGO}
    for identifier in requested_order:
        install_artifact(scenario, python, artifacts[units[identifier].identifier], wheelhouse)

    assert_installed_from_environment(scenario, python, ("promptkit", "promptkit-django", "Django"))
    script = "\n".join(
        (
            "from django.conf import settings",
            "settings.configure(INSTALLED_APPS=['promptkit_django'], "
            "PROMPTKIT={'BASE_URL': 'https://registry.example.com', 'API_KEY': 'test-key'})",
            "import django",
            "django.setup()",
            "from promptkit import RetrievedPrompt",
            "from promptkit_django import get_client",
            "client = get_client()",
            "assert client is get_client()",
            "payload = {",
            "    'slug': 'demo', 'name': 'Demo', 'description': '',",
            "    'category': {'name': 'General', 'slug': 'general'},",
            "    'version': 1, 'version_status': 'published', 'is_on_live': True, 'label': None,",
            "    'template_text': 'Hello {{ name }}',",
            "    'variables': [{'name': 'name', 'var_type': 'string', 'required': True,",
            "                   'default_value': None, 'description': ''}],",
            "    'sections': [], 'created_at': '2026-01-01T00:00:00Z',",
            "}",
            "prompt = RetrievedPrompt.model_validate(payload)",
            "assert prompt.compile({'name': 'Ada'}).content == 'Hello Ada'",
            "client.close()",
        )
    )
    run_python(
        scenario,
        python,
        script,
    )


def test_command_failures_identify_scenario_and_stage(tmp_path: Path) -> None:
    """Keep subprocess diagnostics actionable without mutating real artifacts."""
    with pytest.raises(DeploymentCommandError, match=r"malformed-wheel:install"):
        run(
            "malformed-wheel",
            "install",
            [sys.executable, "-c", "raise SystemExit(1)"],
            cwd=tmp_path,
        )


def test_malformed_artifacts_identify_missing_dependency_and_package_data(
    artifact_root: Path, tmp_path: Path
) -> None:
    """Install real altered wheels and attribute their consumer failures to smoke stages."""
    artifacts = build_wheels(artifact_root / "wheelhouse")
    wheelhouse = artifact_root / "wheelhouse"

    missing_dependency = rewrite_wheel(
        artifacts[PROMPTKIT.identifier],
        tmp_path / artifacts[PROMPTKIT.identifier].name,
        lambda name, content: (
            b"\n".join(
                line for line in content.splitlines() if b"Requires-Dist: pydantic" not in line
            )
            if name.endswith(".dist-info/METADATA")
            else content
        ),
    )
    dependency_python = create_environment("promptkit-missing-dependency", tmp_path / "dependency")
    install_runtime_dependencies(
        "promptkit-missing-dependency",
        dependency_python,
        DeploymentUnit("httpx", "httpx", "", ("httpx>=0.27,<1",)),
    )
    install_artifact(
        "promptkit-missing-dependency", dependency_python, missing_dependency, wheelhouse
    )
    with pytest.raises(DeploymentCommandError, match=r"promptkit-missing-dependency:smoke"):
        run_python("promptkit-missing-dependency", dependency_python, "import promptkit")

    missing_template = rewrite_wheel(
        artifacts[SERVER.identifier],
        tmp_path / artifacts[SERVER.identifier].name,
        lambda name, content: (
            None if name.endswith("core/templates/core/landing.html") else content
        ),
    )
    template_python = create_environment("server-missing-template", tmp_path / "template")
    install_runtime_dependencies("server-missing-template", template_python, SERVER)
    install_runtime_dependencies("server-missing-template", template_python, PROMPTKIT)
    install_artifact(
        "server-missing-template", template_python, artifacts[PROMPTKIT.identifier], wheelhouse
    )
    install_artifact("server-missing-template", template_python, missing_template, wheelhouse)
    with pytest.raises(DeploymentCommandError, match=r"server-missing-template:smoke"):
        run_python(
            "server-missing-template",
            template_python,
            "import django; from django.test import Client; django.setup(); Client().get('/')",
            extra_environment={
                "DJANGO_SETTINGS_MODULE": "apps.server.config.settings",
                "PROMPTKIT_API_KEY": "isolated-test-key",
                "ALLOWED_HOSTS": "testserver",
            },
        )


def run_release_matrix(artifact_root: Path, destination: Path) -> tuple[ReleaseResult, ...]:
    """Execute and record the eight consumer scenarios from fresh directories."""
    scenarios = (
        ("promptkit-wheel", "promptkit", "wheel", test_promptkit_wheel_installs_and_compiles),
        ("promptkit-git", "promptkit", "git", test_promptkit_git_installs_and_compiles),
        (
            "promptkit-django-wheel",
            "promptkit-django",
            "wheel",
            lambda root, path: test_promptkit_django_installs_and_initializes("wheel", root, path),
        ),
        (
            "promptkit-django-git",
            "promptkit-django",
            "git",
            lambda root, path: test_promptkit_django_installs_and_initializes("git", root, path),
        ),
        (
            "server-wheel",
            "server",
            "wheel",
            lambda root, path: test_server_installs_and_serves_health_check("wheel", root, path),
        ),
        (
            "server-git",
            "server",
            "git",
            lambda root, path: test_server_installs_and_serves_health_check("git", root, path),
        ),
        (
            "sdk-django-promptkit-then-promptkit-django",
            "promptkit",
            "wheel",
            lambda root, path: test_sdk_and_django_wheels_interoperate_in_both_requested_orders(
                ("promptkit", "promptkit-django"), root, path
            ),
        ),
        (
            "sdk-django-promptkit-django-then-promptkit",
            "promptkit",
            "wheel",
            lambda root, path: test_sdk_and_django_wheels_interoperate_in_both_requested_orders(
                ("promptkit-django", "promptkit"), root, path
            ),
        ),
    )
    results: list[ReleaseResult] = []
    for scenario, unit, installation_kind, execute in scenarios:
        try:
            execute(artifact_root, destination / scenario)
        except DeploymentCommandError as error:
            stage = str(error).split("\n", 1)[0].split(":", 1)[1]
            results.append(ReleaseResult(scenario, unit, installation_kind, stage, "FAIL"))
        else:
            results.append(ReleaseResult(scenario, unit, installation_kind, "", "PASS"))
    return tuple(results)


def test_release_matrix_reports_actual_results_and_is_repeatable(
    artifact_root: Path, tmp_path: Path
) -> None:
    """Print and compare summaries produced by two complete real scenario runs."""
    first = run_release_matrix(artifact_root, tmp_path / "first")
    second = run_release_matrix(artifact_root, tmp_path / "second")
    first_summary = render_release_summary(first)
    second_summary = render_release_summary(second)

    assert tuple(result.scenario for result in first) == REQUIRED_SCENARIOS
    assert all(result.verdict == "PASS" for result in first), first_summary
    assert first_summary == second_summary
    print(first_summary)
