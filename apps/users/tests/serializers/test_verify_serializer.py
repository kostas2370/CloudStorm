from django.test import TestCase
from apps.users.serializers import VerifySerializer


class VerifySerializerTests(TestCase):
    def test_verify_serializer_defines_email_field(self):
        serializer = VerifySerializer()
        self.assertIn("email", serializer.fields)
        self.assertTrue(serializer.fields["email"].read_only)
