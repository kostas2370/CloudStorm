from rest_framework.viewsets import ModelViewSet
from .models import Group
from rest_framework.permissions import IsAuthenticated
from .serializers import GroupSerializer, GroupListsSerializer
from .permissions import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


class GroupsViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'is_private']
    search_fields = ['name']

    def get_permissions(self):
        if self.action in ['destroy', 'put', 'patch']:
            return [IsGroupAdmin(), ]

        if self.action in ['create', "list"]:
            return [IsAuthenticated(), ]

        if self.action == 'retrieve':
            return [CanAccessPrivateGroup()]

        return [IsGroupUser(), ]

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

