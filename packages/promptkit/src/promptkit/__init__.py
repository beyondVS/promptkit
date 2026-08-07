"""Framework-agnostic, read-only client for the PromptKit registry."""

from promptkit.client import PromptKitClient
from promptkit.exceptions import (
    AuthenticationError,
    CommunicationError,
    InvalidConfigurationError,
    InvalidLabelError,
    InvalidRequestError,
    InvalidResponseError,
    LabelNotFoundError,
    NoDeployableVersionError,
    PromptKitError,
    PromptNotFoundError,
    RateLimitError,
    RedirectError,
)
from promptkit.models import PromptCategory, PromptSection, PromptVariable, RetrievedPrompt

__all__ = [
    "PromptCategory",
    "PromptKitClient",
    "PromptKitError",
    "PromptNotFoundError",
    "PromptSection",
    "PromptVariable",
    "RateLimitError",
    "RedirectError",
    "RetrievedPrompt",
    "AuthenticationError",
    "CommunicationError",
    "InvalidConfigurationError",
    "InvalidLabelError",
    "InvalidRequestError",
    "InvalidResponseError",
    "LabelNotFoundError",
    "NoDeployableVersionError",
]
