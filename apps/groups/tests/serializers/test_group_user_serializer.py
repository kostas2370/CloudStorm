from django.test import TestCase

from apps.groups.serializers import GroupUserSerializer

from apps.groups.tests.baker_recipes import (
    group_user_member_recipe,
)


class GroupUserSerializerTests(TestCase):
    def test_group_user_serializer_includes_username(self):
        member = group_user_member_recipe.make(
            user__username="testuser", group__name="Test Group"
        )

        serializer = GroupUserSerializer(member)

        self.assertEqual(serializer.data["username"], "testuser")
        self.assertNotIn("id", serializer.data)
        self.assertNotIn("group", serializer.data)
