from django.utils.translation import gettext_lazy as _
from rest_framework import pagination


class BasePageNumberPagination(pagination.PageNumberPagination):
    """Default page-number pagination with configurable query param."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class NoPageNumberPagination(BasePageNumberPagination):
    """Allow opt-out of pagination for lightweight endpoints."""

    page_query_description = _("Supports disabling pagination via `no_page`")
    page_size_query_description = _(
        "Using `no_page` on large datasets may cause performance issues"
    )

    def paginate_queryset(self, queryset, request, view=None):
        if "no_page" in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)
