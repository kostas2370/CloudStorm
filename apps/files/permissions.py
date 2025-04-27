from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from apps.groups.models import GroupUser, Group


class CanDelete(BasePermission):
    def has_object_permission(self, request, view, obj):
        gu = GroupUser.objects.filter(user = request.user, group = obj.group).first()
        if not gu:
            return False

        return gu.can_delete


class CanAdd(BasePermission):
    def has_permission(self, request, view):

        gu = GroupUser.objects.filter(user = request.user, group = request.query_params.get('group')).first()
        if not gu:
            return False
        return gu.can_add


class CanView(BasePermission):
    def has_permission(self, request, view):
        return GroupUser.objects.filter(user = request.user, group = request.query_params.get('group')).exists()


class CanEdit(BasePermission):
    def has_permission(self, request, view):

        gu = GroupUser.objects.filter(user = request.user, group = request.query_params.get('group')).first()
        if not gu:
            return False
        return gu.can_edit


class CanList(BasePermission):
    def has_permission(self, request, view):
        group = request.query_params.get('group')
        if not group:
            return True

        gu = GroupUser.objects.filter(user = request.user, group__id = group).first()
        if not gu or not gu.can_view:
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
