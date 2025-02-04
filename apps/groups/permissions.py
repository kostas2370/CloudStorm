from rest_framework.permissions import BasePermission
from .models import GroupUser


class IsGroupAdmin(BasePermission):

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated and not request.user.is_verified:
            return False

        group_user = GroupUser.objects.filter(group = obj, user = request.user).first()
        return group_user and group_user.role == "admin"


class IsGroupUser(BasePermission):

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated and not request.user.is_verified:
            return False

        return obj.is_user_member(request.user)


class CanAccessPrivateGroup(BasePermission):

    def has_object_permission(self, request, view, obj):
        if not obj.is_private:
            return True

        if not obj.is_user_member(request.user):
            return False

        passcode = request.query_params.get("passcode")
        if not passcode or not obj.check_passcode(passcode):
            return False

        return True
