from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.exceptions import ValidationError

from apps.files.serializers import ZipUploadSerializer


class ZipUploadSerializerTests(TestCase):
    def _make_file(self, name, content=b"data", content_type="application/zip"):
        return SimpleUploadedFile(name, content, content_type=content_type)

    def test_valid_zip_file_passes_validation(self):
        data = {"file": self._make_file("archive.zip")}
        serializer = ZipUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_zip_file_fails_validation(self):
        data = {"file": self._make_file("document.txt", content_type="text/plain")}
        serializer = ZipUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_non_zip_error_message_is_descriptive(self):
        data = {"file": self._make_file("image.png", content_type="image/png")}
        serializer = ZipUploadSerializer(data=data)
        serializer.is_valid()

        self.assertIn("ZIP", str(serializer.errors["file"]))

    def test_file_field_is_required(self):
        serializer = ZipUploadSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_ai_enabled_defaults_to_false(self):
        data = {"file": self._make_file("bundle.zip")}
        serializer = ZipUploadSerializer(data=data)
        serializer.is_valid()

        self.assertFalse(serializer.validated_data["ai_enabled"])

    def test_tags_defaults_to_empty_string(self):
        data = {"file": self._make_file("bundle.zip")}
        serializer = ZipUploadSerializer(data=data)
        serializer.is_valid()

        self.assertEqual(serializer.validated_data["tags"], "")

    def test_tags_field_is_optional(self):
        data = {"file": self._make_file("bundle.zip"), "ai_enabled": True}
        serializer = ZipUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_tags_accepted_when_provided(self):
        data = {
            "file": self._make_file("bundle.zip"),
            "tags": "report,2024,finance",
        }
        serializer = ZipUploadSerializer(data=data)
        serializer.is_valid()

        self.assertEqual(serializer.validated_data["tags"], "report,2024,finance")

    def test_ai_enabled_true_accepted(self):
        data = {"file": self._make_file("bundle.zip"), "ai_enabled": True}
        serializer = ZipUploadSerializer(data=data)
        serializer.is_valid()

        self.assertTrue(serializer.validated_data["ai_enabled"])
