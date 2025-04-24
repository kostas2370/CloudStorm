from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .models import File
from .serializers import MultiFileUploadSerializer, FileSerializer, FileListSerializer
from .permissions import CanAdd, CanList, CanView, CanDelete, CanMassDelete

from apps.groups.models import GroupUser
from CloudStorm.paginator import StandardResultsSetPagination
from apps.groups.permissions import CanAccessPrivateGroup
from rest_framework.views import APIView
from azure.storage.blob import BlobServiceClient
from django.http import StreamingHttpResponse


class GroupsViewSet(ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['name', 'file_type', 'group']
    search_fields = ['name']
    http_method_names = ['get', 'post', 'delete']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(group__in =
                                    GroupUser.objects.filter(user = self.request.user, can_view = True).values('group'))

    def get_serializer_class(self):

        serializer_mapping = {"create": MultiFileUploadSerializer,
                              "list": FileListSerializer}

        return serializer_mapping.get(self.action, FileSerializer)

    def get_permissions(self):
        permission_mapping = {"create": [IsAuthenticated(), CanAdd(), CanAccessPrivateGroup()],
                              "destroy": [IsAuthenticated(), CanDelete(), CanAccessPrivateGroup()],
                              "list": [IsAuthenticated(), CanList(), CanAccessPrivateGroup()],
                              "retrieve": [IsAuthenticated(), CanView(), CanAccessPrivateGroup()],
                              "mass_file_delete": [IsAuthenticated(), CanMassDelete()]}

        return permission_mapping.get(self.action, [IsAuthenticated()])

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tags = self.request.query_params.get('tags')

        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__name__in = tag_list).distinct()

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = MultiFileUploadSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            files = serializer.save()
            return Response({"message": "Files uploaded successfully", "files": [file.id for file in files]},
                            status=201)
        return Response(serializer.errors, status=400)

    @action(methods = ["DELETE"], detail = False)
    def mass_file_delete(self, request):
        to_delete = request.data.get("to_delete", [])
        try:
            File.objects.filter(id__in = to_delete, group_id = request.query_params.get("group")).delete()
        except Exception as exc:
            return Response({"message": f"Error : {exc}"}, status = 400)

        return Response({"message": f"Files got deleted !"}, status = 204)


class SecureAzureBlobView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request, group_name, filename):
        try:
            file_path = f'uploads/{group_name}/{filename}'
            blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
            blob_client = blob_service_client.get_blob_client(container = settings.AZURE_CONTAINER, blob = file_path)
            stream = blob_client.download_blob()
            response = StreamingHttpResponse(stream.chunks(),
                                             content_type = stream.properties.content_settings.content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            print(e)
            return Response({"message": "File not found !"}, status = 404)
