from unittest.mock import MagicMock

from django.test import TestCase, override_settings
from django.conf import settings

from rest_framework.test import APIRequestFactory

from apps.files.serializers import (
    AzureBlobFileField,
    FileSerializer,
    FileListSerializer,
    ExtractedDataSerializer,
)
from apps.files.models import ExtractedData
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.files.tests.baker_recipes import file_recipe, extracted_data_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


class AzureBlobFileFieldTests(TestCase):
    def setUp(self):
        self.field = AzureBlobFileField()

    def test_returns_none_when_value_is_none(self):
        result = self.field.to_representation(None)
        self.assertIsNone(result)

    def test_returns_proxy_url_with_correct_structure(self):
        mock_value = MagicMock()
        mock_value.name = "uploads/mygroup/report.pdf"

        result = self.field.to_representation(mock_value)

        self.assertIn("/api/files/media/", result)
        self.assertIn("mygroup", result)
        self.assertIn("report.pdf", result)

    def test_returns_url_with_base_url(self):
        mock_value = MagicMock()
        mock_value.name = "uploads/testgroup/photo.png"

        result = self.field.to_representation(mock_value)

        self.assertTrue(result.startswith(settings.BASE_URL))

    def test_url_uses_group_name_as_second_segment(self):
        mock_value = MagicMock()
        mock_value.name = "uploads/alpha/document.docx"

        result = self.field.to_representation(mock_value)

        expected = f"{settings.BASE_URL}/api/files/media/alpha/document.docx"
        self.assertEqual(result, expected)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FileSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        group_user_member_recipe.make(group=self.group, user=self.user)

    def test_includes_group_name(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)
        request = self.factory.get("/")
        request.user = self.user

        serializer = FileSerializer(instance=file_obj, context={"request": request})
        data = serializer.data

        self.assertIn("group_name", data)
        self.assertEqual(data["group_name"], self.group.name)

    def test_get_extracted_data_excludes_hidden_items(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)
        extracted_data_recipe.make(
            file=file_obj, name="visible", hidden_from_user=False
        )
        extracted_data_recipe.make(file=file_obj, name="hidden", hidden_from_user=True)

        request = self.factory.get("/")
        request.user = self.user

        serializer = FileSerializer(instance=file_obj, context={"request": request})
        extracted = serializer.data["extracted_data"]

        names = [item["name"] for item in extracted]
        self.assertIn("visible", names)
        self.assertNotIn("hidden", names)

    def test_get_extracted_data_includes_all_visible_items(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)
        extracted_data_recipe.make(file=file_obj, name="item1", hidden_from_user=False)
        extracted_data_recipe.make(file=file_obj, name="item2", hidden_from_user=False)

        request = self.factory.get("/")
        request.user = self.user

        serializer = FileSerializer(instance=file_obj, context={"request": request})
        extracted = serializer.data["extracted_data"]

        self.assertEqual(len(extracted), 2)

    def test_extracted_data_is_empty_list_when_no_extractions(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        request = self.factory.get("/")
        request.user = self.user

        serializer = FileSerializer(instance=file_obj, context={"request": request})

        self.assertEqual(serializer.data["extracted_data"], [])

    def test_file_field_returns_proxy_url(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        request = self.factory.get("/")
        request.user = self.user

        serializer = FileSerializer(instance=file_obj, context={"request": request})
        file_url = serializer.data["file"]

        self.assertIn("/api/files/media/", file_url)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FileListSerializerTests(TestCase):
    def setUp(self):
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        group_user_member_recipe.make(group=self.group, user=self.user)

    def test_includes_group_name(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        serializer = FileListSerializer(instance=file_obj)
        data = serializer.data

        self.assertIn("group_name", data)
        self.assertEqual(data["group_name"], self.group.name)

    def test_file_field_returns_proxy_url(self):
        file_obj = file_recipe.make(group=self.group, uploaded_by=self.user)

        serializer = FileListSerializer(instance=file_obj)
        file_url = serializer.data["file"]

        self.assertIn("/api/files/media/", file_url)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class ExtractedDataSerializerTests(TestCase):
    def setUp(self):
        self.user = user_recipe.make()
        self.group = group_recipe.make()
        group_user_member_recipe.make(group=self.group, user=self.user)

    def test_excludes_file_field(self):
        item = extracted_data_recipe.make()

        serializer = ExtractedDataSerializer(instance=item)

        self.assertNotIn("file", serializer.data)

    def test_excludes_hidden_from_user_field(self):
        item = extracted_data_recipe.make()

        serializer = ExtractedDataSerializer(instance=item)

        self.assertNotIn("hidden_from_user", serializer.data)

    def test_includes_name_and_data_fields(self):
        item = extracted_data_recipe.make(name="Summary", data="some text")

        serializer = ExtractedDataSerializer(instance=item)
        data = serializer.data

        self.assertIn("name", data)
        self.assertIn("data", data)
        self.assertEqual(data["name"], "Summary")
        self.assertEqual(data["data"], "some text")

    def test_includes_extraction_date(self):
        item = extracted_data_recipe.make()

        serializer = ExtractedDataSerializer(instance=item)

        self.assertIn("extraction_date", serializer.data)
