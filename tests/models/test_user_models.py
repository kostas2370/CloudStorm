from django.contrib.auth import get_user_model
import pytest
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(username="testuser", email="test@example.com", password="password123", first_name="John", last_name="Doe")
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.check_password("password123")
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.is_verified is False


@pytest.mark.django_db
def test_user_str():
    user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
    assert str(user) == "testuser"


@pytest.mark.django_db
def test_user_full_name():
    user = User.objects.create_user(username="testuser", email="test@example.com", first_name="John", last_name="Doe", password="password123")
    assert user.get_full_name() == "John Doe"


@pytest.mark.django_db
def test_user_short_name():
    user = User.objects.create_user(username="testuser", email="test@example.com", first_name="John", last_name="Doe", password="password123")
    assert user.get_short_name() == "John"


@pytest.mark.django_db
def test_get_tokens():
    user = User.objects.create_user(username="testuser", email="test@example.com", password="password123")
    tokens = user.get_tokens()
    assert "access" in tokens
    assert "refresh" in tokens
    assert isinstance(tokens["access"], str)
    assert isinstance(tokens["refresh"], str)


@pytest.mark.django_db
def test_user_creation_invalid_email():
    user = User(username="testuser", email="invalidemail", password="password123")
    with pytest.raises(ValidationError):
        user.full_clean()
