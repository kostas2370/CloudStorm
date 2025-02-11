from rest_framework.permissions import BasePermission
from .models import GroupUser
from apps.files.models import File


class IsGroupAdmin(BasePermission):
    message = "You have to be admin to do this action"

    def has_object_permission(self, request, view, obj):
        group_user = GroupUser.objects.filter(group = obj, user = request.user).first()
        return group_user and group_user.role == "admin"


class IsGroupUser(BasePermission):
    message = "You have to be member of the group to do this action"

    def has_object_permission(self, request, view, obj):
        return obj.is_user_member(request.user)


class CanAccessPrivateGroup(BasePermission):
    message = "This group is private you need to add the passcode"

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, File):
            obj = obj.group

        if not obj.is_private:
            return True

        if not obj.is_user_member(request.user):
            return False

        passcode = request.query_params.get("passcode")
        if not passcode or not obj.check_passcode(passcode):
            return False

        return True


class IsVerifiedUser(BasePermission):
    message = "You have to be verified to do this action"

    def has_permission(self, request, view):
        return request.user.is_verified
