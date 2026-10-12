"""Project-wide API error envelope.

Every error response uses this shape (see docs/architecture/api-specification.md):

    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

_CODE_BY_STATUS = {
    status.HTTP_400_BAD_REQUEST: "validation_error",
    status.HTTP_401_UNAUTHORIZED: "authentication_required",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def api_exception_handler(exc, context):
    """Wrap DRF errors in the standard envelope; hide unhandled failures."""
    response = exception_handler(exc, context)
    if response is not None:
        code = _CODE_BY_STATUS.get(response.status_code, "request_error")
        detail = response.data
        if isinstance(detail, dict) and set(detail) == {"detail"}:
            message, details = str(detail["detail"]), {}
        else:
            message, details = "The request contains invalid data.", {"errors": detail}
        response.data = {"error": {"code": code, "message": message, "details": details}}
        return response
    return Response(
        {
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred.",
                "details": {},
            }
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
