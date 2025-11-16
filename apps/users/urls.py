from django.urls import path

from .views import (
    LoginView,
    TokenRefreshView,
    UserRegisterView,
    VerifyEmail,
    logout_view,
)

app_name = "users"


urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("email-verify/", VerifyEmail.as_view(), name="email-verify"),
    path("logout/", logout_view, name="logout"),
]
