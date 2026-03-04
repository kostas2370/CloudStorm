from django.test import TestCase, override_settings

from apps.files.serializers import FilePartialUpdateSerializer
from apps.files.models import File
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.files.tests.baker_recipes import file_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


class FilePartialUpdateSerializerValidationTests(TestCase):
    def test_valid_name_passes_validation(self):
        data = {"name": "New Name"}
        serializer = FilePartialUpdateSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_short_description_passes_validation(self):
        data = {"short_description": "A useful file about Django."}
        serializer = FilePartialUpdateSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_valid_tags_list_passes_validation(self):
        data = {"tags": ["python", "django", "rest"]}
        serializer = FilePartialUpdateSerializer(data=data)

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_all_fields_optional(self):
        serializer = FilePartialUpdateSerializer(data={})

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_only_allowed_fields_are_present(self):
        serializer = FilePartialUpdateSerializer(data={})
        serializer.is_valid()

        allowed = {"id", "name", "tags", "short_description"}
        self.assertEqual(set(serializer.fields.keys()), allowed)

    def test_id_field_is_read_only(self):
        field = FilePartialUpdateSerializer().fields["id"]

        self.assertTrue(field.read_only)


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FilePartialUpdateSerializerSaveTests(TestCase):
    def setUp(self):
        self.user = user_recipe.make()
        self.group = group_recipe.make()
        group_user_member_recipe.make(group=self.group, user=self.user)
        self.file = file_recipe.make(
            group=self.group,
            uploaded_by=self.user,
            name="Original",
            short_description="Old description",
        )

    def test_save_updates_name(self):
        serializer = FilePartialUpdateSerializer(
            instance=self.file, data={"name": "Updated"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.file.refresh_from_db()
        self.assertEqual(self.file.name, "Updated")

    def test_save_updates_short_description(self):
        serializer = FilePartialUpdateSerializer(
            instance=self.file,
            data={"short_description": "New description"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.file.refresh_from_db()
        self.assertEqual(self.file.short_description, "New description")

    def test_save_updates_tags(self):
        serializer = FilePartialUpdateSerializer(
            instance=self.file,
            data={"tags": ["newtag", "anothertag"]},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        tag_names = set(self.file.tags.names())
        self.assertIn("newtag", tag_names)
        self.assertIn("anothertag", tag_names)

    def test_partial_update_does_not_clear_unchanged_fields(self):
        serializer = FilePartialUpdateSerializer(
            instance=self.file, data={"name": "OnlyNameChanged"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.file.refresh_from_db()
        self.assertEqual(self.file.short_description, "Old description")
