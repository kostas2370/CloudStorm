from unittest.mock import patch

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase


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
