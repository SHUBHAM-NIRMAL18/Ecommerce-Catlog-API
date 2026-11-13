"""One error shape for every API error:

    {"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [{"field": ..., "value": ..., "message": ...}]}}
"""

import logging

from django.http import Http404, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

CODES = {
    400: "VALIDATION_ERROR",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    406: "NOT_ACCEPTABLE",
    500: "INTERNAL_ERROR",
}


def error_body(status_code, message, details=None):
    return {"error": {"code": CODES.get(status_code, "ERROR"), "message": message, "details": details or []}}


def _first_message(messages):
    if isinstance(messages, (list, tuple)):
        return str(messages[0]) if messages else ""
    return str(messages)


def _validation_details(detail, request):
    """Turn DRF's {"field": ["msg"]} into [{"field", "value", "message"}], with the value the client sent."""
    if not isinstance(detail, dict):
        return [{"field": None, "value": None, "message": _first_message(detail)}]
    params = getattr(request, "query_params", {}) if request else {}
    return [
        {"field": field, "value": params.get(field), "message": _first_message(messages)}
        for field, messages in detail.items()
    ]


def exception_handler(exc, context):
    """DRF exception handler (set in settings.REST_FRAMEWORK)."""
    request = context.get("request")

    if isinstance(exc, Http404):
        exc = exceptions.NotFound()

    if isinstance(exc, exceptions.ValidationError):
        details = _validation_details(exc.detail, request)
        first = details[0]
        message = f"{first['field']}: {first['message']}" if first["field"] else first["message"]
        if len(details) > 1:
            message = f"{len(details)} invalid query parameters"
        return Response(error_body(400, message, details), status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, exceptions.APIException):
        return Response(error_body(exc.status_code, _first_message(exc.detail)), status=exc.status_code)

    # Anything else is a bug: log it with the traceback, never send it to the client.
    logger.exception("Unhandled API error", exc_info=exc)
    return Response(error_body(500, "Something went wrong."), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def not_found(request, exception=None):
    """404 for URLs that match no route (used for /api/* and as Django's handler404)."""
    return JsonResponse(error_body(404, f"No endpoint at {request.path}"), status=404)


def server_error(request):
    """Django's handler500, for errors outside DRF views."""
    return JsonResponse(error_body(500, "Something went wrong."), status=500)
