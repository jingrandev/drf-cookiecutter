from rest_framework import serializers


class EmailStatusRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class EmailStatusResponseSerializer(serializers.Serializer):
    is_whitelisted = serializers.BooleanField()
    has_account = serializers.BooleanField()


class SendCodeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class SendCodeResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    expires_in = serializers.IntegerField(required=False)


class VerifyCodeRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()


class VerifyCodeResponseSerializer(serializers.Serializer):
    is_valid = serializers.BooleanField()
    verification_token = serializers.CharField(required=False, allow_blank=True)


class SetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_token = serializers.CharField()
    password = serializers.CharField()


class SetPasswordResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class LoginRequestSerializer(serializers.Serializer):
    {%- if cookiecutter.username_type == "email" %}
    email = serializers.EmailField(required=True, allow_blank=False)
    {%- else %}
    username = serializers.CharField(required=True, allow_blank=False)
    {%- endif %}
    password = serializers.CharField(required=True, allow_blank=False, write_only=True)


class RefreshResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class LogoutResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
