from rest_framework.permissions import BasePermission


class IsAdminPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_staff:
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        is_requester_admin = request.user.is_staff
        is_target_regular_user = not obj.is_staff and not obj.is_superuser

        return is_requester_admin and is_target_regular_user


class IsSuperuserPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_superuser
