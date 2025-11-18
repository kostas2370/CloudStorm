from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from apps.groups.models import Group, GroupUser, UUIDTaggedItem
from apps.users.tests.baker_recipes import user_recipe


class GroupModelTests(TestCase):
    def test_group_str_returns_name(self):
        user = user_recipe.make()
        group = Group.objects.create(name="My Group", created_by=user)

        self.assertEqual(str(group), "My Group")

    def test_group_default_values(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Default Group", created_by=user)

        self.assertFalse(group.is_private)
        self.assertEqual(group.max_size, 2000000)
        self.assertIsNotNone(group.created_at)
        self.assertIsNotNone(group.updated_at)

    def test_group_created_by_can_be_null(self):
        group = Group.objects.create(name="No Owner Group")
        self.assertIsNone(group.created_by)

    def test_group_tags_manager_uses_uuid_through_model(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Tagged Group", created_by=user)

        # Add tags via TaggableManager
        group.tags.add("important", "work")

        self.assertEqual(group.tags.count(), 2)
        self.assertIs(group.tags.through, UUIDTaggedItem)

    def test_is_user_member_returns_false_for_anonymous_user(self):
        user = AnonymousUser()
        group = Group.objects.create(name="Test Group")

        self.assertFalse(group.is_user_member(user))

    def test_is_user_member_returns_false_when_user_not_in_group(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Test Group", created_by=user)

        self.assertFalse(group.is_user_member(user))

    def test_is_user_member_returns_true_when_user_in_group(self):
        user = user_recipe.make()
        group = Group.objects.create(name="Test Group", created_by=user)

        GroupUser.objects.create(user=user, group=group, role="member")

        self.assertTrue(group.is_user_member(user))
