import pytest


@pytest.mark.django_db
def test_create_group(authenticated_client):
    payload = dict(name="Test Group", passcode=1234, is_private=True, tags=["aek"])
    response = authenticated_client.post("/api/groups/", payload)
    assert response.status_code == 201
    assert response.data["name"] == "Test Group"


@pytest.mark.django_db
def test_list_groups(authenticated_client, private_group):
    response = authenticated_client.get("/api/groups/")
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_retrieve_group(authenticated_client, public_group):
    response = authenticated_client.get(f"/api/groups/{public_group.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "Test Group2"


@pytest.mark.django_db
def test_private_group_access(authenticated_client, private_group):
    response = authenticated_client.get(
        f"/api/groups/{private_group.id}/?passcode=test"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_group(authenticated_client, public_group):
    response = authenticated_client.delete(f"/api/groups/{public_group.id}/")
    assert response.status_code == 204


@pytest.mark.django_db
def test_update_group(authenticated_client, private_group):
    response = authenticated_client.patch(
        f"/api/groups/{private_group.id}/", {"name": "Updated Group"}
    )
    assert response.status_code == 200
    assert response.data["name"] == "Updated Group"


@pytest.mark.django_db
def test_non_member_cannot_access_private_group(
    authenticated_client, group_without_users
):
    response = authenticated_client.get(
        f"/api/groups/{group_without_users.id}/?passcode=test"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_non_admin_cannot_delete_group(authenticated_client, group_with_member_user):
    response = authenticated_client.delete(
        f"/api/groups/{group_with_member_user.id}/?passcode=test"
    )
    assert response.status_code == 403
