from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = self.get_raw_token_from_cookie(request)
        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token

    def get_raw_token_from_cookie(self, request):
        cookie_name = getattr(settings, "AUTH_COOKIE_ACCESS_NAME", "access")
        raw_token = request.COOKIES.get(cookie_name)
        if raw_token:
            return raw_token
        return None
