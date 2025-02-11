from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Group, GroupUser
from .serializers import GroupSerializer, GroupListsSerializer
from .permissions import IsGroupUser, IsGroupAdmin, CanAccessPrivateGroup, IsVerifiedUser


class GroupsViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'is_private']
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['destroy', 'put', 'patch', "add_member", "remove_member"]:
            return [IsAuthenticated(), IsVerifiedUser(), IsGroupAdmin(), CanAccessPrivateGroup()]

        if self.action in ['create', "list"]:
            return [IsAuthenticated(), ]

        if self.action == 'retrieve':
            return [IsAuthenticated(), CanAccessPrivateGroup()]

        return [IsAuthenticated(), IsGroupUser(), ]

    def get_serializer_class(self):
        if self.action == "list":
            return GroupListsSerializer

        return GroupSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.filter(groupuser__user = self.request.user)
        return super().get_queryset()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tags = self.request.query_params.get('tags')

        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__name__in = tag_list).distinct()

        return queryset

    @action(methods = ["POST"], detail = True)
    def add_member(self, request, _):
        group = self.get_object()
        data = request.data.copy()
        user_id = data.pop('user_id', None)
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        user = get_object_or_404(get_user_model(), id=user_id)
        group_user = group.groupuser_set.filter(user=user).first()
        if group_user:
            return Response({"error": "User is already a member"}, status=400)

        GroupUser.objects.create(user = user, group = group, **data)
        return Response({"message": "User added successfully!"})

    @action(methods = ["DELETE"], detail = True)
    def remove_member(self, request, _):
        group = self.get_object()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        group_user = group.groupuser_set.filter(user__id=user_id).first()
        if not group_user:
            return Response({"error": "There is not a user with that id in the group"}, status=400)

        if group_user.role == "admin" and user_id != str(request.user.id):
            return Response({"error": "You do not have permission to remove other group admin"}, status=400)

        group_user.delete()

        return Response({"message": "User removed successfully"}, status = 204)
