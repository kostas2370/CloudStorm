from apps.users.utils import check_conditions
from django.test import TestCase


class CheckConditionsTests(TestCase):
    def test_check_conditions_valid_password(self):
        password = "Valid123"
        self.assertTrue(check_conditions(password))

    def test_check_conditions_too_short(self):
        password = "Va1d"  # < 8 chars
        self.assertFalse(check_conditions(password))

    def test_check_conditions_missing_uppercase(self):
        password = "invalid123"
        self.assertFalse(check_conditions(password))

    def test_check_conditions_missing_lowercase(self):
        password = "INVALID123"
        self.assertFalse(check_conditions(password))

    def test_check_conditions_missing_digit(self):
        password = "InvalidPass"
        self.assertFalse(check_conditions(password))
