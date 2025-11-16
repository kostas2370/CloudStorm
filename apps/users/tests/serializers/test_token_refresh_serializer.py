from django.test import TestCase

from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.serializers import TokenRefreshSerializer

from apps.users.tests.baker_recipes import user_recipe, FakeRequest


class TokenRefreshSerializerTests(TestCase):
    def setUp(self):
        self.user = user_recipe.make(
            email="refresh@example.com",
            password="Testpass123!",
            username="refresh_user",
            first_name="Refresh",
            last_name="User",
        )

    def test_token_refresh_with_valid_refresh_token_returns_access(self):
        refresh = RefreshToken.for_user(self.user)

        request = FakeRequest(data={"refresh_token": str(refresh)})

        serializer = TokenRefreshSerializer(context={"request": request})

        data = serializer.validate(attrs={})

        self.assertIn("access", data)
        self.assertIsInstance(data["access"], str)

    def test_token_refresh_without_refresh_token_raises_invalid_token(self):
        request = FakeRequest(data={})  # no refresh_token

        serializer = TokenRefreshSerializer(context={"request": request})

        with self.assertRaises(InvalidToken) as exc:
            serializer.validate(attrs={})

        self.assertIn("No valid token found in cookie 'refresh'", str(exc.exception))
