from rest_framework import serializers

from core.audit.models import Action


class ActionSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user_id", read_only=True, default=None)

    class Meta:
        model = Action
        fields = [
            "id",
            "user_id",
            "type",
            "params",
            "scope",
            "description",
            "session",
            "undone_at",
            "error",
            "action_group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UndoRedoRequestSerializer(serializers.Serializer):
    action_id = serializers.IntegerField()
