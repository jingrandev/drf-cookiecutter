from constance.test.unittest import override_config
from django.test import Client
from django.test import TestCase


@override_config(MAINTENANCE_MODE=False)
class MaintenanceModeDisabledTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = Client()

    def test_api_accessible_when_maintenance_off(self) -> None:
        response = self.client.get("/api/v1/health/")
        self.assertNotEqual(response.status_code, 503)


@override_config(MAINTENANCE_MODE=True)
class MaintenanceModeEnabledTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = Client()

    def test_api_returns_503_with_envelope(self) -> None:
        response = self.client.get("/api/v1/auth/login/")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"code": "SYS_4503", "data": {}, "message": "service under maintenance"},
        )

    def test_admin_not_blocked(self) -> None:
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 503)

    def test_health_probe_not_blocked(self) -> None:
        response = self.client.get("/api/v1/health/")
        self.assertNotEqual(response.status_code, 503)
