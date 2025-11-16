from django.test import TestCase
from apps.users.serializers import UserSerializer

from apps.users.tests.baker_recipes import user_recipe


class UserSerializerTests(TestCase):
    def test_user_serializer_excludes_password(self):
        user = user_recipe.make(
            email="user@example.com",
            password="Testpass123!",
            username="user1",
            first_name="Test",
            last_name="User",
        )
        serializer = UserSerializer(user)
        data = serializer.data

        self.assertEqual(data["email"], "user@example.com")
        self.assertNotIn("password", data)
