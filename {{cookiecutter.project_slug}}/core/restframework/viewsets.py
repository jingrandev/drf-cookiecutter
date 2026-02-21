from django.db import transaction
from django.utils.decorators import method_decorator
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class BaseReadOnlyListViewSet(mixins.ListModelMixin, GenericViewSet):
    """Read-only ViewSet exposing list endpoint only."""
    pass


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class BaseReadOnlyDetailViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    """Read-only ViewSet exposing detail endpoint only."""
    pass


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class BaseReadOnlyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    """Read-only ViewSet exposing list + detail endpoints."""
    pass