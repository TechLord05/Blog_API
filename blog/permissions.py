from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permission:
    - Any user can read (GET, HEAD, OPTIONS)
    - Only authenticated authors can write (POST, PUT, DELETE)
    """

    def has_permission(self, request, view):
        # Allow read-only requests for anyone
        if request.method in SAFE_METHODS:
            return True

        # Unsafe requests require authenticated user
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions allowed to anyone
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only allowed to the author
        return obj.author == request.user
