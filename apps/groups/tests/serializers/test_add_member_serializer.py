from django.test import TestCase
from apps.groups.serializers import AddMemberSerializer
from apps.groups.tests.baker_recipes import group_recipe, group_user_member_recipe
from apps.users.tests.baker_recipes import user_recipe


class AddMemberSerializerTests(TestCase):
    def test_validate_user_email_no_user(self):
        group = group_recipe.make()

        serializer = AddMemberSerializer(
            data={"user_email": "nouser@example.com"},
            context={"group": group},
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("user_email", serializer.errors)
        self.assertIn(
            "No user with this email exists.",
            serializer.errors["user_email"][0],
        )

    def test_validate_user_email_already_member(self):
        group = group_recipe.make()
        user = user_recipe.make(email="member@example.com")
        group_user_member_recipe.make(group=group, user=user)

        serializer = AddMemberSerializer(
            data={"user_email": user.email}, context={"group": group}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("user_email", serializer.errors)
        self.assertIn(
            "User is already a member of this group.",
            serializer.errors["user_email"][0],
        )

    def test_add_member_creates_member_with_defaults(self):
        group = group_recipe.make()
        new_user = user_recipe.make(email="newuser@example.com")

        serializer = AddMemberSerializer(
            data={"user_email": new_user.email},
            context={"group": group},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        group_user = serializer.save()

        self.assertEqual(group_user.group, group)
        self.assertEqual(group_user.user, new_user)
        self.assertEqual(group_user.role, "member")
        self.assertFalse(group_user.can_add)
        self.assertFalse(group_user.can_delete)

    def test_add_member_respects_role_and_permissions(self):
        group = group_recipe.make()
        new_user = user_recipe.make(email="adminuser@example.com")

        serializer = AddMemberSerializer(
            data={
                "user_email": new_user.email,
                "role": "admin",
                "can_add": True,
                "can_delete": True,
            },
            context={"group": group},
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        group_user = serializer.save()

        self.assertEqual(group_user.group, group)
        self.assertEqual(group_user.user, new_user)
        self.assertEqual(group_user.role, "admin")
        self.assertTrue(group_user.can_add)
        self.assertTrue(group_user.can_delete)
