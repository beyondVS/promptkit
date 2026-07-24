from django.conf import settings
from django.test import TestCase


class ServerApplicationTestCase(TestCase):
    """Integration test for Django server configuration & app state."""

    server_app_installed: bool

    @classmethod
    def setUpTestData(cls) -> None:
        """Setup class-level test context."""
        cls.server_app_installed = "rest_framework" in settings.INSTALLED_APPS

    def test_django_settings_and_apps(self) -> None:
        """Verify Django settings and required apps are loaded."""
        self.assertTrue(self.server_app_installed)
        self.assertIn("apps.server.config.urls", settings.ROOT_URLCONF)
