from django.db import transaction
from django.utils.decorators import method_decorator
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


@method_decorator(transaction.non_atomic_requests, name="dispatch")
class BaseReadOnlyGenericViewSet(GenericViewSet):
    pass


class BaseReadOnlyListViewSet(mixins.ListModelMixin, BaseReadOnlyGenericViewSet):
    pass


class BaseReadOnlyDetailViewSet(mixins.RetrieveModelMixin, BaseReadOnlyGenericViewSet):
    pass


class BaseReadOnlyViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    BaseReadOnlyGenericViewSet,
):
    pass