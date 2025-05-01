from rest_framework.permissions import BasePermission
from apps.groups.models import GroupUser


class CanDelete(BasePermission):
    message = "You need to have the delete permission for this group!"

    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False
        gu = GroupUser.objects.filter(
            user=request.user, group=obj.group, can_delete=True
        )
        return gu.exists()


class CanAdd(BasePermission):
    def has_permission(self, request, view):
        gu = GroupUser.objects.filter(
            user=request.user, group=request.query_params.get("group")
        ).first()
        if not gu:
            return False
        return gu.can_add or gu.role == "admin"


class CanEdit(BasePermission):
    message = "You need to have the edit permission for this group!"

    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False

        gu = GroupUser.objects.filter(user=request.user, group=obj.group, can_edit=True)
        return gu.exists()


class CanRetrieve(BasePermission):
    message = "You need to be member to retrieve the file!!"

    def has_object_permission(self, request, view, obj):
        return obj.group.is_user_member(request.user) or not obj.group.is_private


class CanMassDelete(BasePermission):
    message = "You need to be member of the group, with delete permission!"

    def has_permission(self, request, view):
        group = request.query_params.get("group")

        if not group:
            return False

        gu = GroupUser.objects.filter(user=request.user, group__id=group).first()
        if not gu or not gu.can_delete:
            return False

        return True
