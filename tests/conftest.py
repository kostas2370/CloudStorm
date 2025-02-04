import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.groups.models import Group, GroupUser

user_data: dict = dict(username = "kostas2370", email = "kostas2372@gmail.com", password = "Pass1234!")


@pytest.fixture
def user():
    user = get_user_model().objects.create(**user_data, is_verified = True)
    user.set_password("Pass1234!")
    user.save()
    return user


@pytest.fixture
def unverified_user():
    user = get_user_model().objects.create(**user_data, is_verified = False)
    user.set_password("Pass1234!")
    user.save()
    return user


@pytest.fixture
def authenticated_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def private_group(user):
    group = Group.objects.create(name="Test Group", is_private = True, passcode = "test", tags = [])
    GroupUser.objects.create(role = "admin", user = user, group = group)
    return group


@pytest.fixture
def public_group(user):
    group = Group.objects.create(name="Test Group2", is_private = False, passcode = None, tags = [])
    GroupUser.objects.create(role = "admin", user = user, group = group)
    return group


@pytest.fixture
def group_without_users():
    group = Group.objects.create(name="Test Group", is_private = True, passcode = "test", tags = [])
    return group


@pytest.fixture
def group_with_member_user(user):
    group = Group.objects.create(name="Test Group", is_private = True, passcode = "test", tags = [])
    GroupUser.objects.create(role = "member", user = user, group = group)
    return group
