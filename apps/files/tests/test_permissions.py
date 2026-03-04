from unittest.mock import MagicMock

from django.test import TestCase, override_settings

from rest_framework.test import APIRequestFactory

from apps.files.permissions import (
    CanDelete,
    CanAdd,
    CanEdit,
    CanRetrieve,
    CanMassDelete,
    FileAccessPermission,
)
from apps.files.models import File
from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_member_recipe,
    group_user_admin_recipe,
)
from apps.files.tests.baker_recipes import file_recipe
from apps.files.tests.conftest import IN_MEMORY_STORAGES


class CanDeleteTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanDelete()

    def test_user_with_can_delete_returns_true(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_delete=True)
        file_obj = File(group=group, status="ready")

        request = self.factory.delete("/")
        request.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, file_obj))

    def test_user_without_can_delete_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user, can_delete=False)
        file_obj = File(group=group, status="ready")

        request = self.factory.delete("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))

    def test_non_member_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        file_obj = File(group=group, status="ready")

        request = self.factory.delete("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))

    def test_returns_false_when_status_is_generate(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_delete=True)
        file_obj = File(group=group, status="generate")

        request = self.factory.delete("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))

    def test_message_changes_when_status_is_generate(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_delete=True)
        file_obj = File(group=group, status="generate")

        request = self.factory.delete("/")
        request.user = user

        self.permission.has_object_permission(request, None, file_obj)

        self.assertIn("generate", self.permission.message)


class CanAddTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanAdd()

    def _make_request(self, user, group_id):
        request = self.factory.post(f"/?group={group_id}")
        request.user = user
        request.query_params = {"group": str(group_id)}
        return request

    def test_admin_can_add(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user)

        request = self._make_request(user, group.id)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_member_with_can_add_true_returns_true(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user, can_add=True)

        request = self._make_request(user, group.id)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_member_with_can_add_false_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user, can_add=False)

        request = self._make_request(user, group.id)

        self.assertFalse(self.permission.has_permission(request, None))

    def test_non_member_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()

        request = self._make_request(user, group.id)

        self.assertFalse(self.permission.has_permission(request, None))

    def test_missing_group_param_returns_false(self):
        user = user_recipe.make()
        request = self.factory.post("/")
        request.user = user
        request.query_params = {}

        self.assertFalse(self.permission.has_permission(request, None))


class CanEditTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanEdit()

    def test_user_with_can_edit_returns_true(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_edit=True)
        file_obj = File(group=group, status="ready")

        request = self.factory.patch("/")
        request.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, file_obj))

    def test_user_without_can_edit_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user, can_edit=False)
        file_obj = File(group=group, status="ready")

        request = self.factory.patch("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))

    def test_non_member_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        file_obj = File(group=group, status="ready")

        request = self.factory.patch("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))

    def test_returns_false_when_status_is_generate(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_edit=True)
        file_obj = File(group=group, status="generate")

        request = self.factory.patch("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))


class CanRetrieveTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanRetrieve()

    def test_group_member_can_retrieve_private_file(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user)
        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, file_obj))

    def test_non_member_can_retrieve_public_group_file(self):
        group = group_recipe.make(is_private=False)
        user = user_recipe.make()
        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        self.assertTrue(self.permission.has_object_permission(request, None, file_obj))

    def test_non_member_cannot_retrieve_private_group_file(self):
        group = group_recipe.make(is_private=True)
        user = user_recipe.make()
        file_obj = File(group=group)

        request = self.factory.get("/")
        request.user = user

        self.assertFalse(self.permission.has_object_permission(request, None, file_obj))


class CanMassDeleteTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = CanMassDelete()

    def _make_request(self, user, group_id=None):
        request = self.factory.delete("/")
        request.user = user
        request.query_params = {"group": str(group_id)} if group_id else {}
        return request

    def test_member_with_can_delete_and_group_param_returns_true(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_admin_recipe.make(group=group, user=user, can_delete=True)

        request = self._make_request(user, group.id)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_member_without_can_delete_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()
        group_user_member_recipe.make(group=group, user=user, can_delete=False)

        request = self._make_request(user, group.id)

        self.assertFalse(self.permission.has_permission(request, None))

    def test_missing_group_param_returns_false(self):
        user = user_recipe.make()

        request = self._make_request(user, group_id=None)

        self.assertFalse(self.permission.has_permission(request, None))

    def test_non_member_returns_false(self):
        group = group_recipe.make()
        user = user_recipe.make()

        request = self._make_request(user, group.id)

        self.assertFalse(self.permission.has_permission(request, None))


@override_settings(STORAGES=IN_MEMORY_STORAGES)
class FileAccessPermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = FileAccessPermission()

    def _make_request(self, user, group_name, filename):
        request = self.factory.get(f"/files/media/{group_name}/{filename}/")
        request.user = user
        request.resolver_match = MagicMock()
        request.resolver_match.kwargs = {
            "group_name": group_name,
            "filename": filename,
        }
        return request

    def test_public_group_file_accessible_to_any_authenticated_user(self):
        group = group_recipe.make(is_private=False)
        owner = user_recipe.make()
        group_user_member_recipe.make(group=group, user=owner)
        file_obj = file_recipe.make(group=group, uploaded_by=owner)

        filename = file_obj.file.name.split("/")[-1]
        user = user_recipe.make()
        request = self._make_request(user, group.name, filename)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_private_group_file_accessible_to_member(self):
        group = group_recipe.make(is_private=True)
        member = user_recipe.make()
        group_user_member_recipe.make(group=group, user=member)
        file_obj = file_recipe.make(group=group, uploaded_by=member)

        filename = file_obj.file.name.split("/")[-1]
        request = self._make_request(member, group.name, filename)

        self.assertTrue(self.permission.has_permission(request, None))

    def test_private_group_file_not_accessible_to_non_member(self):
        group = group_recipe.make(is_private=True)
        owner = user_recipe.make()
        group_user_member_recipe.make(group=group, user=owner)
        file_obj = file_recipe.make(group=group, uploaded_by=owner)

        filename = file_obj.file.name.split("/")[-1]
        outsider = user_recipe.make()
        request = self._make_request(outsider, group.name, filename)

        self.assertFalse(self.permission.has_permission(request, None))
