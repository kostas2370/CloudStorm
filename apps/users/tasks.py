from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail

channel_layer = get_channel_layer()


@shared_task
def send_email(subject, recipient_list, message):
    send_mail(subject = subject, message = message, from_email = settings.EMAIL_HOST_USER, recipient_list = recipient_list)
