from rest_framework import serializers

from core.audit.models import Action


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = [
            "id",
            "user",
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


class UndoRedoSerializer(serializers.Serializer):
    action_id = serializers.IntegerField()
