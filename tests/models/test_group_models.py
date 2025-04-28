import pytest
from django.contrib.auth import get_user_model
from apps.groups.models import Group, GroupUser


@pytest.mark.django_db
def test_group_creation():
    group = Group.objects.create(name="Test Group")
    assert group.name == "Test Group"
    assert group.is_private is False
    assert group.passcode is None
    assert group.max_size == 2000000


@pytest.mark.django_db
def test_group_passcode():
    passcode = "secure123"
    group = Group.objects.create(name="Private Group", passcode=passcode)
    assert group.passcode != passcode


@pytest.mark.django_db
def test_group_check_passcode():
    group = Group.objects.create(
        name="Private Group", passcode="secure123", is_private=True
    )
    assert group.check_passcode("secure123") is True
    assert group.check_passcode("wrongpass") is False


@pytest.mark.django_db
def test_group_user_relationship():
    user = get_user_model().objects.create_user(
        username="testuser", password="password"
    )
    group = Group.objects.create(name="Test Group")
    group_user = GroupUser.objects.create(user=user, group=group, role="admin")
    assert group_user.user == user
    assert group_user.group == group
    assert group_user.role == "admin"


@pytest.mark.django_db
def test_group_is_user_member():
    user = get_user_model().objects.create_user(
        username="testuser", password="password"
    )
    group = Group.objects.create(name="Test Group")
    assert group.is_user_member(user) is False
    GroupUser.objects.create(user=user, group=group)
    assert group.is_user_member(user) is True
