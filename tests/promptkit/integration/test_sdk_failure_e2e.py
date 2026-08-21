"""Real-HTTP failure-resilience coverage for the public PromptKit SDK."""

from __future__ import annotations

import logging
import socket
import threading
import traceback
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Any, NoReturn

import httpx
import pytest
from django.conf import LazySettings
from promptkit import (
    AuthenticationError,
    CommunicationError,
    InvalidConfigurationError,
    InvalidVariableTypeError,
    LiteLLMAdapter,
    MissingVariableError,
    PromptKitClient,
    PromptKitError,
    RetrievedPrompt,
    UnexpectedVariableError,
)

from apps.server.prompts.models import PromptCategory, Section, VariableDefinition
from apps.server.prompts.services.lifecycle import (
    create_prompt_with_initial_draft,
    publish_version,
    set_on_live_version,
)

pytestmark = pytest.mark.django_db(transaction=True)

ACCEPTED_API_KEY = "accepted-api-key-sentinel"
REJECTED_API_KEY = "rejected-api-key-sentinel"
AUTHORIZATION_SENTINEL = f"X-PromptKit-Api-Key: {REJECTED_API_KEY}"
VARIABLE_SENTINEL = "variable-value-sentinel"
TEMPLATE_SENTINEL = "template-content-sentinel"
PROMPT_SLUG = "failure-resilience-prompt"


@dataclass
class ManagedRegistry:
    base_url: str
    slug: str


@dataclass
class DisconnectingEndpoint:
    base_url: str
    listener: socket.socket
    stopped: threading.Event
    first_connection_closed: threading.Event
    connections: list[tuple[str, int]]
    thread: threading.Thread


class CapturingHandler(logging.Handler):
    """Collect application-owned diagnostic records without global configuration."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class FailingHandler(logging.Handler):
    """Model an application handler failure after an SDK exception is caught."""

    def emit(self, record: logging.LogRecord) -> NoReturn:
        raise RuntimeError("application diagnostic sink failed")


@pytest.fixture
def configured_api_key(settings: LazySettings) -> str:
    settings.PROMPTKIT_API_KEY = ACCEPTED_API_KEY
    return ACCEPTED_API_KEY


@pytest.fixture
def published_prompt() -> str:
    category = PromptCategory.objects.create(
        name="Failure resilience",
        slug="failure-resilience",
        description="Test-only category for SDK failure resilience.",
    )
    prompt, draft = create_prompt_with_initial_draft(
        category=category,
        name="Failure resilience prompt",
        slug=PROMPT_SLUG,
        description="Test-only prompt fixture.",
    )
    draft.template_text = (
        f"{TEMPLATE_SENTINEL} customer={{{{ customer_name }}}} count={{{{ ticket_count }}}}"
    )
    draft.save(update_fields=["template_text"])
    Section.objects.create(
        version=draft,
        role=Section.Role.SYSTEM,
        order=0,
        content="Handle {{ customer_name }} with ticket {{ ticket_count }}.",
    )
    Section.objects.create(
        version=draft,
        role=Section.Role.USER,
        order=1,
        content="Customer {{ customer_name }} needs help.",
    )
    VariableDefinition.objects.create(
        version=draft,
        name="customer_name",
        var_type=VariableDefinition.VarType.STRING,
    )
    VariableDefinition.objects.create(
        version=draft,
        name="ticket_count",
        var_type=VariableDefinition.VarType.NUMBER,
    )
    published = publish_version(draft.id)
    set_on_live_version(prompt, published.version_number)
    return prompt.slug


@pytest.fixture
def ready_registry(
    configured_api_key: str,
    live_server: Any,
    published_prompt: str,
) -> ManagedRegistry:
    with httpx.Client(timeout=1.0, trust_env=False) as health_client:
        response = health_client.get(f"{live_server.url}/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "promptkit-server"}
    return ManagedRegistry(base_url=live_server.url, slug=published_prompt)


@pytest.fixture
def retrieved_prompt(ready_registry: ManagedRegistry) -> RetrievedPrompt:
    client = PromptKitClient(ready_registry.base_url, ACCEPTED_API_KEY, timeout=1.0)
    try:
        return client.fetch(ready_registry.slug)
    finally:
        client.close()


@pytest.fixture
def refused_endpoint() -> Iterator[str]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    host, port = listener.getsockname()
    try:
        yield f"http://{host}:{port}"
    finally:
        listener.close()


@pytest.fixture
def accept_then_close_endpoint() -> Iterator[DisconnectingEndpoint]:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.settimeout(0.05)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    host, port = listener.getsockname()
    stopped = threading.Event()
    first_connection_closed = threading.Event()
    connections: list[tuple[str, int]] = []

    def serve() -> None:
        while not stopped.is_set():
            try:
                connection, address = listener.accept()
            except TimeoutError:
                continue
            except OSError:
                return
            connections.append(address)
            try:
                connection.recv(4096)
            finally:
                connection.close()
                first_connection_closed.set()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    endpoint = DisconnectingEndpoint(
        base_url=f"http://{host}:{port}",
        listener=listener,
        stopped=stopped,
        first_connection_closed=first_connection_closed,
        connections=connections,
        thread=thread,
    )
    try:
        yield endpoint
    finally:
        stopped.set()
        listener.close()
        thread.join(timeout=1.0)


def _logger_state() -> dict[str, tuple[tuple[int, ...], int, bool, bool]]:
    root_logger = logging.getLogger()
    state = {
        "": (
            tuple(id(handler) for handler in root_logger.handlers),
            root_logger.level,
            root_logger.propagate,
            root_logger.disabled,
        )
    }
    for name, candidate in logging.Logger.manager.loggerDict.items():
        if not (name == "promptkit" or name.startswith("promptkit.")):
            continue
        if not isinstance(candidate, logging.Logger):
            continue
        logger = candidate
        state[name] = (
            tuple(id(handler) for handler in logger.handlers),
            logger.level,
            logger.propagate,
            logger.disabled,
        )
    return state


def _assert_no_protected_values(value: object) -> None:
    rendered = str(value)
    for sentinel in (
        ACCEPTED_API_KEY,
        REJECTED_API_KEY,
        AUTHORIZATION_SENTINEL,
        VARIABLE_SENTINEL,
        TEMPLATE_SENTINEL,
    ):
        assert sentinel not in rendered


def _assert_safe_exception(error: PromptKitError) -> None:
    _assert_no_protected_values(error)
    _assert_no_protected_values("".join(traceback.format_exception(error)))


def _run_fetch(client: PromptKitClient, slug: str) -> RetrievedPrompt:
    try:
        return client.fetch(slug)
    finally:
        client.close()


def _capture_scoped_failure(
    caplog: pytest.LogCaptureFixture,
    action: Callable[[], object],
    expected_error: type[PromptKitError],
) -> PromptKitError:
    before = _logger_state()
    caplog.clear()
    with pytest.raises(expected_error) as raised:
        action()
    error = raised.value

    assert _logger_state() == before
    sdk_records = [
        record
        for record in caplog.records
        if record.name == "promptkit" or record.name.startswith("promptkit.")
    ]
    assert sdk_records == []
    _assert_safe_exception(error)
    return error


def _write_application_record(error: PromptKitError) -> list[str]:
    logger = logging.getLogger("application.promptkit_failure_e2e")
    handler = CapturingHandler()
    previous_handlers = list(logger.handlers)
    previous_level = logger.level
    previous_propagate = logger.propagate
    logger.handlers = [handler]
    logger.setLevel(logging.ERROR)
    logger.propagate = False
    try:
        logger.error("failure_type=%s message=%s", type(error).__name__, str(error))
    finally:
        logger.handlers = previous_handlers
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate
    return [record.getMessage() for record in handler.records]


def _assert_compilation_failure(
    prompt: RetrievedPrompt,
    params: dict[str, object],
    expected_error: type[PromptKitError],
    expected_message_part: str,
    monkeypatch: pytest.MonkeyPatch,
) -> PromptKitError:
    downstream_calls: list[object] = []
    compiled: object | None = None

    def downstream_spy(value: object) -> NoReturn:
        downstream_calls.append(value)
        raise AssertionError("downstream conversion must not run after failed compilation")

    monkeypatch.setattr(LiteLLMAdapter, "to_completion_args", staticmethod(downstream_spy))
    with pytest.raises(expected_error) as raised:
        compiled = prompt.compile(params)
        LiteLLMAdapter.to_completion_args(compiled)

    assert compiled is None
    assert downstream_calls == []
    assert expected_message_part in str(raised.value)
    _assert_safe_exception(raised.value)
    return raised.value


def test_real_http_registry_is_ready_and_retrieves_an_on_live_prompt(
    ready_registry: ManagedRegistry,
) -> None:
    prompt = _run_fetch(
        PromptKitClient(ready_registry.base_url, ACCEPTED_API_KEY, timeout=1.0),
        ready_registry.slug,
    )

    assert prompt.slug == ready_registry.slug
    assert prompt.is_on_live is True
    assert prompt.version_status == "published"


@pytest.mark.parametrize("api_key", ["", "   "])
def test_blank_api_key_is_a_local_configuration_failure_without_http_client_creation(
    monkeypatch: pytest.MonkeyPatch,
    api_key: str,
) -> None:
    def fail_http_client(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("blank API key must not construct an HTTP client")

    monkeypatch.setattr("promptkit.client.httpx.Client", fail_http_client)

    with pytest.raises(InvalidConfigurationError) as raised:
        PromptKitClient("http://127.0.0.1:1", api_key)

    _assert_safe_exception(raised.value)


def test_refused_loopback_endpoint_is_a_no_retry_communication_failure(
    refused_endpoint: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = _capture_scoped_failure(
        caplog,
        lambda: _run_fetch(
            PromptKitClient(refused_endpoint, ACCEPTED_API_KEY, timeout=0.2), PROMPT_SLUG
        ),
        CommunicationError,
    )

    assert "communicate" in str(error)


def test_mid_request_disconnect_is_a_no_retry_communication_failure(
    accept_then_close_endpoint: DisconnectingEndpoint,
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = _capture_scoped_failure(
        caplog,
        lambda: _run_fetch(
            PromptKitClient(accept_then_close_endpoint.base_url, ACCEPTED_API_KEY, timeout=1.0),
            PROMPT_SLUG,
        ),
        CommunicationError,
    )

    assert accept_then_close_endpoint.first_connection_closed.wait(timeout=1.0)
    assert len(accept_then_close_endpoint.connections) == 1
    assert "communicate" in str(error)


def test_rejected_nonempty_key_over_real_http_is_an_authentication_failure(
    ready_registry: ManagedRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = _capture_scoped_failure(
        caplog,
        lambda: _run_fetch(
            PromptKitClient(ready_registry.base_url, REJECTED_API_KEY, timeout=1.0),
            ready_registry.slug,
        ),
        AuthenticationError,
    )

    assert "rejected" in str(error)


@pytest.mark.parametrize(
    ("params", "error_type", "message_part"),
    [
        ({"ticket_count": 3}, MissingVariableError, "customer_name"),
        (
            {"customer_name": "Ada", "ticket_count": 3, "unexpected": VARIABLE_SENTINEL},
            UnexpectedVariableError,
            "unexpected",
        ),
        (
            {"customer_name": "Ada", "ticket_count": VARIABLE_SENTINEL},
            InvalidVariableTypeError,
            "ticket_count",
        ),
    ],
    ids=["missing", "unexpected", "invalid-type"],
)
def test_real_http_retrieved_prompt_rejects_invalid_variables_atomically(
    retrieved_prompt: RetrievedPrompt,
    params: dict[str, object],
    error_type: type[PromptKitError],
    message_part: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _assert_compilation_failure(
        retrieved_prompt,
        params,
        error_type,
        message_part,
        monkeypatch,
    )


def test_application_owned_logging_records_only_safe_exception_metadata(
    ready_registry: ManagedRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    error = _capture_scoped_failure(
        caplog,
        lambda: _run_fetch(
            PromptKitClient(ready_registry.base_url, REJECTED_API_KEY, timeout=1.0),
            ready_registry.slug,
        ),
        AuthenticationError,
    )

    records = _write_application_record(error)
    assert len(records) == 1
    assert "AuthenticationError" in records[0]
    _assert_no_protected_values(records[0])


def test_scoped_failures_remain_log_free_across_three_same_process_runs(
    ready_registry: ManagedRegistry,
    refused_endpoint: str,
    retrieved_prompt: RetrievedPrompt,
    caplog: pytest.LogCaptureFixture,
) -> None:
    for _ in range(3):
        failures: tuple[tuple[Callable[[], object], type[PromptKitError]], ...] = (
            (
                lambda: PromptKitClient("http://127.0.0.1:1", ""),
                InvalidConfigurationError,
            ),
            (
                lambda: _run_fetch(
                    PromptKitClient(refused_endpoint, ACCEPTED_API_KEY, timeout=0.2), PROMPT_SLUG
                ),
                CommunicationError,
            ),
            (
                lambda: _run_fetch(
                    PromptKitClient(ready_registry.base_url, REJECTED_API_KEY, timeout=1.0),
                    ready_registry.slug,
                ),
                AuthenticationError,
            ),
            (
                lambda: retrieved_prompt.compile({"ticket_count": 3}),
                MissingVariableError,
            ),
            (
                lambda: retrieved_prompt.compile(
                    {
                        "customer_name": "Ada",
                        "ticket_count": 3,
                        "unexpected": VARIABLE_SENTINEL,
                    }
                ),
                UnexpectedVariableError,
            ),
            (
                lambda: retrieved_prompt.compile(
                    {"customer_name": "Ada", "ticket_count": VARIABLE_SENTINEL}
                ),
                InvalidVariableTypeError,
            ),
        )
        for action, expected_error in failures:
            error = _capture_scoped_failure(caplog, action, expected_error)
            records = _write_application_record(error)
            assert len(records) == 1
            _assert_no_protected_values(records[0])


def test_application_handler_failure_does_not_replace_an_already_caught_sdk_exception() -> None:
    with pytest.raises(InvalidConfigurationError) as raised:
        PromptKitClient("http://127.0.0.1:1", "")
    error = raised.value
    logger = logging.getLogger("application.promptkit_failure_e2e.failing")
    handler = FailingHandler()
    previous_handlers = list(logger.handlers)
    previous_propagate = logger.propagate
    logger.handlers = [handler]
    logger.propagate = False
    try:
        with pytest.raises(RuntimeError, match="diagnostic sink failed"):
            logger.error("failure_type=%s message=%s", type(error).__name__, str(error))
    finally:
        logger.handlers = previous_handlers
        logger.propagate = previous_propagate

    assert isinstance(error, InvalidConfigurationError)
    assert "api_key" in str(error)
    _assert_safe_exception(error)
