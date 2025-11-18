from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from apps.groups.serializers import GroupSerializer
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_admin_recipe,
    group_user_member_recipe,
)
from apps.groups.models import GroupUser


class GroupSerializerTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.User = get_user_model()

    def test_group_serializer_create_creates_group_and_admin_user(self):
        user = user_recipe.make()
        request = self.factory.post("/groups/")
        request.user = user

        data = {
            "name": "New Group",
            "is_private": True,
            "tags": ["t1", "t2"],
        }

        serializer = GroupSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        group = serializer.save()

        # Group assertions
        self.assertEqual(group.name, "New Group")
        self.assertTrue(group.is_private)
        self.assertEqual(group.created_by, user)
        self.assertEqual(set(group.tags.names()), {"t1", "t2"})

        # GroupUser automatically created by serializer.create
        gu = GroupUser.objects.get(group=group, user=user)
        self.assertEqual(gu.role, "admin")
        self.assertTrue(gu.can_add)
        self.assertTrue(gu.can_delete)

    def test_group_serializer_members_field(self):
        admin = user_recipe.make(username="owner")
        group = group_recipe.make(created_by=admin, name="Group With Members")

        group_user_admin_recipe.make(
            group=group,
            user=admin,
        )

        group_user_member_recipe.make(
            group=group,
            user__username="john",
        )

        request = self.factory.get("/groups/")
        request.user = admin

        serializer = GroupSerializer(instance=group, context={"request": request})
        data = serializer.data

        self.assertIn("members", data)
        self.assertEqual(len(data["members"]), 2)
        usernames = {m["username"] for m in data["members"]}
        self.assertEqual(usernames, {"owner", "john"})

    def test_group_serializer_includes_created_by_username(self):
        group = group_recipe.make(created_by__username="creator123")

        request = self.factory.get("/groups/")
        request.user = group.created_by

        serializer = GroupSerializer(instance=group, context={"request": request})

        self.assertIn("created_by_username", serializer.data)
        self.assertEqual(serializer.data["created_by_username"], "creator123")
