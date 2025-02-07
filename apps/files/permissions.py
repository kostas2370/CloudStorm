from rest_framework.permissions import BasePermission
from apps.groups.models import GroupUser, Group
from django.shortcuts import get_object_or_404


class CanDelete(BasePermission):
    def has_object_permission(self, request, view, obj):
        gu = GroupUser.objects.filter(user = request.user, group = obj.group).first()
        if not gu:
            return False

        return gu.can_delete


class CanAdd(BasePermission):
    def has_permission(self, request, view):

        gu = GroupUser.objects.filter(user = request.user, group = request.data.get('group')).first()
        if not gu:
            return False

        return gu.can_add


class CanList(BasePermission):
    def has_permission(self, request, view):
        group = request.query_params.get('group')
        if not group:
            return True

        gu = GroupUser.objects.filter(user = request.user, group__id = group).first()
        if not gu or not gu.can_view:
            return False

        obj = get_object_or_404(Group, pk = group)
        passcode = request.query_params.get("passcode")

        return not obj.is_private or (obj.is_user_member(request.user) and obj.check_passcode(passcode or ""))


class CanView(BasePermission):
    def has_object_permission(self, request, view, obj):
        gu = GroupUser.objects.filter(user = request.user, group = obj.group).first()
        if not gu:
            return False

        return gu.can_view


class CanMassDelete(BasePermission):

    def has_permission(self, request, view):
        group = request.query_params.get('group')
        passcode = request.query_params.get('passcode')

        if not group:
            return False

        gu = GroupUser.objects.filter(user = request.user, group__id = group).first()
        if not gu or not gu.can_delete:
            return False

        return gu.group.check_passcode(passcode)
