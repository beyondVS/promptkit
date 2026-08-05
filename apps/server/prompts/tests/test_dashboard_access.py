"""
Tests for public landing page, login redirection, staff auth, and non-staff rejection.
"""

from django.contrib.auth.models import User
from django.test import TestCase


class DashboardAccessTests(TestCase):
    def test_public_landing_page_accessible(self) -> None:
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("PromptKit", res.content.decode())

    def test_unauthenticated_dashboard_redirects_to_login(self) -> None:
        res = self.client.get("/dashboard/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/dashboard/login/", res.url)

    def test_non_staff_user_dashboard_access_rejected(self) -> None:
        User.objects.create_user(username="regular_user", password="password")
        self.client.login(username="regular_user", password="password")
        res = self.client.get("/dashboard/")
        self.assertIn(res.status_code, [302, 403])

    def test_staff_user_dashboard_access_granted(self) -> None:
        User.objects.create_superuser(username="staff_user", password="password")
        self.client.login(username="staff_user", password="password")
        res = self.client.get("/dashboard/")
        self.assertEqual(res.status_code, 200)
