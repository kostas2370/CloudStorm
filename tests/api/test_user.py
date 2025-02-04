import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import jwt
from datetime import datetime, timedelta

client = APIClient()


@pytest.mark.django_db
def test_register_user_success():
    payload = dict(
        username = "kostas2370",
        email = "kostas2372@gmail.com",
        password = "Test1234!"
    )

    response = client.post("/api/register/", payload)
    data = response.data
    assert data["username"] == payload["username"]
    assert data["is_verified"] == False
    assert "password" not in data
    assert response.status_code == 201


@pytest.mark.django_db
def test_register_user_fail():
    payload = dict(
        username = "kostas237123",
        email = "kostas2372@gmail.com",
        password = "test1234"
    )

    response = client.post("/api/register/", payload)
    assert response.status_code == 403
    assert response.data['detail'] == 'Your password must contain at least 8 chars ,uppercase ,lowercase ,digit'


@pytest.mark.django_db
def test_register_user_already_existing(user):
    payload = dict(username = "kostas2370", email = "kostas2372@gmail.com", password = "Test1234!")
    response = client.post("/api/register/", payload)
    assert response.status_code == 400
    assert response.data['username'][0] == "A user with that username already exists."


@pytest.mark.django_db
def test_login_user_success(user):
    response = client.post("/api/login/", dict(username= "kostas2370", password = "Pass1234!"))
    assert response.status_code == 200
    assert "access" in response.data['tokens']
    assert "refresh" in response.data['tokens']


@pytest.mark.django_db
def test_login_user_unverified(unverified_user):
    response = client.post("/api/login/", dict(username= "kostas2370", password = "Pass1234!"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_user_fail(user):
    response = client.post("/api/login/", dict(username= "kostas2370", password = "wrongPass1!"))
    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_user(user):
    refresh = RefreshToken.for_user(user)
    client.cookies["refresh_token"] = str(refresh)
    client.force_authenticate(user = user)

    response = client.post("/api/logout/")

    assert response.status_code == 200


@pytest.mark.django_db
def test_verify_email_valid_token(unverified_user):

    payload = {"user_id": unverified_user.id, "exp": datetime.utcnow() + timedelta(days=1)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    response = client.get(f"/api/email-verify/?token={token}")

    unverified_user.refresh_from_db()

    assert response.status_code == 200
    assert response.data == {"email": "Successfully Activated"}
    assert unverified_user.is_verified
