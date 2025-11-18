from django.test import TestCase
from apps.groups.serializers import GroupListsSerializer
from apps.groups.tests.baker_recipes import group_recipe


class GroupListsSerializerTests(TestCase):
    def test_group_lists_serializer_includes_fields(self):
        group = group_recipe.make(created_by__username="creatorX")
        group.tags.add("a", "b")

        serializer = GroupListsSerializer(group)
        data = serializer.data

        self.assertIn("created_by_username", data)
        self.assertEqual(data["created_by_username"], "creatorX")
        self.assertIn("tags", data)
        self.assertCountEqual(data["tags"], ["a", "b"])
        self.assertIn("name", data)
        self.assertEqual(data["name"], group.name)
