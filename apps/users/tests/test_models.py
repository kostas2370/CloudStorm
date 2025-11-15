from django.test import TestCase
from model_bakery import baker
from django.contrib.auth import get_user_model

from apps.users.tests.baker_recipes import (
    user_recipe,
    verified_user_recipe,
    staff_user_recipe,
)


class UserModelTests(TestCase):
    def test_user_str(self):
        user = user_recipe.make()
        self.assertEqual(str(user), user.email)

    def test_get_full_name(self):
        user = user_recipe.make(first_name="Stavroula", last_name="Kesidi")
        self.assertEqual(user.get_full_name(), "Stavroula Kesidi")

    def test_get_short_name(self):
        user = user_recipe.make(first_name="Stavroula")
        self.assertEqual(user.get_short_name(), "Stavroula")

    def test_user_manager_create_user(self):
        user = user_recipe.make(
            email="example@example.com",
            password="testpass123",
            username="unique_username",
            first_name="Test",
            last_name="User",
        )
        user.set_password("testpass123")
        self.assertTrue(user.check_password("testpass123"))
        self.assertEqual(user.email, "example@example.com")
        self.assertFalse(user.is_superuser)

    def test_user_manager_create_superuser(self):
        user = staff_user_recipe.make(
            email="admin@example.com",
            password="admin123",
            username="admin_username",
            first_name="Admin",
            last_name="Super",
        )
        user.set_password("admin123")
        self.assertTrue(user.check_password("admin123"))
        self.assertTrue(user.is_superuser)

    def test_user_tokens(self):
        user = user_recipe.make()
        tokens = user.get_tokens()

        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)
        self.assertIsInstance(tokens["access"], str)
        self.assertIsInstance(tokens["refresh"], str)
