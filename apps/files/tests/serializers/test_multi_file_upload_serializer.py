from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APIRequestFactory

from apps.files.serializers import MultiFileUploadSerializer
from apps.files.models import File
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


class MultiFileUploadSerializerValidationTests(TestCase):
    def _make_dummy_file(self, name="test.txt"):
        return SimpleUploadedFile(name, b"content", content_type="text/plain")

    def test_valid_data_with_single_file_passes_validation(self):
        data = {"files": [self._make_dummy_file()], "ai_enabled": False}
        serializer = MultiFileUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_data_with_multiple_files_passes_validation(self):
        files = [self._make_dummy_file("a.txt"), self._make_dummy_file("b.txt")]
        data = {"files": files, "ai_enabled": False}
        serializer = MultiFileUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_ai_enabled_defaults_to_false(self):
        data = {"files": [self._make_dummy_file()]}
        serializer = MultiFileUploadSerializer(data=data)
        serializer.is_valid()

        self.assertFalse(serializer.validated_data["ai_enabled"])

    def test_tags_field_is_optional(self):
        data = {"files": [self._make_dummy_file()], "ai_enabled": False}
        serializer = MultiFileUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_tags_field_accepted_when_provided(self):
        data = {
            "files": [self._make_dummy_file()],
            "tags": "python,django",
            "ai_enabled": False,
        }
        serializer = MultiFileUploadSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["tags"], "python,django")

    def test_files_field_is_required(self):
        data = {"ai_enabled": False}
        serializer = MultiFileUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("files", serializer.errors)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class MultiFileUploadSerializerCreateTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)
        self.group = group_recipe.make()
        group_user_member_recipe.make(group=self.group, user=self.user)

    def _make_context(self):
        request = self.factory.post("/")
        request.user = self.user
        return {"request": request, "group": str(self.group.id)}

    @patch("apps.files.serializers.group")
    @patch("apps.files.serializers.process_file")
    def test_create_bulk_creates_file_instances(self, mock_process_file, mock_group):
        mock_group.return_value = MagicMock()
        mock_group.return_value.apply_async.return_value = None
        mock_process_file.s.return_value = MagicMock()

        dummy = SimpleUploadedFile("upload.txt", b"data", content_type="text/plain")
        data = {"files": [dummy], "ai_enabled": False}

        serializer = MultiFileUploadSerializer(data=data, context=self._make_context())
        self.assertTrue(serializer.is_valid(), serializer.errors)

        result = serializer.save()

        self.assertEqual(len(result), 1)
        self.assertTrue(File.objects.filter(uploaded_by=self.user).exists())

    @patch("apps.files.serializers.group")
    @patch("apps.files.serializers.process_file")
    def test_create_dispatches_celery_task_for_each_file(
        self, mock_process_file, mock_group
    ):
        mock_task_group = MagicMock()
        # celery.group receives a generator expression; MagicMock won't iterate
        # it, so process_file.s() would never be called. The side_effect forces
        # the generator to be consumed before returning the mock task group.
        mock_group.side_effect = lambda tasks: (list(tasks), mock_task_group)[1]

        files = [
            SimpleUploadedFile("f1.txt", b"a", content_type="text/plain"),
            SimpleUploadedFile("f2.txt", b"b", content_type="text/plain"),
        ]
        data = {"files": files, "ai_enabled": True, "tags": "tag1,tag2"}

        serializer = MultiFileUploadSerializer(data=data, context=self._make_context())
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        mock_task_group.apply_async.assert_called_once()
        self.assertEqual(mock_process_file.s.call_count, 2)

    @patch("apps.files.serializers.group")
    @patch("apps.files.serializers.process_file")
    def test_create_assigns_uploaded_by_from_request_user(
        self, mock_process_file, mock_group
    ):
        mock_group.return_value = MagicMock()
        mock_group.return_value.apply_async.return_value = None

        dummy = SimpleUploadedFile("doc.txt", b"x", content_type="text/plain")
        data = {"files": [dummy], "ai_enabled": False}

        serializer = MultiFileUploadSerializer(data=data, context=self._make_context())
        serializer.is_valid()
        result = serializer.save()

        created = File.objects.get(id=result[0].id)
        self.assertEqual(created.uploaded_by, self.user)
