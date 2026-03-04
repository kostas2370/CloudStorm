import io
import zipfile
import uuid

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from unittest.mock import patch, MagicMock

from apps.files.views import FilesViewSet
from apps.files.models import File

from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_member_recipe,
    group_user_admin_recipe,
)
from apps.files.tests.baker_recipes import file_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetListTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)

    def test_list_returns_only_files_from_user_groups(self):
        group1 = group_recipe.make()
        group2 = group_recipe.make()

        group_user_member_recipe.make(group=group1, user=self.user)

        other_user = user_recipe.make()
        group_user_member_recipe.make(group=group2, user=other_user)

        file_in_group1 = file_recipe.make(group=group1, uploaded_by=self.user, name="Mine")
        file_recipe.make(group=group2, uploaded_by=other_user, name="NotMine")

        view = FilesViewSet.as_view({"get": "list"})
        request = self.factory.get("/files/")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {str(f["id"]) for f in response.data["results"]}
        self.assertIn(str(file_in_group1.id), result_ids)

    def test_list_excludes_files_from_groups_user_is_not_member_of(self):
        group1 = group_recipe.make()
        group2 = group_recipe.make()

        group_user_member_recipe.make(group=group1, user=self.user)

        other_user = user_recipe.make()
        group_user_member_recipe.make(group=group2, user=other_user)

        file_recipe.make(group=group1, uploaded_by=self.user, name="Mine")
        other_file = file_recipe.make(group=group2, uploaded_by=other_user, name="NotMine")

        view = FilesViewSet.as_view({"get": "list"})
        request = self.factory.get("/files/")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {str(f["id"]) for f in response.data["results"]}
        self.assertNotIn(str(other_file.id), result_ids)

    def test_list_unauthenticated_returns_401(self):
        view = FilesViewSet.as_view({"get": "list"})
        request = self.factory.get("/files/")

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_filtered_by_tags(self):
        group = group_recipe.make()
        group_user_member_recipe.make(group=group, user=self.user)

        tagged_file = file_recipe.make(group=group, uploaded_by=self.user, name="Tagged")
        untagged_file = file_recipe.make(group=group, uploaded_by=self.user, name="Untagged")
        tagged_file.tags.add("alpha")

        view = FilesViewSet.as_view({"get": "list"})
        request = self.factory.get("/files/", {"tags": "alpha"})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {str(f["id"]) for f in response.data["results"]}
        self.assertIn(str(tagged_file.id), result_ids)
        self.assertNotIn(str(untagged_file.id), result_ids)

    def test_list_filtered_by_file_type(self):
        group = group_recipe.make()
        group_user_member_recipe.make(group=group, user=self.user)

        doc_file = file_recipe.make(group=group, uploaded_by=self.user)
        image_file = file_recipe.make(group=group, uploaded_by=self.user)
        File.objects.filter(id=image_file.id).update(file_type="image")

        view = FilesViewSet.as_view({"get": "list"})
        request = self.factory.get("/files/", {"file_type": "document"})
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = {str(f["id"]) for f in response.data["results"]}
        self.assertIn(str(doc_file.id), result_ids)
        self.assertNotIn(str(image_file.id), result_ids)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetRetrieveTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)

    def test_retrieve_file_as_group_member(self):
        group = group_recipe.make(is_private=False)
        group_user_member_recipe.make(group=group, user=self.user)
        file_obj = file_recipe.make(group=group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/files/{file_obj.id}/")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(file_obj.id))

    def test_retrieve_file_from_public_group_non_member_returns_404(self):
        # get_queryset() filters to groups the user is a member of, so a
        # non-member never finds the file in their queryset → 404.
        public_group = group_recipe.make(is_private=False)
        owner = user_recipe.make()
        group_user_member_recipe.make(group=public_group, user=owner)
        file_obj = file_recipe.make(group=public_group, uploaded_by=owner)

        view = FilesViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/files/{file_obj.id}/")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_file_from_private_group_non_member_returns_404(self):
        # Same queryset restriction: non-member's queryset excludes the file.
        private_group = group_recipe.make(is_private=True)
        owner = user_recipe.make()
        group_user_member_recipe.make(group=private_group, user=owner)
        file_obj = file_recipe.make(group=private_group, uploaded_by=owner)

        view = FilesViewSet.as_view({"get": "retrieve"})
        request = self.factory.get(f"/files/{file_obj.id}/")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetCreateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        self.admin_gu = group_user_admin_recipe.make(group=self.group, user=self.user)

    @patch("apps.files.serializers.group")
    @patch("apps.files.serializers.process_file")
    def test_create_files_successfully_returns_201(self, mock_process_file, mock_group):
        mock_task = MagicMock()
        mock_process_file.s.return_value = mock_task
        mock_group.return_value = MagicMock()
        mock_group.return_value.apply_async.return_value = None

        dummy_file = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")

        view = FilesViewSet.as_view({"post": "create"})
        request = self.factory.post(
            f"/files/?group={self.group.id}",
            {"files": [dummy_file], "ai_enabled": False},
            format="multipart",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("files", response.data)
        self.assertIn("message", response.data)

    def test_create_files_returns_403_without_can_add_permission(self):
        member_gu = group_user_member_recipe.make(
            group=self.group, user=user_recipe.make(is_verified=True), can_add=False
        )
        no_add_user = member_gu.user

        dummy_file = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")

        view = FilesViewSet.as_view({"post": "create"})
        request = self.factory.post(
            f"/files/?group={self.group.id}",
            {"files": [dummy_file]},
            format="multipart",
        )
        force_authenticate(request, user=no_add_user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_files_returns_403_when_not_group_member(self):
        non_member = user_recipe.make(is_verified=True)
        dummy_file = SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")

        view = FilesViewSet.as_view({"post": "create"})
        request = self.factory.post(
            f"/files/?group={self.group.id}",
            {"files": [dummy_file]},
            format="multipart",
        )
        force_authenticate(request, user=non_member)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetPartialUpdateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        self.group_user = group_user_admin_recipe.make(group=self.group, user=self.user)
        self.file = file_recipe.make(group=self.group, uploaded_by=self.user, name="Original")

    def test_partial_update_name_with_can_edit_returns_200(self):
        view = FilesViewSet.as_view({"patch": "partial_update"})
        data = {"name": "Updated Name"}
        request = self.factory.patch(f"/files/{self.file.id}/", data, format="json")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.file.refresh_from_db()
        self.assertEqual(self.file.name, "Updated Name")

    def test_partial_update_short_description_returns_200(self):
        view = FilesViewSet.as_view({"patch": "partial_update"})
        data = {"short_description": "A new description"}
        request = self.factory.patch(f"/files/{self.file.id}/", data, format="json")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.file.refresh_from_db()
        self.assertEqual(self.file.short_description, "A new description")

    def test_partial_update_returns_403_without_can_edit(self):
        member = user_recipe.make(is_verified=True)
        group_user_member_recipe.make(group=self.group, user=member, can_edit=False)

        view = FilesViewSet.as_view({"patch": "partial_update"})
        data = {"name": "Hacked"}
        request = self.factory.patch(f"/files/{self.file.id}/", data, format="json")
        force_authenticate(request, user=member)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_returns_403_when_status_is_generate(self):
        self.file.status = "generate"
        self.file.save(update_fields=["status"])

        view = FilesViewSet.as_view({"patch": "partial_update"})
        data = {"name": "While Generating"}
        request = self.factory.patch(f"/files/{self.file.id}/", data, format="json")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetDestroyTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        self.group_user = group_user_admin_recipe.make(group=self.group, user=self.user)

    @patch("apps.files.models.File.delete")
    def test_destroy_file_with_can_delete_returns_204(self, mock_delete):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(f"/files/{file_obj.id}/")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_returns_403_without_can_delete(self):
        member = user_recipe.make(is_verified=True)
        group_user_member_recipe.make(group=self.group, user=member, can_delete=False)
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(f"/files/{file_obj.id}/")
        force_authenticate(request, user=member)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(File.objects.filter(id=file_obj.id).exists())

    @patch("apps.files.models.File.delete")
    def test_destroy_returns_403_when_status_is_generate(self, mock_delete):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user, status="generate")

        view = FilesViewSet.as_view({"delete": "destroy"})
        request = self.factory.delete(f"/files/{file_obj.id}/")
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(file_obj.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        mock_delete.assert_not_called()


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetMassFileDeleteTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        self.group_user = group_user_admin_recipe.make(group=self.group, user=self.user)

    @patch("apps.files.models.File.delete")
    def test_mass_file_delete_successfully_returns_204(self, mock_delete):
        file1 = file_recipe.make(group=self.group, uploaded_by=self.user)
        file2 = file_recipe.make(group=self.group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"delete": "mass_file_delete"})
        data = {"to_delete": [str(file1.id), str(file2.id)]}
        request = self.factory.delete(
            f"/files/mass_file_delete/?group={self.group.id}",
            data,
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_mass_file_delete_returns_403_without_can_delete(self):
        member = user_recipe.make(is_verified=True)
        group_user_member_recipe.make(group=self.group, user=member, can_delete=False)
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"delete": "mass_file_delete"})
        data = {"to_delete": [str(file_obj.id)]}
        request = self.factory.delete(
            f"/files/mass_file_delete/?group={self.group.id}",
            data,
            format="json",
        )
        force_authenticate(request, user=member)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mass_file_delete_returns_403_without_group_query_param(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        view = FilesViewSet.as_view({"delete": "mass_file_delete"})
        data = {"to_delete": [str(file_obj.id)]}
        request = self.factory.delete(
            "/files/mass_file_delete/",
            data,
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetZipUploadTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        group_user_admin_recipe.make(group=self.group, user=self.user)

    @patch("apps.files.views.zip_upload_service")
    def test_zip_upload_successfully_returns_200(self, mock_zip_service):
        mock_file = MagicMock()
        mock_file.id = uuid.uuid4()
        mock_zip_service.return_value = [mock_file]

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("hello.txt", "hello world")
        zip_buffer.seek(0)
        zip_file = SimpleUploadedFile("archive.zip", zip_buffer.read(), content_type="application/zip")

        view = FilesViewSet.as_view({"post": "zip_upload"})
        request = self.factory.post(
            f"/files/zip_upload/?group={self.group.id}",
            {"file": zip_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("files", response.data)
        mock_zip_service.assert_called_once()

    def test_zip_upload_non_zip_file_returns_400(self):
        txt_file = SimpleUploadedFile("not_a_zip.txt", b"plain text", content_type="text/plain")

        view = FilesViewSet.as_view({"post": "zip_upload"})
        request = self.factory.post(
            f"/files/zip_upload/?group={self.group.id}",
            {"file": txt_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("apps.files.views.zip_upload_service")
    def test_zip_upload_returns_400_on_bad_zip_file(self, mock_zip_service):
        mock_zip_service.side_effect = zipfile.BadZipFile("not a valid zip")

        zip_file = SimpleUploadedFile("broken.zip", b"not-a-zip-content", content_type="application/zip")

        view = FilesViewSet.as_view({"post": "zip_upload"})
        request = self.factory.post(
            f"/files/zip_upload/?group={self.group.id}",
            {"file": zip_file},
            format="multipart",
        )
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_zip_upload_returns_403_without_can_add(self):
        member = user_recipe.make(is_verified=True)
        group_user_member_recipe.make(group=self.group, user=member, can_add=False)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("hello.txt", "hello world")
        zip_buffer.seek(0)
        zip_file = SimpleUploadedFile("archive.zip", zip_buffer.read(), content_type="application/zip")

        view = FilesViewSet.as_view({"post": "zip_upload"})
        request = self.factory.post(
            f"/files/zip_upload/?group={self.group.id}",
            {"file": zip_file},
            format="multipart",
        )
        force_authenticate(request, user=member)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilesViewSetAIGenerateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        group_user_admin_recipe.make(group=self.group, user=self.user)
        self.file = file_recipe.make(group=self.group, uploaded_by=self.user, status="ready")

    @patch("apps.files.views.ai_generate_service")
    def test_ai_generate_name_returns_200(self, mock_service):
        mock_service.return_value = "Generated File Name"

        view = FilesViewSet.as_view({"patch": "ai_generate"})
        data = {"type": "name"}
        request = self.factory.patch(
            f"/files/{self.file.id}/ai_generate/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("extracted_data", response.data)
        self.assertEqual(response.data["extracted_data"], "Generated File Name")
        mock_service.assert_called_once()

    @patch("apps.files.views.ai_generate_service")
    def test_ai_generate_returns_400_on_service_exception(self, mock_service):
        mock_service.side_effect = Exception("OpenAI error")

        view = FilesViewSet.as_view({"patch": "ai_generate"})
        data = {"type": "short_description"}
        request = self.factory.patch(
            f"/files/{self.file.id}/ai_generate/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    def test_ai_generate_returns_403_when_file_status_is_generate(self):
        # CanEdit.has_object_permission returns False when status=="generate",
        # so the permission layer raises 403 before the serializer validates.
        self.file.status = "generate"
        self.file.save(update_fields=["status"])

        view = FilesViewSet.as_view({"patch": "ai_generate"})
        data = {"type": "name"}
        request = self.factory.patch(
            f"/files/{self.file.id}/ai_generate/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ai_generate_returns_403_without_can_edit(self):
        member = user_recipe.make(is_verified=True)
        group_user_member_recipe.make(group=self.group, user=member, can_edit=False)

        view = FilesViewSet.as_view({"patch": "ai_generate"})
        data = {"type": "name"}
        request = self.factory.patch(
            f"/files/{self.file.id}/ai_generate/", data, format="json"
        )
        force_authenticate(request, user=member)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_ai_generate_returns_400_for_invalid_type(self):
        view = FilesViewSet.as_view({"patch": "ai_generate"})
        data = {"type": "invalid_type"}
        request = self.factory.patch(
            f"/files/{self.file.id}/ai_generate/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(self.file.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
