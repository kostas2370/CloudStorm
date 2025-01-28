from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import PermissionsMixin
from rest_framework_simplejwt.tokens import RefreshToken


class User(AbstractUser, PermissionsMixin):
    first_name = models.CharField(max_length = 20, blank = False)
    last_name = models.CharField(max_length = 20, blank = False)
    email = models.EmailField(unique = True)
    is_verified = models.BooleanField(default = False)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        return self.first_name

    def get_tokens(self):
        tokens = RefreshToken.for_user(self)

        return {"access": str(tokens.access_token),
                "refresh": str(tokens)}
