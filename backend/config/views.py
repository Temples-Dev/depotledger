"""Foundation views: health check only. Domain views live in apps/."""

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Report service liveness and database connectivity."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            connections["default"].ensure_connection()
            database = "connected"
        except OperationalError:
            database = "unreachable"
        status_code = 200 if database == "connected" else 503
        return Response(
            {"status": "ok" if status_code == 200 else "degraded", "database": database},
            status=status_code,
        )


def api_not_found(request, exception):
    """Return the standard error envelope for unknown API routes."""
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "error": {
                    "code": "not_found",
                    "message": "The requested resource was not found.",
                    "details": {},
                }
            },
            status=404,
        )
    from django.views.defaults import page_not_found

    return page_not_found(request, exception)
