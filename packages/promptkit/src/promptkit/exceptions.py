"""Public exceptions raised by the PromptKit SDK."""


class PromptKitError(Exception):
    """Base class for every expected SDK error."""


class InvalidConfigurationError(PromptKitError):
    """Raised when client configuration is unsafe or incomplete."""


class InvalidRequestError(PromptKitError):
    """Raised when a prompt retrieval request is invalid locally."""


class AuthenticationError(PromptKitError):
    """Raised when the registry rejects the API key."""


class PromptNotFoundError(PromptKitError):
    """Raised when the requested prompt slug does not exist."""


class NoDeployableVersionError(PromptKitError):
    """Raised when a prompt has no version available for retrieval."""


class LabelNotFoundError(PromptKitError):
    """Raised when the requested published label does not exist."""


class InvalidLabelError(InvalidRequestError):
    """Raised when a requested label is invalid or reserved."""


class RateLimitError(PromptKitError):
    """Raised when the registry rate-limits a request."""


class RedirectError(PromptKitError):
    """Raised when the registry responds with a redirect."""


class CommunicationError(PromptKitError):
    """Raised when the SDK cannot safely communicate with the registry."""


class InvalidResponseError(PromptKitError):
    """Raised when the registry response cannot satisfy the SDK contract."""
