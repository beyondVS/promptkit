"""Public exceptions raised by the Django integration."""

from django.core.exceptions import ImproperlyConfigured


class PromptKitDjangoConfigurationError(ImproperlyConfigured):
    """Raised when the ``PROMPTKIT`` settings mapping is invalid."""


class PromptKitDjangoNotInitializedError(ImproperlyConfigured):
    """Raised when no completed PromptKit Django registration is available."""
