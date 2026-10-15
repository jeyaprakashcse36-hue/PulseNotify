
from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """
    Allow access only to authenticated users with the ADMIN profile role.
    """

    message = "You must have the ADMIN role to access this endpoint."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return (
            hasattr(user, "profile")
            and user.profile.role == "ADMIN"
        )
