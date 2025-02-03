import pytest
from django.contrib.auth import get_user_model


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
