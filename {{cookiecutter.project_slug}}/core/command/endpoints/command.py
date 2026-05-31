from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.command.models import Command
from core.command.serializers import CommandSerializer
from core.command.serializers.command import UndoRedoRequestSerializer
from core.command.services.handler import CommandHandler
from core.restframework.viewsets import BaseReadOnlyGenericViewSet


@extend_schema(tags=["audit"])
class CommandViewSet(ReadOnlyModelViewSet, BaseReadOnlyGenericViewSet):
    serializer_class = CommandSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["type", "user", "scope", "session"]
    search_fields = ["type", "description", "params"]
    ordering_fields = ["created_at", "updated_at", "id"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Command.objects.select_related("user")

    @extend_schema(
        operation_id="audit_command_undo",
        request=UndoRedoRequestSerializer,
        responses={status.HTTP_200_OK: CommandSerializer},
    )
    @action(detail=False, methods=["post"], url_path="undo", permission_classes=[IsAuthenticated])
    def undo(self, request):
        serializer = UndoRedoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = CommandHandler.undo(
            user=request.user,
            command_id=serializer.validated_data["command_id"],
        )
        return Response(CommandSerializer(command).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="audit_command_redo",
        request=UndoRedoRequestSerializer,
        responses={status.HTTP_200_OK: CommandSerializer},
    )
    @action(detail=False, methods=["post"], url_path="redo", permission_classes=[IsAuthenticated])
    def redo(self, request):
        serializer = UndoRedoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command = CommandHandler.redo(
            user=request.user,
            command_id=serializer.validated_data["command_id"],
        )
        return Response(CommandSerializer(command).data, status=status.HTTP_200_OK)
