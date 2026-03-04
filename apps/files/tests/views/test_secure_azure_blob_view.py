from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from unittest.mock import patch, MagicMock

from apps.files.views import SecureAzureBlobView

from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.files.tests.baker_recipes import file_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


@override_settings(
    STORAGES=IN_MEMORY_STORAGES, AZURE_CONNECTION_STRING="fake", AZURE_CONTAINER="fake"
)
class SecureAzureBlobViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make(name="testgroup", is_private=False)
        group_user_member_recipe.make(group=self.group, user=self.user)
        self.file_obj = file_recipe.make(
            group=self.group,
            uploaded_by=self.user,
            name="sample.txt",
        )
        self.filename = self.file_obj.file.name.split("/")[-1]

    @patch("apps.files.views.BlobServiceClient")
    @patch("apps.files.permissions.File.objects.get")
    def test_get_streams_file_from_azure(self, mock_file_get, mock_blob_service_client):
        mock_file_get.return_value = self.file_obj

        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        mock_stream = MagicMock()
        mock_stream.chunks.return_value = iter([b"file content"])
        mock_stream.properties.content_settings.content_type = "text/plain"
        mock_blob_client.download_blob.return_value = mock_stream

        view = SecureAzureBlobView.as_view()
        request = self.factory.get(f"/files/media/{self.group.name}/{self.filename}/")
        request.resolver_match = MagicMock()
        request.resolver_match.kwargs = {
            "group_name": self.group.name,
            "filename": self.filename,
        }
        force_authenticate(request, user=self.user)

        response = view(request, group_name=self.group.name, filename=self.filename)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.filename, response["Content-Disposition"])

    @patch("apps.files.views.BlobServiceClient")
    @patch("apps.files.permissions.File.objects.get")
    def test_get_returns_404_when_azure_raises_exception(
        self, mock_file_get, mock_blob_service_client
    ):
        mock_file_get.return_value = self.file_obj
        mock_blob_service_client.from_connection_string.side_effect = Exception(
            "Azure unavailable"
        )

        view = SecureAzureBlobView.as_view()
        request = self.factory.get(f"/files/media/{self.group.name}/{self.filename}/")
        request.resolver_match = MagicMock()
        request.resolver_match.kwargs = {
            "group_name": self.group.name,
            "filename": self.filename,
        }
        force_authenticate(request, user=self.user)

        response = view(request, group_name=self.group.name, filename=self.filename)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("message", response.data)

    @patch("apps.files.permissions.File.objects.get")
    def test_get_returns_403_when_user_has_no_access_to_private_file(
        self, mock_file_get
    ):
        private_group = group_recipe.make(is_private=True)
        other_user = user_recipe.make()
        group_user_member_recipe.make(group=private_group, user=other_user)
        private_file = file_recipe.make(group=private_group, uploaded_by=other_user)

        mock_file_get.return_value = private_file

        view = SecureAzureBlobView.as_view()
        filename = private_file.file.name.split("/")[-1]
        request = self.factory.get(f"/files/media/{private_group.name}/{filename}/")
        request.resolver_match = MagicMock()
        request.resolver_match.kwargs = {
            "group_name": private_group.name,
            "filename": filename,
        }
        force_authenticate(request, user=self.user)

        response = view(request, group_name=private_group.name, filename=filename)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.files.views.BlobServiceClient")
    @patch("apps.files.permissions.File.objects.get")
    def test_get_returns_correct_content_disposition_header(
        self, mock_file_get, mock_blob_service_client
    ):
        mock_file_get.return_value = self.file_obj

        mock_blob_client = MagicMock()
        mock_blob_service_client.from_connection_string.return_value.get_blob_client.return_value = mock_blob_client

        mock_stream = MagicMock()
        mock_stream.chunks.return_value = iter([b"content"])
        mock_stream.properties.content_settings.content_type = (
            "application/octet-stream"
        )
        mock_blob_client.download_blob.return_value = mock_stream

        view = SecureAzureBlobView.as_view()
        request = self.factory.get(f"/files/media/{self.group.name}/{self.filename}/")
        request.resolver_match = MagicMock()
        request.resolver_match.kwargs = {
            "group_name": self.group.name,
            "filename": self.filename,
        }
        force_authenticate(request, user=self.user)

        response = view(request, group_name=self.group.name, filename=self.filename)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{self.filename}"',
        )
