from django.urls import path

from .views import *

app_name = "users"


urlpatterns = [
    path('login/', LoginView.as_view(), name = "login"),
    path('token/refresh/', CookieTokenRefreshView.as_view()),
    path('register/', UserRegisterView.as_view(), name = "register"),
    path('email-verify/', VerifyEmail.as_view(), name = "email-verify"),
    path('logout/', logout_view, name = 'logout')

]
