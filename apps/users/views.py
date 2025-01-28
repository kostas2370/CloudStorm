from django.shortcuts import render
import jwt
from rest_framework_simplejwt import views as jwt_views
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth import get_user_model
from .serializers import LoginSerializer
from django.middleware import csrf


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data = request.data, context = {'request': request})
        serializer.is_valid(raise_exception = True)

        user = get_user_model().objects.get(username = request.data.get("username"))

        serializer.is_valid(raise_exception = True)

        response = Response(serializer.data, status = status.HTTP_200_OK)
        response.set_cookie("access_token", serializer.data["tokens"]["access"],
                            expires = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                            httponly = settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'])

        response.set_cookie("refresh_token",
                            serializer.data["tokens"]["refresh"],
                            expires = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
                            httponly = settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                            secure = settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"])

        response["X-CSRFToken"] = csrf.get_token(request)

        return response
