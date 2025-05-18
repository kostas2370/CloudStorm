from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.http import StreamingHttpResponse

from .models import Group, GroupUser
from .serializers import GroupSerializer, GroupListsSerializer
from .permissions import (
    IsGroupUser,
    IsGroupAdmin,
    CanAccessPrivateGroup,
    IsVerifiedUser,
)
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from .swagger_seriallizers import (
    EditGroupMemberSerializer,
    AddMemberSerializer,
    AddMemberResponseSerializer,
)

import io
import zipfile
import logging
from uuid import UUID


from azure.storage.blob import BlobServiceClient
from apps.users.tasks import send_email

logger = logging.Logger("CloudStorm Logger")


class GroupsViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["name", "is_private"]
    search_fields = ["name"]

    def get_permissions(self):
        if self.action in [
            "destroy",
            "put",
            "patch",
            "add_member",
            "remove_member",
            "edit_member",
        ]:
            return [IsAuthenticated(), IsVerifiedUser(), IsGroupAdmin()]

        if self.action in ["create", "list"]:
            return [
                IsAuthenticated(),
            ]

        if self.action == "retrieve":
            return [IsAuthenticated(), CanAccessPrivateGroup()]

        return [
            IsAuthenticated(),
            IsGroupUser(),
        ]

    def get_serializer_class(self):
        if self.action == "list":
            return GroupListsSerializer

        return GroupSerializer

    def get_queryset(self):
        if self.action == "list":
            return self.queryset.filter(groupuser__user=self.request.user)
        return super().get_queryset()

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        tags = self.request.query_params.get("tags")

        if tags:
            tag_list = tags.split(",")
            queryset = queryset.filter(tags__name__in=tag_list).distinct()

        return queryset

    @extend_schema(
        request=GroupSerializer,
        responses={
            201: GroupSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Unauthorized or permission denied"),
        },
        description="Creates a new group and assigns the creator as an admin member.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request)

    @extend_schema(
        methods=["POST"],
        request=AddMemberSerializer,
        responses={
            200: AddMemberResponseSerializer,
            400: OpenApiResponse(description="Validation or business logic error"),
            403: OpenApiResponse(
                description="User is not authenticated, verified, or not a group admin"
            ),
        },
        description="Adds a user to the group using their email. Additional role and permissions can be provided.",
    )
    @action(methods=["POST"], detail=True)
    def add_member(self, request, pk):
        group = self.get_object()
        data = request.data.copy()
        email = data.pop("user_email", None)
        if not email:
            return Response({"error": "User email is required"}, status=400)
        user = get_user_model().objects.filter(email=email[0]).first()
        if not user:
            return Response({"error": "There is not user with this email"}, status=400)

        group_user = group.groupuser_set.filter(user=user).first()
        if group_user:
            return Response({"error": "User is already a member"}, status=400)

        GroupUser.objects.create(user=user, group=group, **data)
        send_email.delay(
            subject="You got added to a group",
            recipient_list=[user.email],
            message=f"You got added to a group named : {group.name}",
        )

        return Response({"message": "User added successfully!"})

    @extend_schema(
        methods=["DELETE"],
        parameters=[
            OpenApiParameter(
                name="user_id",
                type=UUID,
                location=OpenApiParameter.QUERY,
                required=True,
                description="UUID of the user to remove from the group",
            )
        ],
        responses={
            204: OpenApiResponse(description="User removed successfully"),
            400: OpenApiResponse(
                description="Missing or invalid user_id, or permission error"
            ),
            403: OpenApiResponse(
                description="User is not authenticated, verified, or not a group admin"
            ),
        },
        description="Removes a member from the group by UUID. Only admins can remove themselves or non-admin users.",
    )
    @action(methods=["DELETE"], detail=True)
    def remove_member(self, request, _):
        group = self.get_object()
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "User ID is required"}, status=400)

        group_user = group.groupuser_set.filter(user__id=user_id).first()
        if not group_user:
            return Response(
                {"error": "There is not a user with that id in the group"}, status=400
            )

        if group_user.role == "admin" and user_id != str(request.user.id):
            return Response(
                {"error": "You do not have permission to remove other group admin"},
                status=400,
            )
        send_email.delay(
            subject="You have been removed from a group",
            recipient_list=[group_user.user.email],
            message=f"You got removed from a group named : {group.name}",
        )

        group_user.delete()

        return Response({"message": "User removed successfully"}, status=204)

    @extend_schema(
        methods=["PUT"],
        request=EditGroupMemberSerializer(many=True),
        responses={
            200: OpenApiResponse(description="User permissions updated"),
            400: OpenApiResponse(description="Invalid request data"),
            403: OpenApiResponse(
                description="User is not authenticated, verified, or not a group admin"
            ),
        },
        description="Edit roles and permissions of members in a group.",
    )
    @action(methods=["PUT"], detail=True)
    def edit_members(self, request, pk):
        group = self.get_object()
        for member in request.data:
            group_user = group.groupuser_set.filter(user__id=member["user_id"]).first()
            if not group_user:
                continue
            group_user.role = member.get("role", group_user.role)
            group_user.can_add = member.get("can_add", group_user.role)
            group_user.can_delete = member.get("can_delete", group_user.role)
            group_user.save()

        return Response({"message": "Users permission got edited !"}, status=200)

    @extend_schema(
        methods=["GET"],
        responses={
            200: OpenApiResponse(description="ZIP file containing all group files"),
            403: OpenApiResponse(
                description="User is not authenticated or not a group member"
            ),
            404: OpenApiResponse(description="No files found for this group"),
        },
        description="Downloads all files in the group as a ZIP archive.",
    )
    @action(methods=["GET"], detail=True)
    def download_zip(self, request, pk):
        group = self.get_object()
        files = group.files.all()

        if not files.exists():
            return Response("No files found.", status=404)

        blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_CONNECTION_STRING
        )
        container = settings.AZURE_CONTAINER

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                blob_path = file.file.name

                try:
                    blob_client = blob_service_client.get_blob_client(
                        container=container, blob=blob_path
                    )
                    stream = blob_client.download_blob()
                    file_data = stream.readall()
                    filename = file.name or blob_path.split("/")[-1]
                    zip_file.writestr(filename, file_data)

                except Exception as e:
                    logger.error(f"Error downloading blob {blob_path}: {e}")
                    continue

        zip_buffer.seek(0)

        response = StreamingHttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = (
            f"attachment; filename=group_{group.id}_files.zip"
        )
        return response
