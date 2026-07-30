from unittest.mock import patch

from django.test import TestCase

from apps.files.exceptions import (
    FileAlreadyGenerating,
    GenerationFailed,
    UnsupportedFileType,
)
from apps.files.models import File
from apps.files.services import ai_generate_service
from apps.groups.tests.baker_recipes import group_recipe
from apps.users.tests.baker_recipes import user_recipe


class AIGenerateServiceTests(TestCase):
    def setUp(self):
        self.file = File.objects.create(
            name="photo.png",
            file_type=File.FileType.IMAGE,
            group=group_recipe.make(),
            uploaded_by=user_recipe.make(),
        )

    def refreshed_status(self):
        return File.objects.get(pk=self.file.pk).status

    def test_rejects_file_types_that_cannot_be_extracted(self):
        self.file.file_type = File.FileType.OTHER

        with self.assertRaises(UnsupportedFileType):
            ai_generate_service(self.file, {"type": "tags"})

        self.assertEqual(self.refreshed_status(), File.FileStatus.READY)

    def test_rejects_a_file_that_is_already_generating(self):
        File.objects.filter(pk=self.file.pk).update(status=File.FileStatus.GENERATE)

        with self.assertRaises(FileAlreadyGenerating):
            ai_generate_service(self.file, {"type": "tags"})

    @patch("apps.files.services.generate_short_description", return_value="a photo")
    def test_saves_only_the_generated_field_and_status(self, _mock_generate):
        with self.assertNumQueries(3):  # claim, update, and the status re-read below
            ai_generate_service(self.file, {"type": "short_description"})
            self.refreshed_status()

        saved = File.objects.get(pk=self.file.pk)
        self.assertEqual(saved.short_description, "a photo")
        self.assertEqual(saved.status, File.FileStatus.READY)

    @patch("apps.files.services.generate_filename", return_value="better-name.png")
    def test_does_not_overwrite_fields_changed_by_someone_else(self, _mock_generate):
        # A concurrent update lands after this request loaded the file.
        File.objects.filter(pk=self.file.pk).update(short_description="set elsewhere")

        ai_generate_service(self.file, {"type": "name"})

        saved = File.objects.get(pk=self.file.pk)
        self.assertEqual(saved.name, "better-name.png")
        self.assertEqual(saved.short_description, "set elsewhere")

    @patch("apps.files.services.generate_tags", return_value=["holiday", "beach"])
    def test_adds_generated_tags(self, _mock_generate):
        extracted_data = ai_generate_service(self.file, {"type": "tags"})

        self.assertEqual(extracted_data, ["holiday", "beach"])
        self.assertCountEqual(
            self.file.tags.names(),
            ["holiday", "beach"],
        )
        self.assertEqual(self.refreshed_status(), File.FileStatus.READY)

    @patch("apps.files.services.extract_data", return_value="42")
    def test_runs_custom_extraction_with_the_user_prompt(self, mock_extract):
        extracted_data = ai_generate_service(
            self.file, {"type": "custom", "user_prompt": "the invoice total"}
        )

        mock_extract.assert_called_once_with(self.file, "the invoice total")
        self.assertEqual(extracted_data, "42")

    @patch("apps.files.services.generate_short_description", return_value=None)
    def test_fails_when_the_model_returns_nothing(self, _mock_generate):
        with self.assertRaises(GenerationFailed):
            ai_generate_service(self.file, {"type": "short_description"})

        saved = File.objects.get(pk=self.file.pk)
        self.assertEqual(saved.status, File.FileStatus.READY)
        self.assertIsNone(saved.short_description)

    @patch(
        "apps.files.services.generate_tags", side_effect=RuntimeError("openai is down")
    )
    def test_resets_status_and_reraises_on_failure(self, _mock_generate):
        with self.assertRaises(RuntimeError):
            ai_generate_service(self.file, {"type": "tags"})

        self.assertEqual(self.refreshed_status(), File.FileStatus.READY)
