from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import promptkit_django.cache as cache_module
import pytest
from django.core.cache.backends.locmem import LocMemCache
from promptkit import (
    AuthenticationError,
    ConditionalFetchResult,
    InvalidResponseError,
    LabelNotFoundError,
    NoDeployableVersionError,
    PromptNotFoundError,
    RetrievedPrompt,
)
from promptkit_django.configuration import PromptKitSettings
from promptkit_django.exceptions import PromptKitDjangoNotInitializedError


@pytest.fixture
def prompt() -> RetrievedPrompt:
    return RetrievedPrompt.model_validate(
        {
            "slug": "support-reply",
            "name": "Support reply",
            "description": "A response",
            "category": {"name": "Support", "slug": "support"},
            "version": 1,
            "version_status": "published",
            "is_on_live": True,
            "label": None,
            "template_text": "Hello",
            "variables": [],
            "sections": [{"role": "user", "order": 0, "content": "Hello"}],
            "created_at": "2026-08-07T00:00:00Z",
        }
    )


class FakeClient:
    def __init__(self, outcomes: Iterator[ConditionalFetchResult | Exception]) -> None:
        self.base_url = "https://registry.example.com/"
        self.outcomes = outcomes
        self.fetch_calls: list[tuple[str, str | None]] = []
        self.conditional_calls: list[tuple[str, str | None, str | None]] = []

    def fetch(self, slug: str, *, label: str | None = None) -> RetrievedPrompt:
        self.fetch_calls.append((slug, label))
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        assert outcome.prompt is not None
        return outcome.prompt

    def fetch_conditional(
        self, slug: str, *, label: str | None = None, etag: str | None = None
    ) -> ConditionalFetchResult:
        self.conditional_calls.append((slug, label, etag))
        outcome = next(self.outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@pytest.fixture
def configured_cache(monkeypatch: pytest.MonkeyPatch) -> Any:
    backend = LocMemCache("promptkit-cache-tests", {})
    backend.clear()
    monkeypatch.setattr(cache_module, "cache", backend)
    monkeypatch.setattr(
        cache_module,
        "get_client_settings",
        lambda: PromptKitSettings.model_validate(
            {
                "BASE_URL": "https://registry.example.com",
                "API_KEY": "not-a-real-secret",
                "CACHE_TTL": 60.0,
            }
        ),
    )
    return backend


def test_fresh_cache_hit_makes_exactly_one_registry_request_for_100_lookups(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"')])
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)

    for _ in range(100):
        assert cache_module.fetch_cached("support-reply") == prompt

    assert len(client.conditional_calls) == 1
    assert client.fetch_calls == []


def test_stale_entry_revalidates_with_etag_and_refreshes_without_replacing_prompt(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                ConditionalFetchResult(not_modified=True, prompt=None, etag='"v1"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    clock = iter([100.0, 161.0])
    monkeypatch.setattr(cache_module, "_now", lambda: next(clock))

    assert cache_module.fetch_cached("support-reply") == prompt
    assert cache_module.fetch_cached("support-reply") == prompt

    assert client.conditional_calls == [
        ("support-reply", None, None),
        ("support-reply", None, '"v1"'),
    ]


def test_identity_distinguishes_omitted_and_explicit_labels(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    labelled = prompt.model_copy(update={"label": "latest"})
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"on-live"'),
                ConditionalFetchResult(not_modified=False, prompt=labelled, etag='"latest"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)

    assert cache_module.fetch_cached("support-reply").label is None
    assert cache_module.fetch_cached("support-reply", label="latest").label == "latest"
    assert len(client.conditional_calls) == 2


def test_identity_isolates_registry_addresses_and_never_stores_credentials(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    first = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"first"')])
    )
    second_prompt = prompt.model_copy(update={"description": "Other registry"})
    second = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=second_prompt, etag='"second"')])
    )
    second.base_url = "https://other-registry.example.com/"
    current = first
    monkeypatch.setattr(cache_module, "get_client", lambda: current)

    assert cache_module.fetch_cached("support-reply") == prompt
    current = second
    assert cache_module.fetch_cached("support-reply") == second_prompt

    stored = repr(configured_cache._cache)
    assert "not-a-real-secret" not in stored
    assert len(first.conditional_calls) == 1
    assert len(second.conditional_calls) == 1


def test_prompt_and_global_invalidation_preserve_unrelated_cache_entries(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v2"'),
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v3"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    configured_cache.set("unrelated", "keep", timeout=60)

    cache_module.fetch_cached("support-reply")
    cache_module.clear_prompt_cache("support-reply")
    cache_module.fetch_cached("support-reply")
    cache_module.clear_prompt_cache()
    cache_module.fetch_cached("support-reply")

    assert len(client.conditional_calls) == 3
    assert configured_cache.get("unrelated") == "keep"


def test_changed_stale_response_replaces_the_cached_representation(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    replacement = prompt.model_copy(update={"description": "A changed response", "version": 2})
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                ConditionalFetchResult(not_modified=False, prompt=replacement, etag='"v2"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    clock = iter([100.0, 161.0])
    monkeypatch.setattr(cache_module, "_now", lambda: next(clock))

    cache_module.fetch_cached("support-reply")

    assert cache_module.fetch_cached("support-reply") == replacement
    assert client.conditional_calls[-1] == ("support-reply", None, '"v1"')


def test_cache_backend_failure_does_not_change_registry_result(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    class FailingCache:
        def get(self, key: str) -> object:
            raise RuntimeError("cache unavailable")

        def set(self, key: str, value: object, timeout: float | None = None) -> None:
            raise RuntimeError("cache unavailable")

    client = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"')])
    )
    monkeypatch.setattr(cache_module, "cache", FailingCache())
    monkeypatch.setattr(cache_module, "get_client", lambda: client)

    assert cache_module.fetch_cached("support-reply") == prompt
    assert len(client.conditional_calls) == 1


def test_invalidation_between_fetch_and_write_cannot_revive_an_old_entry(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"')])
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    generations = iter([("0", "0"), ("0", "invalidated")])
    monkeypatch.setattr(cache_module, "_generations", lambda base_url, slug: next(generations))

    assert cache_module.fetch_cached("support-reply") == prompt
    assert configured_cache._cache == {}


def test_unsuccessful_or_etagless_revalidation_never_returns_a_stale_prompt(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                PromptNotFoundError("prompt was not found"),
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v2"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    clock = iter([100.0, 161.0, 162.0, 163.0])
    monkeypatch.setattr(cache_module, "_now", lambda: next(clock))

    cache_module.fetch_cached("support-reply")
    with pytest.raises(PromptNotFoundError):
        cache_module.fetch_cached("support-reply")
    assert cache_module.fetch_cached("support-reply") == prompt
    assert client.conditional_calls[-1] == ("support-reply", None, None)

    etagless = FakeClient(iter([InvalidResponseError("missing ETag")]))
    monkeypatch.setattr(cache_module, "get_client", lambda: etagless)
    with pytest.raises(InvalidResponseError):
        cache_module.fetch_cached("new-prompt")


def test_post_retention_lookup_omits_the_old_validator(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v2"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    clock = iter([100.0, 221.0])
    monkeypatch.setattr(cache_module, "_now", lambda: next(clock))

    cache_module.fetch_cached("support-reply")
    cache_module.fetch_cached("support-reply")

    assert client.conditional_calls[-1] == ("support-reply", None, None)


@pytest.mark.parametrize(
    "error",
    [
        PromptNotFoundError("deleted"),
        LabelNotFoundError("label moved"),
        NoDeployableVersionError("on-live removed"),
        AuthenticationError("access denied"),
    ],
)
def test_current_unavailable_or_inaccessible_outcomes_never_fall_back_to_stale_data(
    configured_cache: Any,
    monkeypatch: pytest.MonkeyPatch,
    prompt: RetrievedPrompt,
    error: Exception,
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                error,
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    clock = iter([100.0, 161.0])
    monkeypatch.setattr(cache_module, "_now", lambda: next(clock))

    cache_module.fetch_cached("support-reply", label="staging")

    with pytest.raises(type(error)):
        cache_module.fetch_cached("support-reply", label="staging")


def test_zero_ttl_uses_existing_uncached_client_fetch(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter(
            [
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
                ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"'),
            ]
        )
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    monkeypatch.setattr(
        cache_module,
        "get_client_settings",
        lambda: PromptKitSettings.model_validate(
            {
                "BASE_URL": "https://registry.example.com",
                "API_KEY": "not-a-real-secret",
                "CACHE_TTL": 0,
            }
        ),
    )

    cache_module.fetch_cached("support-reply")
    cache_module.fetch_cached("support-reply")

    assert len(client.fetch_calls) == 2
    assert client.conditional_calls == []


def test_zero_ttl_clear_is_a_cache_write_noop(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v1"')])
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    monkeypatch.setattr(
        cache_module,
        "get_client_settings",
        lambda: PromptKitSettings.model_validate(
            {
                "BASE_URL": "https://registry.example.com",
                "API_KEY": "not-a-real-secret",
                "CACHE_TTL": 0,
            }
        ),
    )

    cache_module.clear_prompt_cache()
    cache_module.clear_prompt_cache("support-reply")

    assert configured_cache._cache == {}


def test_malformed_cached_validator_is_a_miss_and_uses_an_unconditional_fetch(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch, prompt: RetrievedPrompt
) -> None:
    client = FakeClient(
        iter([ConditionalFetchResult(not_modified=False, prompt=prompt, etag='"v2"')])
    )
    monkeypatch.setattr(cache_module, "get_client", lambda: client)
    identity = cache_module._identity(client.base_url, "support-reply", None)
    entry_key = cache_module._entry_key(identity, "0", "0")
    configured_cache.set(
        entry_key,
        {
            "identity_version": 1,
            "prompt": prompt.model_dump(mode="json"),
            "etag": "malformed",
            "fresh_until": 9999999999.0,
        },
        timeout=60,
    )

    assert cache_module.fetch_cached("support-reply") == prompt
    assert client.conditional_calls == [("support-reply", None, None)]


def test_cache_helper_uses_registered_lifecycle_state(
    configured_cache: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        cache_module,
        "get_client_settings",
        lambda: (_ for _ in ()).throw(PromptKitDjangoNotInitializedError("not initialized")),
    )

    with pytest.raises(PromptKitDjangoNotInitializedError):
        cache_module.fetch_cached("support-reply")
