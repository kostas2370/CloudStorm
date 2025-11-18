from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from unittest.mock import patch, MagicMock

from apps.groups.views import GroupsViewSet
from apps.groups.models import GroupUser

from apps.users.tests.baker_recipes import user_recipe
from apps.groups.tests.baker_recipes import (
    group_recipe,
    group_user_member_recipe,
    group_user_admin_recipe,
)


User = get_user_model()


class GroupsViewSetTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = user_recipe.make(is_verified=True)

    def test_list_returns_only_groups_where_user_is_member(self):
        group1 = group_recipe.make(name="My Group 1")
        group2 = group_recipe.make(name="Other Group")

        group_user_member_recipe.make(group=group1, user=self.user)

        other_user = user_recipe.make()
        group_user_member_recipe.make(group=group2, user=other_user)

        view = GroupsViewSet.as_view({"get": "list"})
        request = self.factory.get("/groups/")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {g["name"] for g in response.data}
        self.assertIn("My Group 1", names)
        self.assertNotIn("Other Group", names)

    def test_create_group_creates_group_and_admin_membership(self):
        view = GroupsViewSet.as_view({"post": "create"})
        data = {
            "name": "New Group",
            "is_private": True,
            "tags": ["tag1", "tag2"],
        }

        request = self.factory.post("/groups/", data, format="json")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group_id = response.data["id"]

        group_user = GroupUser.objects.get(group__id=group_id, user=self.user)
        self.assertEqual(group_user.role, "admin")
        self.assertTrue(group_user.can_add)
        self.assertTrue(group_user.can_delete)

    @patch("apps.groups.views.send_email")
    def test_add_member_adds_user_and_sends_email(self, mock_send_email):
        group = group_recipe.make(created_by=self.user)
        # ο requester πρέπει να είναι admin
        group_user_admin_recipe.make(group=group, user=self.user)

        new_user = user_recipe.make(email="newmember@example.com", is_verified=True)

        view = GroupsViewSet.as_view({"post": "add_member"})
        data = {"user_email": new_user.email}
        request = self.factory.post(
            f"/groups/{group.id}/add_member/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(group.id))

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(GroupUser.objects.filter(group=group, user=new_user).exists())
        mock_send_email.delay.assert_called_once()

    def test_add_member_fails_if_user_already_member(self):
        group = group_recipe.make(created_by=self.user)
        group_user_admin_recipe.make(group=group, user=self.user)

        member_user = user_recipe.make(email="member@example.com")
        group_user_member_recipe.make(group=group, user=member_user)

        view = GroupsViewSet.as_view({"post": "add_member"})
        data = {"user_email": member_user.email}
        request = self.factory.post(
            f"/groups/{group.id}/add_member/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(group.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_email", response.data)
        self.assertIn(
            "User is already a member of this group.",
            response.data["user_email"][0],
        )

    @patch("apps.groups.views.send_email")
    def test_remove_member_removes_user_from_group(self, mock_send_email):
        group = group_recipe.make(created_by=self.user)
        admin_membership = group_user_admin_recipe.make(group=group, user=self.user)

        member_user = user_recipe.make()
        member_membership = group_user_member_recipe.make(group=group, user=member_user)

        view = GroupsViewSet.as_view({"delete": "remove_member"})

        request = self.factory.delete(
            f"/groups/{group.id}/remove_member/?user_id={member_user.id}"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(group.id))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(GroupUser.objects.filter(id=member_membership.id).exists())
        mock_send_email.delay.assert_called_once()

    def test_remove_member_cannot_remove_other_admin(self):
        group = group_recipe.make(created_by=self.user)
        group_user_admin_recipe.make(group=group, user=self.user)

        other_admin = user_recipe.make()
        other_admin_membership = group_user_admin_recipe.make(
            group=group, user=other_admin
        )

        view = GroupsViewSet.as_view({"delete": "remove_member"})

        request = self.factory.delete(
            f"/groups/{group.id}/remove_member/?user_id={other_admin.id}"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(group.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(GroupUser.objects.filter(id=other_admin_membership.id).exists())

    def test_edit_members_updates_roles_and_permissions(self):
        group = group_recipe.make(created_by=self.user)
        group_user_admin_recipe.make(group=group, user=self.user)

        target_user = user_recipe.make()
        membership = group_user_member_recipe.make(
            group=group,
            user=target_user,
            role="member",
            can_add=False,
            can_delete=False,
        )

        view = GroupsViewSet.as_view({"put": "edit_members"})

        data = [
            {
                "user_id": str(target_user.id),
                "role": "admin",
                "can_add": True,
                "can_delete": True,
            }
        ]

        request = self.factory.put(
            f"/groups/{group.id}/edit_members/", data, format="json"
        )
        force_authenticate(request, user=self.user)

        response = view(request, pk=str(group.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        membership.refresh_from_db()
        self.assertEqual(membership.role, "admin")
        self.assertTrue(membership.can_add)
        self.assertTrue(membership.can_delete)


@patch("apps.groups.views.BlobServiceClient")
@patch("apps.files.models.File.save", autospec=True)
def test_download_zip_returns_zip_response(
    self, mock_file_save, mock_blob_service_client
):
    from apps.files.models import File

    group = group_recipe.make(created_by=self.user)
    group_user_member_recipe.make(group=group, user=self.user)

    file_obj = File.objects.create(
        group=group,
        name="test.txt",
        file="uploads/test.txt",
        uploaded_by=self.user,
    )

    mock_client_instance = MagicMock()
    mock_blob_service_client.from_connection_string.return_value = mock_client_instance

    mock_blob = MagicMock()
    mock_client_instance.get_blob_client.return_value = mock_blob
    mock_blob.download_blob.return_value.readall.return_value = b"dummy content"

    view = GroupsViewSet.as_view({"get": "download_zip"})
    request = self.factory.get(f"/groups/{group.id}/download_zip/")
    force_authenticate(request, user=self.user)

    response = view(request, pk=str(group.id))

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response["Content-Type"], "application/zip")
    self.assertIn("group_", response["Content-Disposition"])
