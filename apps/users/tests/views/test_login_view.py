from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.baker_recipes import user_recipe, verified_user_recipe


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
