from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .permissions import CanAdd, CanList, CanView, CanDelete
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .serializers import MultiFileUploadSerializer, FileSerializer, FileListSerializer
from apps.groups.models import GroupUser
from rest_framework.response import Response
from CloudStorm.paginator import StandardResultsSetPagination
from apps.groups.permissions import CanAccessPrivateGroup
from .models import File


class GroupsViewSet(ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'file_type', 'group']
    search_fields = ['name']
    http_method_names = ['get', 'post', 'delete']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(group__in = GroupUser.objects.filter(user = self.request.user, can_view = True).values('group'))

    def get_serializer_class(self):

        permission_mapping = {"create": MultiFileUploadSerializer,
                              "list": FileListSerializer}

        return permission_mapping.get(self.action, FileSerializer)

    def get_permissions(self):
        permission_mapping = {"create": [IsAuthenticated(), CanAdd(), CanAccessPrivateGroup()],
                              "destroy": [IsAuthenticated(), CanDelete(), CanAccessPrivateGroup()],
                              "list": [IsAuthenticated(), CanList(), CanAccessPrivateGroup()],
                              "retrieve": [IsAuthenticated(), CanView(), CanAccessPrivateGroup()], }

        return permission_mapping.get(self.action, [IsAuthenticated()])
    def create(self, request, *args, **kwargs):
        serializer = MultiFileUploadSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            files = serializer.save()
            return Response({"message": "Files uploaded successfully", "files": [file.id for file in files]}, status=201)
        return Response(serializer.errors, status=400)
