from unittest.mock import patch

from django.test import TestCase

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.exceptions import ValidationError


from apps.users.serializers import (
    LoginSerializer,
)

from apps.users.tests.baker_recipes import (
    user_recipe,
    verified_user_recipe,
    FakeRequest,
)


class LoginSerializerTests(TestCase):
    def test_login_missing_email_raises_authentication_failed(self):
        payload = {"email": "", "password": "whatever"}

        serializer = LoginSerializer(
            data=payload,
            context={"request": FakeRequest()},
        )

        with self.assertRaises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

    @patch("apps.users.serializers.authenticate", return_value=None)
    def test_login_invalid_credentials(self, mock_auth):
        payload = {"email": "user@example.com", "password": "wrongpass"}

        serializer = LoginSerializer(
            data=payload,
            context={"request": FakeRequest()},
        )

        with self.assertRaises(AuthenticationFailed):
            serializer.is_valid(raise_exception=True)

        mock_auth.assert_called_once_with(
            email="user@example.com",
            password="wrongpass",
            request=serializer.context["request"],
        )

    @patch("apps.users.serializers.authenticate")
    def test_login_unverified_user(self, mock_auth):
        user = user_recipe.make()
        mock_auth.return_value = user

        payload = {"email": user.email, "password": "pass"}
        serializer = LoginSerializer(
            data=payload,
            context={"request": FakeRequest()},
        )

        with self.assertRaises(AuthenticationFailed) as exc:
            serializer.is_valid(raise_exception=True)

        self.assertIn("verify your account", str(exc.exception))

    @patch("apps.users.serializers.authenticate")
    def test_login_success(self, mock_auth):
        user = verified_user_recipe.make()
        mock_auth.return_value = user

        payload = {"email": user.email, "password": "pass"}
        serializer = LoginSerializer(
            data=payload,
            context={"request": FakeRequest()},
        )

        self.assertTrue(serializer.is_valid(raise_exception=True))
        data = serializer.validated_data

        self.assertIn("tokens", data)
        self.assertIn("access", data["tokens"])
        self.assertIn("refresh", data["tokens"])
