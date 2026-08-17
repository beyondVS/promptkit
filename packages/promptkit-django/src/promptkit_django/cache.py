"""Opt-in Django cache helpers for validator-aware prompt retrieval."""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Mapping
from uuid import uuid4

from django.core.cache import cache
from promptkit import RetrievedPrompt
from promptkit.models import is_valid_entity_tag

from promptkit_django.registry import get_client, get_client_settings

_KEY_PREFIX = "promptkit-django:v1"
_IDENTITY_VERSION = 1


def fetch_cached(slug: str, *, label: str | None = None) -> RetrievedPrompt:
    """Fetch a prompt through the Django default cache when caching is enabled."""
    settings = get_client_settings()
    client = get_client()
    if settings.CACHE_TTL == 0:
        return client.fetch(slug, label=label)

    ttl = settings.CACHE_TTL
    identity = _identity(client.base_url, slug, label)
    global_generation, prompt_generation = _generations(client.base_url, slug)
    entry_key = _entry_key(identity, global_generation, prompt_generation)
    now = _now()
    entry = _decode_entry(_cache_get(entry_key))
    if entry is not None:
        prompt, etag, fresh_until = entry
        if now < fresh_until:
            return prompt
        if now < fresh_until + ttl:
            try:
                result = client.fetch_conditional(slug, label=label, etag=etag)
            except Exception:
                _cache_delete(entry_key)
                raise
            if result.not_modified:
                refreshed = _encode_entry(prompt, result.etag, now + ttl)
                _write_if_current(
                    identity,
                    client.base_url,
                    slug,
                    global_generation,
                    prompt_generation,
                    refreshed,
                    ttl,
                )
                return prompt
            if result.prompt is None:
                raise RuntimeError("conditional prompt result invariant violated")
            _write_if_current(
                identity,
                client.base_url,
                slug,
                global_generation,
                prompt_generation,
                _encode_entry(result.prompt, result.etag, now + ttl),
                ttl,
            )
            return result.prompt

    result = client.fetch_conditional(slug, label=label)
    if result.prompt is None:
        raise RuntimeError("unconditional retrieval must return a prompt")
    _write_if_current(
        identity,
        client.base_url,
        slug,
        global_generation,
        prompt_generation,
        _encode_entry(result.prompt, result.etag, now + ttl),
        ttl,
    )
    return result.prompt


def clear_prompt_cache(slug: str | None = None) -> None:
    """Logically invalidate one prompt or all PromptKit-owned cache entries."""
    if get_client_settings().CACHE_TTL == 0:
        return
    if slug is None:
        _cache_set(_global_generation_key(), uuid4().hex, None)
        return
    client = get_client()
    _cache_set(_prompt_generation_key(client.base_url, slug), uuid4().hex, None)


def _identity(base_url: str, slug: str, label: str | None) -> str:
    """Hash non-secret resolution inputs, preserving omitted-label identity."""
    material = json.dumps(
        {
            "base_url": base_url,
            "slug": slug,
            "label": {"supplied": label is not None, "value": label},
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _generations(base_url: str, slug: str) -> tuple[str, str]:
    return (
        _generation_value(_global_generation_key()),
        _generation_value(_prompt_generation_key(base_url, slug)),
    )


def _generation_value(key: str) -> str:
    value = _cache_get(key)
    return value if isinstance(value, str) and value else "0"


def _global_generation_key() -> str:
    return f"{_KEY_PREFIX}:generation:global"


def _prompt_generation_key(base_url: str, slug: str) -> str:
    digest = hashlib.sha256(f"{base_url}\x00{slug}".encode()).hexdigest()
    return f"{_KEY_PREFIX}:generation:prompt:{digest}"


def _entry_key(identity: str, global_generation: str, prompt_generation: str) -> str:
    return f"{_KEY_PREFIX}:entry:{global_generation}:{prompt_generation}:{identity}"


def _encode_entry(prompt: RetrievedPrompt, etag: str, fresh_until: float) -> dict[str, object]:
    return {
        "identity_version": _IDENTITY_VERSION,
        "prompt": prompt.model_dump(mode="json"),
        "etag": etag,
        "fresh_until": fresh_until,
    }


def _decode_entry(value: object) -> tuple[RetrievedPrompt, str, float] | None:
    if not isinstance(value, Mapping) or value.get("identity_version") != _IDENTITY_VERSION:
        return None
    etag = value.get("etag")
    fresh_until = value.get("fresh_until")
    prompt_payload = value.get("prompt")
    if (
        not isinstance(etag, str)
        or not is_valid_entity_tag(etag)
        or isinstance(fresh_until, bool)
        or not isinstance(fresh_until, int | float)
        or not isinstance(prompt_payload, Mapping)
    ):
        return None
    try:
        return RetrievedPrompt.model_validate(dict(prompt_payload)), etag, float(fresh_until)
    except (TypeError, ValueError):
        return None


def _write_if_current(
    identity: str,
    base_url: str,
    slug: str,
    global_generation: str,
    prompt_generation: str,
    entry: dict[str, object],
    ttl: float,
) -> None:
    current_global, current_prompt = _generations(base_url, slug)
    if (current_global, current_prompt) != (global_generation, prompt_generation):
        return
    _cache_set(_entry_key(identity, global_generation, prompt_generation), entry, timeout=ttl * 2)


def _cache_get(key: str) -> object:
    try:
        return cache.get(key)
    except Exception:
        return None


def _now() -> float:
    """Provide a narrow clock seam for deterministic cache-boundary tests."""
    return time.time()


def _cache_set(key: str, value: object, timeout: float | None) -> None:
    try:
        cache.set(key, value, timeout=timeout)
    except Exception:
        return


def _cache_delete(key: str) -> None:
    try:
        cache.delete(key)
    except Exception:
        return
