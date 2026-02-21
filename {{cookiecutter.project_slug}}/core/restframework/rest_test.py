from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.db import IntegrityError
from django.urls import reverse
from rest_framework.test import APITestCase


class BaseAPITestCase(APITestCase):
    DEFAULT_AUTH_USER_ID = 123
    {%- if cookiecutter.username_type == "email" %}
    DEFAULT_AUTH_EMAIL = "authed@example.com"
    {%- else %}
    DEFAULT_AUTH_USERNAME = "authed"
    {%- endif %}
    DEFAULT_AUTH_PASSWORD = "Password123!"

    AUTH_LOGIN_URL_NAME = "auth-login"
    AUTH_LOGOUT_URL_NAME = "auth-logout"

    DEFAULT_URL_NAMESPACE = "api:v1"

    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)
        self.user: AbstractBaseUser | None = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def reverse_url(
        self,
        viewname: str,
        *,
        kwargs: dict[str, Any] | None = None,
        namespace: str | None = None,
    ) -> str:
        if ":" not in viewname:
            effective_namespace = (
                self.DEFAULT_URL_NAMESPACE if namespace is None else namespace
            )
            if effective_namespace:
                viewname = f"{effective_namespace}:{viewname}"
        return reverse(viewname, kwargs=kwargs)

    def create_user(
        self,
        *,
        {%- if cookiecutter.username_type == "email" %}
        email: str,
        {%- else %}
        username: str,
        {%- endif %}
        password: str,
        user_id: int | None = None,
        **extra_fields: Any,
    ):
        User = get_user_model()
        create_kwargs: dict[str, Any] = {**extra_fields}
        {%- if cookiecutter.username_type == "email" %}
        create_kwargs["email"] = email
        {%- else %}
        create_kwargs["username"] = username
        {%- endif %}

        if user_id is not None:
            try:
                return User.objects.create_user(
                    id=user_id,
                    password=password,
                    **create_kwargs,
                )
            except IntegrityError:
                pass

        {%- if cookiecutter.username_type == "email" %}
        lookup_kwargs = {"email": email}
        {%- else %}
        lookup_kwargs = {"username": username}
        {%- endif %}
        user, _ = User.objects.get_or_create(defaults=extra_fields, **lookup_kwargs)
        user.set_password(password)
        user.save()
        return user

    def set_current_user(self, user=None) -> None:
        if user is None:
            if self.user is None:
                raise AssertionError("self.user is not set")
            user = self.user
        self.client.force_authenticate(user=user)

    def clear_current_user(self) -> None:
        self.client.force_authenticate(user=None)
        self.client.cookies.clear()

    def login(
        self,
        *,
        {%- if cookiecutter.username_type == "email" %}
        email: str,
        {%- else %}
        username: str,
        {%- endif %}
        password: str,
    ):
        response = self.client.post(
            self.reverse_url(self.AUTH_LOGIN_URL_NAME),
            data={
                {%- if cookiecutter.username_type == "email" %}
                "email": email,
                {%- else %}
                "username": username,
                {%- endif %}
                "password": password,
            },
            format="json",
        )
        self.assert_api_success(response)
        return response

    def logout(self):
        response = self.client.post(
            self.reverse_url(self.AUTH_LOGOUT_URL_NAME),
            data={},
            format="json",
        )
        self.assert_api_success(response)
        return response

    def assert_api_success(self, response, *, http_status: int = 200) -> dict[str, Any]:
        self.assertEqual(
            response.status_code,
            http_status,
            getattr(response, "data", None),
        )
        payload = response.json()
        self.assertIn("code", payload)
        self.assertIn("data", payload)
        self.assertIn("message", payload)
        self.assertEqual(payload["code"], 0)
        return payload

    def assert_api_error(
        self,
        response,
        *,
        http_status: int = 400,
        code: str | None = None,
    ) -> dict[str, Any]:
        self.assertEqual(
            response.status_code,
            http_status,
            getattr(response, "data", None),
        )
        payload = response.json()
        self.assertIn("code", payload)
        self.assertIn("data", payload)
        self.assertIn("message", payload)
        self.assertNotEqual(payload["code"], 0)
        if code is not None:
            self.assertEqual(payload["code"], code)
        return payload

    def setUp(self):
        super().setUp()
        self.user = self.create_user(
            user_id=self.DEFAULT_AUTH_USER_ID,
            {%- if cookiecutter.username_type == "email" %}
            email=self.DEFAULT_AUTH_EMAIL,
            {%- else %}
            username=self.DEFAULT_AUTH_USERNAME,
            {%- endif %}
            password=self.DEFAULT_AUTH_PASSWORD,
        )
