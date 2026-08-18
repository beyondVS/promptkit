"""Offline contract tests for the isolated Gemini E2E consumer example."""

import importlib.util
import io
import os
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest import TestCase
from unittest.mock import patch

import promptkit

EXAMPLE_PATH = Path(__file__).parents[2] / "examples" / "gemini-e2e" / "gemini_e2e.py"


def load_example() -> ModuleType:
    """Load the hyphenated example directory as an isolated test module."""
    spec = importlib.util.spec_from_file_location("promptkit_gemini_e2e", EXAMPLE_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load Gemini E2E example")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def retrieved_prompt() -> promptkit.RetrievedPrompt:
    """Return a provider-neutral prompt fixture."""
    return promptkit.RetrievedPrompt(
        slug="support-reply",
        name="Support reply",
        description="Example",
        category=promptkit.PromptCategory(name="Support", slug="support"),
        version=2,
        version_status="published",
        is_on_live=True,
        label=None,
        template_text="Hello {{ name }}",
        variables=[
            promptkit.PromptVariable(
                name="name",
                var_type="string",
                required=True,
                default_value=None,
                description="Recipient",
            )
        ],
        sections=[promptkit.PromptSection(role="user", order=0, content="Hello {{ name }}")],
        created_at="2026-08-18T00:00:00Z",
    )


class FakeRegistryClient:
    """Track registry use without network access."""

    def __init__(
        self,
        prompt: promptkit.RetrievedPrompt | Exception,
        *,
        close_error: Exception | None = None,
    ) -> None:
        self.prompt = prompt
        self.close_error = close_error
        self.fetch_calls: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    def fetch(self, slug: str, **kwargs: Any) -> promptkit.RetrievedPrompt:
        self.fetch_calls.append((slug, kwargs))
        if isinstance(self.prompt, Exception):
            raise self.prompt
        return self.prompt

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeGeminiClient:
    """Track one context-managed provider call."""

    def __init__(self, response_text: str | None = "Gemini response") -> None:
        self.response_text = response_text
        self.calls: list[dict[str, Any]] = []
        self.closed = False
        self.models = self

    def __enter__(self) -> "FakeGeminiClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.closed = True

    def generate_content(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(text=self.response_text)


class GeminiE2EExampleTests(TestCase):
    """Protect stage ordering, live consent, and secret-safe failures."""

    def setUp(self) -> None:
        self.example = load_example()
        self.base_env = {
            "PROMPTKIT_BASE_URL": "https://registry.example.com",
            "PROMPTKIT_API_KEY": "registry-secret",
            "PROMPTKIT_PROMPT_SLUG": "support-reply",
            "PROMPTKIT_PROMPT_PARAMS": '{"name":"Ada"}',
        }

    def test_non_live_fetches_compiles_and_adapts_without_gemini_factory(self) -> None:
        registry = FakeRegistryClient(retrieved_prompt())
        stdout = io.StringIO()
        gemini_factory_calls: list[str] = []

        status = self.example.run(
            live=False,
            environ=self.base_env,
            registry_client_factory=lambda *_: registry,
            gemini_client_factory=lambda key: gemini_factory_calls.append(key),
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(status, 0)
        self.assertEqual(registry.fetch_calls, [("support-reply", {})])
        self.assertTrue(registry.closed)
        self.assertEqual(gemini_factory_calls, [])
        output = stdout.getvalue()
        self.assertLess(output.index("registry: complete"), output.index("compilation: complete"))
        self.assertLess(output.index("compilation: complete"), output.index("adapter: complete"))
        self.assertNotIn("Hello Ada", output)
        self.assertNotIn("registry-secret", output)

    def test_live_calls_gemini_exactly_once_and_closes_client(self) -> None:
        registry = FakeRegistryClient(retrieved_prompt())
        gemini = FakeGeminiClient()
        environ = {
            **self.base_env,
            "GEMINI_API_KEY": "gemini-secret",
            "GEMINI_MODEL": "operator-model",
        }
        stdout = io.StringIO()

        status = self.example.run(
            live=True,
            environ=environ,
            registry_client_factory=lambda *_: registry,
            gemini_client_factory=lambda key: gemini,
            stdout=stdout,
            stderr=io.StringIO(),
        )

        self.assertEqual(status, 0)
        self.assertEqual(len(gemini.calls), 1)
        self.assertEqual(gemini.calls[0]["model"], "operator-model")
        self.assertTrue(gemini.closed)
        self.assertIn("Gemini response", stdout.getvalue())
        self.assertNotIn("gemini-secret", stdout.getvalue())

    def test_configuration_failure_stops_before_registry(self) -> None:
        calls: list[object] = []
        stderr = io.StringIO()

        status = self.example.run(
            live=False,
            environ={**self.base_env, "PROMPTKIT_PROMPT_PARAMS": "[]"},
            registry_client_factory=lambda *_: calls.append(object()),
            gemini_client_factory=lambda key: calls.append(key),
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertEqual(calls, [])
        self.assertIn("configuration", stderr.getvalue())

    def test_registry_failure_stops_before_gemini_and_redacts_secrets(self) -> None:
        registry = FakeRegistryClient(promptkit.AuthenticationError("registry-secret rejected"))
        provider_calls: list[str] = []
        stderr = io.StringIO()

        status = self.example.run(
            live=False,
            environ=self.base_env,
            registry_client_factory=lambda *_: registry,
            gemini_client_factory=lambda key: provider_calls.append(key),
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertEqual(provider_calls, [])
        self.assertIn("registry", stderr.getvalue())
        self.assertNotIn("registry-secret", stderr.getvalue())

    def test_registry_close_failure_is_sanitized_and_stops_the_journey(self) -> None:
        registry = FakeRegistryClient(
            retrieved_prompt(), close_error=RuntimeError("registry-secret close failure")
        )
        stderr = io.StringIO()

        status = self.example.run(
            live=False,
            environ=self.base_env,
            registry_client_factory=lambda *_: registry,
            gemini_client_factory=lambda key: FakeGeminiClient(),
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertTrue(registry.closed)
        self.assertIn("registry", stderr.getvalue())
        self.assertNotIn("registry-secret", stderr.getvalue())

    def test_compilation_and_adapter_failures_stop_before_provider(self) -> None:
        for prompt, expected_stage in (
            (retrieved_prompt().model_copy(update={"variables": []}), "compilation"),
            (
                retrieved_prompt().model_copy(
                    update={
                        "sections": [
                            promptkit.PromptSection(role="tool", order=0, content="secret-prompt")
                        ]
                    }
                ),
                "adapter",
            ),
        ):
            with self.subTest(expected_stage=expected_stage):
                provider_calls: list[str] = []
                stderr = io.StringIO()
                status = self.example.run(
                    live=False,
                    environ=self.base_env,
                    registry_client_factory=lambda *_: FakeRegistryClient(prompt),
                    gemini_client_factory=lambda key: provider_calls.append(key),
                    stdout=io.StringIO(),
                    stderr=stderr,
                )
                self.assertNotEqual(status, 0)
                self.assertEqual(provider_calls, [])
                self.assertIn(expected_stage, stderr.getvalue())
                self.assertNotIn("secret-prompt", stderr.getvalue())

    def test_live_rejects_empty_response_and_closes_client(self) -> None:
        gemini = FakeGeminiClient(response_text="")
        stderr = io.StringIO()

        status = self.example.run(
            live=True,
            environ={
                **self.base_env,
                "GEMINI_API_KEY": "gemini-secret",
                "GEMINI_MODEL": "operator-model",
            },
            registry_client_factory=lambda *_: FakeRegistryClient(retrieved_prompt()),
            gemini_client_factory=lambda key: gemini,
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertEqual(len(gemini.calls), 1)
        self.assertTrue(gemini.closed)
        self.assertIn("gemini", stderr.getvalue())
        self.assertNotIn("gemini-secret", stderr.getvalue())

    def test_live_missing_gemini_configuration_stops_before_provider(self) -> None:
        provider_calls: list[str] = []
        stderr = io.StringIO()

        status = self.example.run(
            live=True,
            environ=self.base_env,
            registry_client_factory=lambda *_: FakeRegistryClient(retrieved_prompt()),
            gemini_client_factory=lambda key: provider_calls.append(key),
            stdout=io.StringIO(),
            stderr=stderr,
        )

        self.assertNotEqual(status, 0)
        self.assertEqual(provider_calls, [])
        self.assertIn("configuration", stderr.getvalue())

    def test_main_loads_adjacent_dotenv_without_overriding_shell_values(self) -> None:
        captured_environ: dict[str, str] = {}

        def capture_run(**kwargs: Any) -> int:
            captured_environ.update(kwargs["environ"])
            return 0

        with (
            patch.object(self.example, "load_dotenv") as load_dotenv_mock,
            patch.object(self.example, "run", side_effect=capture_run),
            patch.dict(os.environ, {"PROMPTKIT_PROMPT_SLUG": "shell-slug"}, clear=True),
        ):
            status = self.example.main([])

        self.assertEqual(status, 0)
        load_dotenv_mock.assert_called_once_with(self.example.ENV_FILE, override=False)
        self.assertEqual(captured_environ["PROMPTKIT_PROMPT_SLUG"], "shell-slug")
