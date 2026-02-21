from unittest.mock import patch

from typing import Any

from django.test import override_settings
from rest_framework.exceptions import NotAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

from core.restframework.error_handler import handle_exception


class ErrorHandlerTests(APITestCase):
    def setUp(self) -> None:
        super().setUp()
        self.factory = APIRequestFactory()

    def get_request_context(self) -> dict[str, Any]:
        request = self.factory.get("/api/example/")
        return {"request": request}

    def test_validation_error_returns_normalized_errors(self) -> None:
        exc = ValidationError({"name": ["required"]})

        response = handle_exception(exc, self.get_request_context())

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "REQ_1001")
        self.assertEqual(
            response.data["data"],
            {"errors": {"name": ["required"]}},
        )

    def test_not_authenticated_prefers_exception_detail(self) -> None:
        exc = NotAuthenticated(detail="token missing")

        response = handle_exception(exc, self.get_request_context())

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "AUTH_1000")
        self.assertEqual(response.data["message"], "token missing")
        self.assertEqual(
            response.data["data"],
            {"errors": {"detail": "token missing"}},
        )

    @override_settings(PROPAGATE_API_EXCEPTIONS=False)
    def test_unhandled_exception_falls_back_to_sys_5000(self) -> None:
        exc = RuntimeError("boom")
        context = self.get_request_context()

        with patch("core.restframework.error_handler.logger") as mock_logger:
            mock_logger.opt.return_value = mock_logger

            response = handle_exception(exc, context)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["code"], "SYS_5000")
        self.assertTrue(mock_logger.opt.called)
