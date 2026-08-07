from collections.abc import Callable
from typing import Any

import httpx
import pytest


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def prompt_payload() -> dict[str, Any]:
    return {
        "slug": "support-reply",
        "name": "Support reply",
        "description": "A customer support response.",
        "category": {"name": "Support", "slug": "support"},
        "version": 4,
        "version_status": "published",
        "is_on_live": True,
        "label": "latest",
        "template_text": "Hello {{ customer_name }}!",
        "variables": [
            {
                "name": "customer_name",
                "var_type": "string",
                "required": True,
                "default_value": None,
                "description": "Customer name",
            }
        ],
        "sections": [{"role": "user", "order": 0, "content": "Hello {{ customer_name }}!"}],
        "created_at": "2026-08-07T00:00:00Z",
    }


@pytest.fixture
def mock_transport() -> Callable[[Callable[[httpx.Request], httpx.Response]], httpx.MockTransport]:
    def build(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
        return httpx.MockTransport(handler)

    return build
