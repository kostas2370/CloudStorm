from django.test import TestCase

from rest_framework.exceptions import ValidationError

from apps.files.serializers import AIGenerateSerializer
from apps.files.models import File


class AIGenerateSerializerValidationTests(TestCase):
    def _serialize(self, data, context=None):
        return AIGenerateSerializer(data=data, context=context or {})

    def test_type_name_is_valid(self):
        serializer = self._serialize({"type": "name"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_type_short_description_is_valid(self):
        serializer = self._serialize({"type": "short_description"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_type_tags_is_valid(self):
        serializer = self._serialize({"type": "tags"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_type_custom_is_valid(self):
        serializer = self._serialize({"type": "custom"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_type_fails_validation(self):
        serializer = self._serialize({"type": "unknown_type"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_type_field_is_required(self):
        serializer = self._serialize({})
        self.assertFalse(serializer.is_valid())
        self.assertIn("type", serializer.errors)

    def test_user_prompt_is_optional(self):
        serializer = self._serialize({"type": "custom"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_prompt_accepted_when_provided(self):
        serializer = self._serialize(
            {"type": "custom", "user_prompt": "Extract invoice number"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["user_prompt"], "Extract invoice number"
        )

    def test_target_format_is_optional(self):
        serializer = self._serialize({"type": "name"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_target_format_accepted_when_provided(self):
        serializer = self._serialize(
            {"type": "name", "target_format": "{date}_{title}"}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["target_format"], "{date}_{title}"
        )

    def test_blank_user_prompt_is_allowed(self):
        serializer = self._serialize({"type": "custom", "user_prompt": ""})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_blank_target_format_is_allowed(self):
        serializer = self._serialize({"type": "name", "target_format": ""})
        self.assertTrue(serializer.is_valid(), serializer.errors)


class AIGenerateSerializerFileStatusTests(TestCase):
    def test_raises_validation_error_when_file_status_is_generate(self):
        file_obj = File(status="generate")
        serializer = AIGenerateSerializer(
            data={"type": "name"},
            context={"file_obj": file_obj},
        )

        with self.assertRaises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        self.assertIn("generate", str(exc.exception.detail))

    def test_passes_validation_when_file_status_is_ready(self):
        file_obj = File(status="ready")
        serializer = AIGenerateSerializer(
            data={"type": "name"},
            context={"file_obj": file_obj},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_passes_validation_when_no_file_in_context(self):
        serializer = AIGenerateSerializer(
            data={"type": "tags"},
            context={},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
