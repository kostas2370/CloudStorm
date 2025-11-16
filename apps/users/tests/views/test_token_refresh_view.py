from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.baker_recipes import verified_user_recipe


class TokenRefreshAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("users:token_refresh")
        self.user = verified_user_recipe.make()

    def test_refresh_with_valid_token_returns_new_access_token(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.url, data={"refresh_token": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_without_token_returns_400(self):
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_invalid_token_returns_400(self):
        response = self.client.post(
            self.url, data={"refresh_token": "not-a-real-refresh-token"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Message", response.data)
