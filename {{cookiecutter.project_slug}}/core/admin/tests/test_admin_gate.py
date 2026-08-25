from constance.test.unittest import override_config
from django.test import Client
from django.test import TestCase

from core.admin.middleware import SESSION_KEY


@override_config(ADMIN_SECURITY_CODE="")
class AdminGateDisabledTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = Client()

    def test_admin_redirects_to_login_when_gate_disabled(self) -> None:
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/admin/login/"))


@override_config(ADMIN_SECURITY_CODE="s3cret-token")
class AdminGateEnabledTests(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.client = Client()

    def test_admin_returns_404_without_unlock(self) -> None:
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_admin_subpaths_return_404_without_unlock(self) -> None:
        self.assertEqual(self.client.get("/admin/login/").status_code, 404)

    def test_unlock_with_wrong_token_returns_404(self) -> None:
        self.assertEqual(self.client.get("/admin/wrong-token/").status_code, 404)

    def test_unlock_with_correct_token_redirects_to_admin(self) -> None:
        response = self.client.get("/admin/s3cret-token/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")
        self.assertTrue(self.client.session.get(SESSION_KEY))

    def test_admin_accessible_after_unlock(self) -> None:
        self.client.get("/admin/s3cret-token/")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/admin/login/"))

    def test_unlock_without_trailing_slash(self) -> None:
        response = self.client.get("/admin/s3cret-token")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")

    def test_non_admin_paths_unaffected(self) -> None:
        response = self.client.get("/api/v1/health/")
        self.assertNotEqual(response.status_code, 404)
