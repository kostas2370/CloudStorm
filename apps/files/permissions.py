from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from apps.groups.models import GroupUser, Group


class CanDelete(BasePermission):
    message = "You need to have the delete permission for this group!"
    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False
        gu = GroupUser.objects.filter(user = request.user, group = obj.group, can_delete = True)
        return gu.exists()


class CanAdd(BasePermission):
    def has_permission(self, request, view):

        gu = GroupUser.objects.filter(user = request.user, group = request.query_params.get('group')).first()
        if not gu:
            return False
        return gu.can_add or gu.role == "admin"


class CanView(BasePermission):

    def has_permission(self, request, view):
        return GroupUser.objects.filter(user = request.user, group = request.query_params.get('group')).exists()


class CanEdit(BasePermission):
    message = "You need to have the edit permission for this group!"

    def has_object_permission(self, request, view, obj):
        if obj.status == "generate":
            self.message = "You can not Delete when status is generate"
            return False

        gu = GroupUser.objects.filter(user = request.user, group = obj.group, can_edit = True)
        return gu.exists()


class CanList(BasePermission):
    def has_permission(self, request, view):
        group = request.query_params.get('group')
        if not group:
            return True

        gu = GroupUser.objects.filter(user = request.user, group__id = group).first()
        if not gu:
            return False

        obj = get_object_or_404(Group, pk = group)

        return not obj.is_private or (obj.is_user_member(request.user))


class CanMassDelete(BasePermission):

    def has_permission(self, request, view):
        group = request.query_params.get('group')

        if not group:
            return False

        gu = GroupUser.objects.filter(user = request.user, group__id = group).first()
        if not gu or not gu.can_delete:
            return False

        return True
