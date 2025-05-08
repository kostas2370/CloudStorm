from rest_framework.permissions import BasePermission
from apps.groups.models import GroupUser
from apps.files.models import File


class CanDelete(BasePermission):
    message = "You do not have delete permissions for this group."

    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False
        gu = GroupUser.objects.filter(
            user=request.user, group=obj.group, can_delete=True
        )
        return gu.exists()


class CanAdd(BasePermission):
    message = "You do not have permission to add items to this group."

    def has_permission(self, request, view):
        gu = GroupUser.objects.filter(
            user=request.user, group=request.query_params.get("group")
        ).first()
        if not gu:
            return False
        return gu.can_add or gu.role == "admin"


class CanEdit(BasePermission):
    message = "You do not have permission to edit items in this group."

    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False

        gu = GroupUser.objects.filter(user=request.user, group=obj.group, can_edit=True)
        return gu.exists()


class CanRetrieve(BasePermission):
    message = "You must be a group member to retrieve this file."

    def has_object_permission(self, request, view, obj):
        return obj.group.is_user_member(request.user) or not obj.group.is_private


class CanMassDelete(BasePermission):
    message = "You must be a member of the group and have delete permission."

    def has_permission(self, request, view):
        group = request.query_params.get("group")

        if not group:
            return False

        gu = GroupUser.objects.filter(user=request.user, group__id=group).first()
        if not gu or not gu.can_delete:
            return False

        return True


class FileAccessPermission(BasePermission):
    def has_permission(self, request, view):
        group_name = request.resolver_match.kwargs.get("group_name")
        filename = request.resolver_match.kwargs.get("filename")
        file_path = f"uploads/{group_name}/{filename}"
        file = File.objects.get(file=file_path)
        return file.check_user_access(request.user)
