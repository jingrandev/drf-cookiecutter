from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.audit.models import Action
from core.audit.serializers import ActionSerializer
from core.audit.serializers.action import UndoRedoRequestSerializer
from core.audit.services.handler import ActionHandler
from core.restframework.viewsets import BaseReadOnlyGenericViewSet


@extend_schema(tags=["audit"])
class ActionViewSet(ReadOnlyModelViewSet, BaseReadOnlyGenericViewSet):
    serializer_class = ActionSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["type", "user", "scope", "session"]
    search_fields = ["type", "description", "params"]
    ordering_fields = ["created_at", "updated_at", "id"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Action.objects.select_related("user")

    @extend_schema(
        operation_id="audit_undo",
        request=UndoRedoRequestSerializer,
        responses={status.HTTP_200_OK: ActionSerializer},
    )
    @action(detail=False, methods=["post"], url_path="undo", permission_classes=[IsAuthenticated])
    def undo(self, request):
        serializer = UndoRedoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = ActionHandler.undo(
            user=request.user,
            action_id=serializer.validated_data["action_id"],
        )
        return Response(ActionSerializer(action).data, status=status.HTTP_200_OK)

    @extend_schema(
        operation_id="audit_redo",
        request=UndoRedoRequestSerializer,
        responses={status.HTTP_200_OK: ActionSerializer},
    )
    @action(detail=False, methods=["post"], url_path="redo", permission_classes=[IsAuthenticated])
    def redo(self, request):
        serializer = UndoRedoRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = ActionHandler.redo(
            user=request.user,
            action_id=serializer.validated_data["action_id"],
        )
        return Response(ActionSerializer(action).data, status=status.HTTP_200_OK)
