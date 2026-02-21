from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    """
    Custom user create serializer for Djoser.
    """

    class Meta(BaseUserCreateSerializer.Meta):
        model = User

        {% if cookiecutter.username_type == "email" %}
        fields = ["id", "email", "name", "password"]
        {% else %}
        fields = ["id", "username", "email", "name", "password"]
        {% endif %}


class UserSerializer(BaseUserSerializer):
    """
    Custom user serializer for Djoser.
    """

    class Meta(BaseUserSerializer.Meta):
        model = User

        {%- if cookiecutter.username_type == "email" %}
        fields = [
            "id",
            "email",
            "name",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
        ]
        {%- else %}
        fields = [
            "id",
            "username",
            "email",
            "name",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
        ]
        {%- endif %}
        read_only_fields = ["id", "is_active", "is_staff"]
