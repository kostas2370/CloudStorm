from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.baker_recipes import user_recipe, verified_user_recipe


class UserRegisterAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:register")

    @patch("apps.users.views.send_email.delay")
    def test_register_user_creates_user_and_sends_email(self, mock_delay):
        payload = {
            "email": "newuser@example.com",
            "username": "new_user",
            "password": "Testpass123!",
            "first_name": "New",
            "last_name": "User",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            get_user_model().objects.filter(email="newuser@example.com").exists()
        )
        mock_delay.assert_called_once()
        self.assertEqual(response.data["email"], "newuser@example.com")

    def test_register_user_invalid_email_returns_400(self):
        payload = {
            "email": "not-an-email",
            "username": "invalid_email_user",
            "password": "Testpass123!",
            "first_name": "New",
            "last_name": "User",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)


class VerifyEmailAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:email-verify")
        self.user = user_recipe.make()

    def test_verify_email_with_valid_token_marks_user_verified(self):
        access_token = RefreshToken.for_user(self.user).access_token
        response = self.client.get(self.url, {"token": str(access_token)})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "Successfully Activated")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_verify_email_with_invalid_token_returns_400(self):
        response = self.client.get(self.url, {"token": "totally-invalid-token"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_verify_email_when_already_verified_returns_400(self):
        verified_user = verified_user_recipe.make()
        access_token = RefreshToken.for_user(verified_user).access_token
        response = self.client.get(self.url, {"token": str(access_token)})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "User is already verified")


class LoginAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:login")
        self.password = "Testpass123!"
        self.user = verified_user_recipe.make()
        self.user.set_password(self.password)
        self.user.save()

    def test_login_with_valid_credentials_returns_tokens(self):
        payload = {
            "email": self.user.email,
            "password": self.password,
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_login_with_invalid_credentials_returns_401(self):
        payload = {
            "email": self.user.email,
            "password": "wrong-pass",
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)


class TokenRefreshAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:token_refresh")
        self.user = verified_user_recipe.make()

    def test_refresh_with_valid_token_returns_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.url, data={"refresh_token": str(refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_without_token_returns_400(self):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token_returns_400(self):
        response = self.client.post(self.url, data={"refresh_token": "not-a-real-refresh-token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Message", response.data)


class LogoutAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:logout")
        self.user = verified_user_recipe.make()

    def test_logout_with_valid_refresh_token_blacklists_and_clears_cookies(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.cookies["refresh_token"] = str(refresh)

        response = self.client.post(self.url)

        self.assertIn(
            response.status_code, (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
        )
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

    def test_logout_with_invalid_refresh_token_returns_400(self):
        self.client.cookies["refresh_token"] = "invalid-token"

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
