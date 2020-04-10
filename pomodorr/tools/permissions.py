from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsObjectOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class IsNotAuthenticated(permissions.BasePermission):
    message = _("Only unauthenticated users are allowed to perform this action.")

    def has_permission(self, request, view):
        return not request.user.is_authenticated
