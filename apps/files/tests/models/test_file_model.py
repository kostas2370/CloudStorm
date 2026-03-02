from django.test import TestCase
from unittest.mock import MagicMock, patch

from apps.files.models import File, ExtractedData
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.users.tests.baker_recipes import user_recipe


class FileModelStrTests(TestCase):
    def test_str_returns_name_if_present(self):
        f = File(name="My File")
        self.assertEqual(str(f), "My File")

    def test_str_returns_fallback_if_no_name(self):
        f = File(
            id="12345678-1234-1234-1234-123456789012"
        )  # fake uuid as str ok for test
        f.name = None
        self.assertIn("File ", str(f))  # "File <id>"


class FileDataExtractionTests(TestCase):
    @patch("apps.files.models.image_data_extraction")
    def test_data_extraction_uses_correct_function_for_image(self, mock_image_extract):
        file_obj = File(file_type="image")
        mock_image_extract.return_value = {"result": "ok"}

        result = file_obj.data_extraction(prompt="describe")

        mock_image_extract.assert_called_once_with(file_obj, "describe")
        self.assertEqual(result, {"result": "ok"})

    def test_data_extraction_returns_none_for_unknown_type(self):
        file_obj = File(file_type="other")

        result = file_obj.data_extraction(prompt="whatever")

        self.assertIsNone(result)


class FileCreateExtractedDataTests(TestCase):
    @patch("apps.files.models.ExtractedData.objects.create")
    def test_create_extracted_data_calls_extracteddata_create(self, mock_create):
        file_obj = File()
        mock_create.return_value = MagicMock(spec=ExtractedData)

        res = file_obj.create_extracted_data(
            name="Summary", data="{}", hidden_from_user=True
        )

        mock_create.assert_called_once_with(
            file=file_obj, name="Summary", data="{}", hidden_from_user=True
        )
        self.assertEqual(res, mock_create.return_value)


class FileCheckUserAccessTests(TestCase):
    def test_check_user_access_public_group_always_true(self):
        group = group_recipe.make(is_private=False)
        user = user_recipe.make()

        file_obj = File(group=group)

        self.assertTrue(file_obj.check_user_access(user))

    def test_check_user_access_private_group_member_true(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        file_obj = File(group=group)

        self.assertTrue(file_obj.check_user_access(user))

    def test_check_user_access_private_group_non_member_false(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()

        file_obj = File(group=group)

        self.assertFalse(file_obj.check_user_access(user))


class FileGetMetaDataTests(TestCase):
    def test_get_meta_data_returns_empty_dict_when_no_file(self):
        file_obj = File(file=None)

        data = file_obj.get_meta_data()

        self.assertEqual(data, {})

    def test_get_meta_data_success(self):
        file_obj = File()
        file_obj.uploaded_at = MagicMock()
        file_obj.uploaded_at.strftime.return_value = "2025-11-18 12:00:00"
        file_obj.file_extension = "txt"

        # Fake file wrapper
        fake_file = MagicMock()
        fake_file.name = "uploads/test.txt"

        # .file.file.content_type
        fake_file.file = MagicMock()
        fake_file.file.content_type = "text/plain"

        # context manager for .open("rb")
        fake_fh = MagicMock()
        fake_fh.__enter__.return_value = fake_fh
        fake_fh.__exit__.return_value = None

        # seek/tell for size
        def fake_seek(offset, whence):
            return None

        def fake_tell():
            return 2048  # bytes

        fake_fh.seek.side_effect = fake_seek
        fake_fh.tell.side_effect = fake_tell

        fake_file.open.return_value = fake_fh

        file_obj.file = fake_file

        data = file_obj.get_meta_data()

        self.assertEqual(data["File Name"], "uploads/test.txt")
        self.assertEqual(data["Size (KB)"], round(2048 / 1024, 2))
        self.assertEqual(data["Uploaded At"], "2025-11-18 12:00:00")
        self.assertEqual(data["Extension"], "txt")
        self.assertEqual(data["MIME Type"], "text/plain")

    @patch("apps.files.models.logger")
    def test_get_meta_data_handles_exception_and_logs(self, mock_logger):
        file_obj = File()
        fake_file = MagicMock()
        fake_file.name = "badfile.txt"

        fake_file.open.side_effect = Exception("boom")
        file_obj.file = fake_file

        data = file_obj.get_meta_data()

        mock_logger.error.assert_called_once()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "boom")
