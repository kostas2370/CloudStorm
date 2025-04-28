from rest_framework import filters
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend

from .models import Group, GroupUser
from .serializers import GroupSerializer, GroupListsSerializer
from .permissions import (
    IsGroupUser,
    IsGroupAdmin,
    CanAccessPrivateGroup,
    IsVerifiedUser,
)

import io
import zipfile
from django.conf import settings
from django.http import StreamingHttpResponse
from azure.storage.blob import BlobServiceClient
from rest_framework.decorators import action
from django.core.mail import send_mail


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
        send_mail(
            subject="You got added to a group",
            recipient_list=[user.email],
            message=f"You got added to a group named : {group.name}",
            from_email=settings.EMAIL_HOST_USER,
        )

        return Response({"message": "User added successfully!"})

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

        group_user.delete()

        return Response({"message": "User removed successfully"}, status=204)

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
                    print(f"Error downloading blob {blob_path}: {e}")
                    continue

        zip_buffer.seek(0)

        response = StreamingHttpResponse(zip_buffer, content_type="application/zip")
        response["Content-Disposition"] = (
            f"attachment; filename=group_{group.id}_files.zip"
        )
        return response
