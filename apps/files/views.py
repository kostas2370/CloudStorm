from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings

from .models import File
from .serializers import (
    MultiFileUploadSerializer,
    FileSerializer,
    FileListSerializer,
    FilePartialUpdateSerializer,
)
from .permissions import CanAdd, CanList, CanEdit, CanDelete, CanMassDelete, CanView
from .utils.file_utils import (
    generate_filename,
    generate_short_description,
    generate_tags,
    extract_data,
)

from apps.groups.models import GroupUser
from CloudStorm.paginator import StandardResultsSetPagination
from apps.groups.permissions import CanAccessPrivateGroup
from rest_framework.views import APIView
from azure.storage.blob import BlobServiceClient
from django.http import StreamingHttpResponse

import zipfile
import os
import tempfile
from django.core.files.base import ContentFile


class FilesViewSet(ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["name", "file_type", "group"]
    search_fields = ["name", "short_description"]
    http_method_names = ["get", "post", "delete", "patch"]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return self.queryset.filter(
            group__in=GroupUser.objects.filter(user=self.request.user).values("group")
        )

    def get_serializer_class(self):
        serializer_mapping = {
            "create": MultiFileUploadSerializer,
            "list": FileListSerializer,
            "partial_update": FilePartialUpdateSerializer,
        }

        return serializer_mapping.get(self.action, FileSerializer)

    def get_permissions(self):
        permission_mapping = {
            "create": [IsAuthenticated(), CanAccessPrivateGroup(), CanAdd()],
            "destroy": [IsAuthenticated(), CanAccessPrivateGroup(), CanDelete()],
            "list": [IsAuthenticated(), CanAccessPrivateGroup(), CanList()],
            "retrieve": [IsAuthenticated(), CanAccessPrivateGroup()],
            "mass_file_delete": [IsAuthenticated(), CanMassDelete()],
            "partial_update": [IsAuthenticated(), CanEdit()],
            "zip_upload": [IsAuthenticated(), CanAdd()],
            "ai_generate": [IsAuthenticated(), CanEdit()],
        }

        return permission_mapping.get(self.action, [IsAuthenticated()])

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tags = self.request.query_params.get("tags")

        if tags:
            tag_list = tags.split(",")
            queryset = queryset.filter(tags__name__in=tag_list).distinct()

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = MultiFileUploadSerializer(
            data=request.data,
            context={"request": request, "group": request.query_params.get("group")},
        )

        if serializer.is_valid():
            files = serializer.save()
            return Response(
                {
                    "message": "Files uploaded successfully",
                    "files": [file.id for file in files],
                },
                status=201,
            )
        return Response(serializer.errors, status=400)

    @action(methods=["DELETE"], detail=False)
    def mass_file_delete(self, request):
        to_delete = request.data.get("to_delete", [])
        try:
            File.objects.filter(
                id__in=to_delete, group_id=request.query_params.get("group")
            ).delete()
        except Exception as exc:
            return Response({"message": f"Error : {exc}"}, status=400)

        return Response({"message": "Files got deleted !"}, status=204)

    @action(methods=["POST"], detail=False)
    def zip_upload(self, request):
        zip_file = request.FILES.get("file")

        if not zip_file:
            return Response({"error": "No file provided."}, status=400)

        if not zip_file.name.endswith(".zip"):
            return Response(
                {"error": "Uploaded file is not a ZIP archive."}, status=400
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                with zipfile.ZipFile(zip_file, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                files = []
                for root, dirs, file_names in os.walk(temp_dir):
                    for filename in file_names:
                        file_path = os.path.join(root, filename)

                        with open(file_path, "rb") as f:
                            content = f.read()

                        content_file = ContentFile(content, name=filename)
                        files.append(content_file)

                serializer_data = {
                    "files": files,
                    "tags": request.data.get("tags", ""),
                    "ai_enabled": request.data.get("ai_enabled", False),
                }

                serializer = MultiFileUploadSerializer(
                    data=serializer_data,
                    context={
                        "request": request,
                        "group": request.query_params.get("group"),
                    },
                )
                serializer.is_valid(raise_exception=True)
                file_instances = serializer.save()

                return Response(
                    {
                        "message": "ZIP extracted and files uploaded successfully.",
                        "file_ids": [file.id for file in file_instances],
                    }
                )

            except zipfile.BadZipFile:
                return Response({"error": "Invalid ZIP file."}, status=400)

    @action(methods=["PATCH"], detail=True)
    def ai_generate(self, request, pk=None):
        obj = self.get_object()
        if obj.status == "generate":
            return Response(
                {"message": "The file is on generate status. Wait until its done!"},
                status=400,
            )
        generate_type = request.data.get("type")
        user_prompt = request.data.get("user_prompt")
        target_format = request.data.get("target_format")

        if not generate_type:
            return Response({"error": "Missing 'type' in request data."}, status=400)

        extracted_data = None
        if generate_type == "filename":
            extracted_data = generate_filename(obj, target_format)
            obj.name = extracted_data
            obj.save()
        elif generate_type == "short_description":
            extracted_data = generate_short_description(obj)
            obj.short_description = extracted_data
            obj.save()
        elif generate_type == "tags":
            extracted_data = generate_tags(obj)
            if extracted_data:
                for generated_tag in extracted_data:
                    obj.tags.add(generated_tag)
                obj.save()
        else:
            extracted_data = extract_data(obj, user_prompt)

        return Response({"extracted_data": extracted_data}, status=200)


class SecureAzureBlobView(APIView):
    permission_classes = [IsAuthenticated, CanView]

    def get(self, request, group_name, filename):
        try:
            file_path = f"uploads/{group_name}/{filename}"
            blob_service_client = BlobServiceClient.from_connection_string(
                settings.AZURE_CONNECTION_STRING
            )
            blob_client = blob_service_client.get_blob_client(
                container=settings.AZURE_CONTAINER, blob=file_path
            )
            stream = blob_client.download_blob()
            response = StreamingHttpResponse(
                stream.chunks(),
                content_type=stream.properties.content_settings.content_type,
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            print(e)
            return Response({"message": "File not found !"}, status=404)
