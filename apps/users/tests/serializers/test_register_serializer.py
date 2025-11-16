from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from apps.users.serializers import RegisterSerializer


class RegisterSerializerTests(TestCase):
    def test_register_serializer_rejects_weak_password(self):
        payload = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak",
        }
        serializer = RegisterSerializer(data=payload)

        with self.assertRaises(AuthenticationFailed) as exc:
            serializer.is_valid(raise_exception=True)

        self.assertIn("Your password must contain at least 8 chars", str(exc.exception))

    def test_register_serializer_creates_user_and_hashes_password(self):
        raw_password = "Valid123"
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": raw_password,
        }

        serializer = RegisterSerializer(data=payload)
        self.assertTrue(serializer.is_valid(raise_exception=True))

        user = serializer.save()

        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.username, "newuser")
        self.assertNotEqual(user.password, raw_password)
        self.assertTrue(user.check_password(raw_password))
