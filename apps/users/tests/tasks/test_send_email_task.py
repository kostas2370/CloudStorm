from unittest.mock import patch
from django.test import TestCase
from django.conf import settings

from apps.users.tasks import send_email


class SendEmailTaskTests(TestCase):

    @patch("apps.users.tasks.send_mail")
    def test_send_email_task_calls_send_mail_with_correct_args(self, mock_send_mail):
        subject = "Test Subject"
        recipient_list = ["user@example.com"]
        message = "This is a test message."

        send_email(subject, recipient_list, message)

        mock_send_mail.assert_called_once_with(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
        )