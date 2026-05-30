import json
from functools import cached_property

from django.utils.translation import gettext_lazy as _
from rest_framework import pagination
from rest_framework.response import Response

APPROXIMATE_COUNT_THRESHOLD = 50_000


def _get_approximate_row_count(queryset) -> int:
    """Use PostgreSQL EXPLAIN to estimate row count.

    Falls back to exact ``COUNT(*)`` when the estimate is below
    ``APPROXIMATE_COUNT_THRESHOLD`` because the planner estimate is
    unreliable for small result sets.
    """
    qs = queryset.order_by()
    plan = json.loads(qs.explain(format="json"))
    estimate = int(plan[0]["Plan"]["Plan Rows"])
    if estimate < APPROXIMATE_COUNT_THRESHOLD:
        return qs.count()
    return estimate


class _ApproximateCountPaginator(pagination.PageNumberPagination.django_paginator_class):
    """Paginator that uses ``EXPLAIN`` estimate instead of ``COUNT(*)``."""

    @cached_property
    def count(self):
        return _get_approximate_row_count(self.object_list)


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


class NoCountPageNumberPagination(BasePageNumberPagination):
    """Page-number pagination that skips the ``COUNT(*)`` query.

    The response omits the ``count`` field entirely, which makes it
    suitable for large tables or infinite-scroll frontends where the
    total number of results is not needed.
    """

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = self.get_page_number(request, paginator)

        try:
            page = list(queryset[(page_number - 1) * page_size : page_number * page_size])
        except Exception:
            return None

        self.page = page
        return list(page)

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "next": {"type": "string", "nullable": True},
                "previous": {"type": "string", "nullable": True},
                "results": schema,
            },
        }


{%- if cookiecutter.database_engine == 'postgres' %}


class ApproximateCountPageNumberPagination(BasePageNumberPagination):
    """Page-number pagination that uses PostgreSQL EXPLAIN for count.

    Instead of running an expensive ``COUNT(*)`` query, the paginator
    parses the ``EXPLAIN`` output to get an estimated row count.  When
    the estimate is below 50 000 rows it falls back to an exact count
    because the planner estimate is unreliable at that scale.

    Only available when the database engine is PostgreSQL.
    """

    django_paginator_class = _ApproximateCountPaginator
{%- endif %}
