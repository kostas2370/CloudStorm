from rest_framework.viewsets import ModelViewSet
from .models import Group
from rest_framework.permissions import IsAuthenticated
from .serializers import GroupSerializer, GroupListsSerializer
from .permissions import *


class GroupsViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_permissions(self):
        if self.action in ['destroy', 'put', 'patch']:
            return [IsGroupAdmin(), ]

        if self.action in ['create']:
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

