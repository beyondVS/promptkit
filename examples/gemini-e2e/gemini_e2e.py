"""Prompt Server → PromptKit SDK → optional Gemini live-call example."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol, TextIO, cast

from promptkit import GeminiAdapter, PromptKitClient
from dotenv import load_dotenv

ENV_FILE = Path(__file__).with_name(".env")


class RegistryClient(Protocol):
    """Minimal read-only client boundary used by the example."""

    def fetch(self, slug: str) -> Any:
        """Fetch the omitted-label on-live prompt."""

    def close(self) -> None:
        """Close client resources."""


class GeminiClientContext(Protocol):
    """Context-managed Gemini client boundary used for offline tests."""

    def __enter__(self) -> Any:
        """Open the provider client."""

    def __exit__(self, *args: object) -> object:
        """Close the provider client."""


RegistryClientFactory = Callable[[str, str], RegistryClient]
GeminiClientFactory = Callable[[str], GeminiClientContext]


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise ValueError(f"missing setting: {name}")
    return value


def _load_promptkit_config(environ: Mapping[str, str]) -> tuple[str, str, str, dict[str, object]]:
    base_url = _required(environ, "PROMPTKIT_BASE_URL")
    api_key = _required(environ, "PROMPTKIT_API_KEY")
    slug = _required(environ, "PROMPTKIT_PROMPT_SLUG")
    raw_params = environ.get("PROMPTKIT_PROMPT_PARAMS", "{}").strip() or "{}"
    try:
        params = json.loads(raw_params)
    except json.JSONDecodeError as error:
        raise ValueError("invalid setting: PROMPTKIT_PROMPT_PARAMS") from error
    if not isinstance(params, dict):
        raise ValueError("invalid setting: PROMPTKIT_PROMPT_PARAMS must be a JSON object")
    return base_url, api_key, slug, cast(dict[str, object], params)


def _default_gemini_client_factory(api_key: str) -> GeminiClientContext:
    from google import genai

    return cast(GeminiClientContext, genai.Client(api_key=api_key))


def run(
    *,
    live: bool,
    environ: Mapping[str, str],
    registry_client_factory: RegistryClientFactory = PromptKitClient,
    gemini_client_factory: GeminiClientFactory = _default_gemini_client_factory,
    stdout: TextIO = sys.stdout,
    stderr: TextIO = sys.stderr,
) -> int:
    """Run the staged consumer journey and return a process status."""
    try:
        base_url, api_key, slug, params = _load_promptkit_config(environ)
    except (TypeError, ValueError):
        print("configuration: failed; check the named PromptKit environment settings", file=stderr)
        return 2
    print("configuration: complete", file=stdout)

    registry: RegistryClient | None = None
    try:
        registry = registry_client_factory(base_url, api_key)
        prompt = registry.fetch(slug)
    except Exception:
        if registry is not None:
            try:
                registry.close()
            except Exception:
                pass
        print(
            "registry: failed; check connectivity, credentials, and on-live publication",
            file=stderr,
        )
        return 3
    try:
        registry.close()
    except Exception:
        print(
            "registry: failed; check connectivity, credentials, and on-live publication",
            file=stderr,
        )
        return 3
    print(f"registry: complete (slug={prompt.slug}, version={prompt.version})", file=stdout)

    try:
        compiled = prompt.compile(params)
    except Exception:
        print("compilation: failed; check declarations, values, and template syntax", file=stderr)
        return 4
    print("compilation: complete", file=stdout)

    try:
        gemini_args = GeminiAdapter.to_generate_content_args(compiled)
    except Exception:
        print("adapter: failed; check the compiled section roles and ordering", file=stderr)
        return 5
    print("adapter: complete", file=stdout)

    if not live:
        print("gemini: skipped; rerun with --live to authorize one provider request", file=stdout)
        return 0

    try:
        gemini_api_key = _required(environ, "GEMINI_API_KEY")
        gemini_model = _required(environ, "GEMINI_MODEL")
    except ValueError:
        print("configuration: failed; check GEMINI_API_KEY and GEMINI_MODEL", file=stderr)
        return 2

    try:
        with gemini_client_factory(gemini_api_key) as client:
            response = client.models.generate_content(model=gemini_model, **gemini_args)
            response_text = response.text
        if not isinstance(response_text, str) or not response_text.strip():
            raise ValueError("empty Gemini response")
    except Exception:
        print(
            "gemini: failed; check credentials, model access, quota, and connectivity", file=stderr
        )
        return 6

    print("gemini: complete", file=stdout)
    print(response_text, file=stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse explicit live consent and execute the example."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="authorize exactly one Gemini request after registry, compile, and adapter stages",
    )
    args = parser.parse_args(argv)
    load_dotenv(ENV_FILE, override=False)
    return run(live=args.live, environ=os.environ)


if __name__ == "__main__":
    raise SystemExit(main())
