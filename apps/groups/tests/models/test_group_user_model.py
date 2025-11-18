from django.test import TestCase
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_member_recipe,
    group_user_admin_recipe,
)
from apps.groups.models import Group, GroupUser

from django.db import IntegrityError


class GroupUserModelTests(TestCase):
    def test_group_user_str(self):
        user = user_recipe.make(username="testuser")
        group = Group.objects.create(name="GroupName", created_by=user)

        group_user = GroupUser.objects.create(
            user=user,
            group=group,
            role="member",
        )

        self.assertEqual(str(group_user), "testuser" + "GroupName")

    def test_group_user_default_role_and_permissions(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Permissions Group", created_by=user)

        group_user = GroupUser.objects.create(user=user, group=group)

        self.assertEqual(group_user.role, "member")
        self.assertFalse(group_user.can_add)
        self.assertFalse(group_user.can_delete)
        self.assertFalse(group_user.can_edit)

    def test_group_user_unique_together_user_group(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Unique Group", created_by=user)

        GroupUser.objects.create(user=user, group=group, role="member")

        with self.assertRaises(IntegrityError):
            GroupUser.objects.create(user=user, group=group, role="admin")
