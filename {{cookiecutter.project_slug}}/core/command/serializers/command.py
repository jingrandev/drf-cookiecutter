from rest_framework import serializers

from core.command.models import Command


class CommandSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user_id", read_only=True, default=None)

    class Meta:
        model = Command
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
            "command_group",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UndoRedoRequestSerializer(serializers.Serializer):
    command_id = serializers.IntegerField()
