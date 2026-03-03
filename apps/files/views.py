from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter

from django.conf import settings
from django.http import StreamingHttpResponse


from .models import File
from .serializers import (
    MultiFileUploadSerializer,
    FileSerializer,
    FileListSerializer,
    FilePartialUpdateSerializer,
    ZipUploadSerializer,
    AIGenerateSerializer,
)
from .permissions import (
    CanAdd,
    CanEdit,
    CanDelete,
    CanMassDelete,
    CanRetrieve,
    FileAccessPermission,
)
from .services import ai_generate_service, zip_upload_service

from apps.groups.permissions import CanAccessPrivateGroup
from apps.groups.models import GroupUser

from CloudStorm.paginator import StandardResultsSetPagination
from azure.storage.blob import BlobServiceClient

from .swagger_serializers import (
    FileUploadResponseSerializer,
    MassFileDeleteRequestSerializer,
    ErrorResponseSerializer,
    ZipUploadRequestSerializer,
    AIGenerateRequestSerializer,
    AIGenerateResponseSerializer,
)

from .filters import FileFilter

import zipfile
import logging

logger = logging.Logger("CloudStorm Logger")


class FilesViewSet(ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    search_fields = ["name", "short_description"]
    http_method_names = ["get", "post", "delete", "patch"]
    pagination_class = StandardResultsSetPagination
    filterset_class = FileFilter

    def get_queryset(self):
        return self.queryset.filter(
            group_id__in=GroupUser.objects.filter(user=self.request.user).values(
                "group_id"
            )
        ).select_related("group")

    def get_serializer_class(self):
        serializer_mapping = {
            "create": MultiFileUploadSerializer,
            "list": FileListSerializer,
            "partial_update": FilePartialUpdateSerializer,
            "zip_upload": ZipUploadSerializer,
            "ai_generate": AIGenerateSerializer,
        }

        return serializer_mapping.get(self.action, FileSerializer)

    def get_permissions(self):
        permission_mapping = {
            "create": [IsAuthenticated(), CanAccessPrivateGroup(), CanAdd()],
            "destroy": [IsAuthenticated(), CanAccessPrivateGroup(), CanDelete()],
            "list": [IsAuthenticated(), CanAccessPrivateGroup()],
            "retrieve": [IsAuthenticated(), CanRetrieve()],
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

    @extend_schema(
        responses={
            201: FileUploadResponseSerializer,
            400: OpenApiResponse(
                description="Bad request – serializer validation failed"
            ),
            403: OpenApiResponse(
                description="User is not authenticated or lacks add permissions"
            ),
        }
    )
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
        logger.error(serializer.errors)
        return Response(serializer.errors, status=400)

    @extend_schema(
        methods=["DELETE"],
        request=MassFileDeleteRequestSerializer,
        responses={
            204: OpenApiResponse(description="Files deleted successfully"),
            400: ErrorResponseSerializer,
            403: OpenApiResponse(
                description="User is not authenticated or lacks mass delete permissions"
            ),
        },
    )
    @action(methods=["DELETE"], detail=False)
    def mass_file_delete(self, request):
        to_delete = request.data.get("to_delete", [])
        try:
            File.objects.filter(
                id__in=to_delete, group_id=request.query_params.get("group")
            ).delete()
        except Exception as exc:
            logger.error(exc)
            return Response({"message": f"Error : {exc}"}, status=400)

        return Response({"message": "Files got deleted !"}, status=204)

    @extend_schema(
        methods=["POST"],
        request=ZipUploadRequestSerializer,
        responses={
            200: FileUploadResponseSerializer,
            400: ErrorResponseSerializer,
            403: OpenApiResponse(
                description="User is not authenticated or lacks add permissions"
            ),
        },
    )
    @action(methods=["POST"], detail=False)
    def zip_upload(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            file_instances = zip_upload_service(serializer.validated_data, request)
        except zipfile.BadZipFile:
            return Response({"message": "Invalid ZIP file."}, status=400)

        return Response(
            {
                "message": "ZIP extracted and files uploaded successfully.",
                "files": [file.id for file in file_instances],
            }
        )

    @extend_schema(
        methods=["PATCH"],
        request=AIGenerateRequestSerializer,
        responses={
            200: AIGenerateResponseSerializer,
            400: OpenApiResponse(description="Missing or invalid input data"),
            403: OpenApiResponse(
                description="User is not authenticated or lacks edit permissions"
            ),
        },
    )
    @action(methods=["PATCH"], detail=True)
    def ai_generate(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "file_obj": obj},
        )
        serializer.is_valid(raise_exception=True)

        try:
            extracted_data = ai_generate_service(obj, serializer.validated_data)
        except Exception:
            return Response(
                {"message": "There was a problem in generating data!"}, status=400
            )

        return Response({"extracted_data": extracted_data}, status=200)


class SecureAzureBlobView(APIView):
    permission_classes = [FileAccessPermission]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="group_name",
                type=str,
                location=OpenApiParameter.PATH,
                required=True,
            ),
            OpenApiParameter(
                name="filename", type=str, location=OpenApiParameter.PATH, required=True
            ),
        ],
        responses={
            200: OpenApiResponse(description="Streamed file download"),
            403: OpenApiResponse(description="User does not have access to this file"),
            404: OpenApiResponse(description="File not found"),
        },
        description="Securely streams a file from Azure Blob Storage by group and filename.",
    )
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
            logger.error(e)
            return Response({"message": "File not found !"}, status=404)
