"""Shared permission bases. Module-specific checks live in each app."""

from rest_framework.permissions import IsAuthenticated


class ActiveUserPermission(IsAuthenticated):
    """Allow only active authenticated users."""

    message = "An active authenticated user is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "is_active", False)
        )
