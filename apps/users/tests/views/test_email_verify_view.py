from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.tests.baker_recipes import user_recipe, verified_user_recipe


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
