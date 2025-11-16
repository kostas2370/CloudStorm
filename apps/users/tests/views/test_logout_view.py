from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.baker_recipes import verified_user_recipe


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
