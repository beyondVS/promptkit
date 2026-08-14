from __future__ import annotations

import importlib.resources

import promptkit_django


def test_public_api_is_deliberate_and_typed() -> None:
    assert promptkit_django.__all__ == [
        "PromptKitDjangoConfig",
        "PromptKitDjangoConfigurationError",
        "PromptKitDjangoNotInitializedError",
        "get_client",
    ]
    assert importlib.resources.files("promptkit_django").joinpath("py.typed").is_file()
    for name in promptkit_django.__all__:
        assert getattr(promptkit_django, name).__doc__
