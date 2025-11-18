from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory

from apps.groups.permissions import (
    IsGroupAdmin,
    IsGroupUser,
    CanAccessPrivateGroup,
    IsVerifiedUser,
)
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_member_recipe,
    group_user_admin_recipe,
)
from apps.users.tests.baker_recipes import user_recipe
from apps.files.models import File  # μόνο για isinstance check (δεν θα σώσουμε)


User = get_user_model()


class IsGroupAdminTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsGroupAdmin()

    def test_admin_user_has_object_permission(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertTrue(has_perm)

    def test_non_admin_member_has_no_permission(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertFalse(has_perm)

    def test_non_member_has_no_permission(self):
        group = group_recipe.make()
        user = user_recipe.make()  # δεν είναι σε group_user

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertFalse(has_perm)


class IsGroupUserTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsGroupUser()

    def test_member_has_object_permission_for_group(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertTrue(has_perm)

    def test_non_member_has_no_permission_for_group(self):
        group = group_recipe.make()
        user = user_recipe.make()

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertFalse(has_perm)

    def test_member_has_permission_for_file_in_group(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        # unsaved File instance – δεν χτυπάει storage
        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(
            request, view=None, obj=file_obj
        )
        self.assertTrue(has_perm)

    def test_non_member_has_no_permission_for_file_in_group(self):
        group = group_recipe.make()
        user = user_recipe.make()

        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(
            request, view=None, obj=file_obj
        )
        self.assertFalse(has_perm)


class CanAccessPrivateGroupTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanAccessPrivateGroup()

    def test_public_group_access_allowed_for_any_user(self):
        group = group_recipe.make(is_private=False)
        user = user_recipe.make()

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertTrue(has_perm)

    def test_private_group_access_allowed_for_member(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertTrue(has_perm)

    def test_private_group_access_denied_for_non_member(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(request, view=None, obj=group)
        self.assertFalse(has_perm)

    def test_private_group_file_access_uses_file_group(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)

        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(
            request, view=None, obj=file_obj
        )
        self.assertTrue(has_perm)

    def test_private_group_file_access_denied_for_non_member(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()

        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_object_permission(
            request, view=None, obj=file_obj
        )
        self.assertFalse(has_perm)


class IsVerifiedUserTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsVerifiedUser()

    def test_verified_user_has_permission(self):
        user = user_recipe.make(is_verified=True)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_permission(request, view=None)
        self.assertTrue(has_perm)

    def test_unverified_user_has_no_permission(self):
        user = user_recipe.make(is_verified=False)

        request = self.factory.get("/")
        request.user = user

        has_perm = self.permission.has_permission(request, view=None)
        self.assertFalse(has_perm)