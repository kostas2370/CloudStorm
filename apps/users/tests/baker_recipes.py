from model_bakery.recipe import Recipe, seq
from django.contrib.auth import get_user_model

User = get_user_model()


class FakeRequest:
    def __init__(self, data=None):
        self.data = data or {}


user_recipe = Recipe(
    User,
    email=seq("user_{0}@example.com"),
    username=seq("username_{0}"),
    first_name="Test",
    last_name="User",
    is_verified=False,
    is_staff=False,
)

verified_user_recipe = Recipe(
    User,
    email=seq("verified_{0}@example.com"),
    username=seq("verified_username_{0}"),
    first_name="Verified",
    last_name="User",
    is_verified=True,
    is_staff=False,
)

staff_user_recipe = Recipe(
    User,
    email=seq("staff_{0}@example.com"),
    username=seq("staff_username_{0}"),
    first_name="Staff",
    last_name="User",
    is_verified=True,
    is_staff=True,
    is_superuser=True,
)
