"""
Tests for CSRF protection on dashboard mutation routes (US5).
"""

from django.http import HttpResponse
from django.middleware.csrf import CsrfViewMiddleware
from django.test import RequestFactory, TestCase


class DashboardCSRFTests(TestCase):
    def test_post_with_invalid_csrf_token_fails(self) -> None:
        factory = RequestFactory()
        request = factory.post(
            "/dashboard/prompts/create/",
            {"name": "CSRF Prompt", "slug": "csrf-prompt"},
            HTTP_X_CSRFTOKEN="invalid_csrf_token",
        )
        request.COOKIES["csrftoken"] = "cookie_csrf_token"

        middleware = CsrfViewMiddleware(get_response=lambda req: HttpResponse("OK"))
        response = middleware.process_view(request, None, (), {})
        self.assertIsNotNone(response)
        if response:
            self.assertEqual(response.status_code, 403)
