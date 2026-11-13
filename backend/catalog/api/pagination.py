"""Page/limit pagination done in the database (COUNT + LIMIT/OFFSET).

Response shape: {"items": [...], "page": 1, "limit": 12, "total": 7, "totalPages": 1}
"""

from math import ceil

from rest_framework import serializers

DEFAULT_LIMIT = 12
MAX_LIMIT = 50
MAX_PAGE = 10_000  # keeps OFFSET sane; page=10**20 must be a 400, not a database error


class PageQuerySerializer(serializers.Serializer):
    """Validates ?page and ?limit. Endpoint query serializers extend this."""

    page = serializers.IntegerField(min_value=1, max_value=MAX_PAGE, default=1)
    limit = serializers.IntegerField(min_value=1, max_value=MAX_LIMIT, default=DEFAULT_LIMIT)


def paginate(queryset, page, limit):
    """Returns (rows for this page, metadata). The queryset must already have a stable order.

    A page past the end returns no rows with the real total, not an error.
    """
    total = queryset.count()
    offset = (page - 1) * limit
    rows = list(queryset[offset:offset + limit])
    meta = {"page": page, "limit": limit, "total": total, "totalPages": ceil(total / limit)}
    return rows, meta


def page_response(items, meta):
    return {"items": items, **meta}
