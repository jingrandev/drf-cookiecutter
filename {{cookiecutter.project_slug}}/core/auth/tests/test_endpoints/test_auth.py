from unittest import mock

from django.conf import settings

from core.restframework.rest_test import BaseAPITestCase


class TestAuthEndpoints(BaseAPITestCase):
    def get_cookie_names(self) -> tuple[str, str]:
        access_name = getattr(settings, "AUTH_COOKIE_ACCESS_NAME", "access")
        refresh_name = getattr(settings, "AUTH_COOKIE_REFRESH_NAME", "refresh")
        return access_name, refresh_name

    def test_login_success_sets_cookies(self):
        response = self.login(
            {%- if cookiecutter.username_type == "email" %}
            email=self.DEFAULT_AUTH_EMAIL,
            {%- else %}
            username=self.DEFAULT_AUTH_USERNAME,
            {%- endif %}
            password=self.DEFAULT_AUTH_PASSWORD,
        )

        payload = response.json()
        access_name, refresh_name = self.get_cookie_names()
        self.assertIn(access_name, response.cookies)
        self.assertIn(refresh_name, response.cookies)

        self.assertIn("id", payload["data"])

    def test_login_invalid_credentials_returns_error(self):
        response = self.client.post(
            self.reverse_url(self.AUTH_LOGIN_URL_NAME),
            data={
                {%- if cookiecutter.username_type == "email" %}
                "email": self.DEFAULT_AUTH_EMAIL,
                {%- else %}
                "username": self.DEFAULT_AUTH_USERNAME,
                {%- endif %}
                "password": "wrong",
            },
            format="json",
        )

        self.assert_api_error(response, http_status=401, code="AUTH_1001")

    def test_login_validation_error_missing_password(self):
        response = self.client.post(
            self.reverse_url(self.AUTH_LOGIN_URL_NAME),
            data={
                {%- if cookiecutter.username_type == "email" %}
                "email": self.DEFAULT_AUTH_EMAIL,
                {%- else %}
                "username": self.DEFAULT_AUTH_USERNAME,
                {%- endif %}
            },
            format="json",
        )

        self.assert_api_error(response, http_status=400, code="REQ_1001")

    def test_logout_clears_cookies(self):
        self.login(
            {%- if cookiecutter.username_type == "email" %}
            email=self.DEFAULT_AUTH_EMAIL,
            {%- else %}
            username=self.DEFAULT_AUTH_USERNAME,
            {%- endif %}
            password=self.DEFAULT_AUTH_PASSWORD,
        )

        response = self.logout()

        access_name, refresh_name = self.get_cookie_names()
        self.assertIn(access_name, response.cookies)
        self.assertIn(refresh_name, response.cookies)
        self.assertIn(response.cookies[access_name]["max-age"], {0, "0"})
        self.assertIn(response.cookies[refresh_name]["max-age"], {0, "0"})

    def test_logout_without_login_is_ok(self):
        self.clear_current_user()

        response = self.logout()

        self.assert_api_success(response)

        access_name, refresh_name = self.get_cookie_names()
        self.assertIn(access_name, response.cookies)
        self.assertIn(refresh_name, response.cookies)
        self.assertIn(response.cookies[access_name]["max-age"], {0, "0"})
        self.assertIn(response.cookies[refresh_name]["max-age"], {0, "0"})

    def test_refresh_without_cookie_returns_error(self):
        self.clear_current_user()
        url = self.reverse_url("auth-refresh")
        response = self.client.post(url, data={}, format="json")

        self.assert_api_error(response, http_status=401, code="AUTH_1003")

    def test_refresh_with_invalid_cookie_returns_error(self):
        self.login(
            {%- if cookiecutter.username_type == "email" %}
            email=self.DEFAULT_AUTH_EMAIL,
            {%- else %}
            username=self.DEFAULT_AUTH_USERNAME,
            {%- endif %}
            password=self.DEFAULT_AUTH_PASSWORD,
        )

        _, refresh_name = self.get_cookie_names()
        self.client.cookies[refresh_name] = "invalid"

        response = self.client.post(
            self.reverse_url("auth-refresh"),
            data={},
            format="json",
        )

        self.assert_api_error(response, http_status=401, code="AUTH_1003")

    def test_refresh_after_login_sets_cookies(self):
        login_response = self.login(
            {%- if cookiecutter.username_type == "email" %}
            email=self.DEFAULT_AUTH_EMAIL,
            {%- else %}
            username=self.DEFAULT_AUTH_USERNAME,
            {%- endif %}
            password=self.DEFAULT_AUTH_PASSWORD,
        )
        access_name, refresh_name = self.get_cookie_names()

        self.assertIn(access_name, login_response.cookies)
        self.assertIn(refresh_name, login_response.cookies)

        url = self.reverse_url("auth-refresh")
        response = self.client.post(url, data={}, format="json")
        self.assert_api_success(response)

        self.assertIn(access_name, response.cookies)
        self.assertIn(refresh_name, response.cookies)
        self.assertTrue(response.cookies[access_name].value)
        self.assertTrue(response.cookies[refresh_name].value)


class TestAuthEndpointsCookieNames(BaseAPITestCase):
    def test_login_uses_configured_cookie_names(self):
        access_cookie_name = "test-access"
        refresh_cookie_name = "test-refresh"

        with mock.patch.object(
            settings,
            "AUTH_COOKIE_ACCESS_NAME",
            access_cookie_name,
            create=True,
        ), mock.patch.object(
            settings,
            "AUTH_COOKIE_REFRESH_NAME",
            refresh_cookie_name,
            create=True,
        ):
            response = self.login(
                {%- if cookiecutter.username_type == "email" %}
                email=self.DEFAULT_AUTH_EMAIL,
                {%- else %}
                username=self.DEFAULT_AUTH_USERNAME,
                {%- endif %}
                password=self.DEFAULT_AUTH_PASSWORD,
            )
            self.assertIn(access_cookie_name, response.cookies)
            self.assertIn(refresh_cookie_name, response.cookies)
