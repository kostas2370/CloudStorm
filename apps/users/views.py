import jwt
from rest_framework_simplejwt import views as jwt_views
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .tasks import send_email
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt import tokens
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ParseError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


import logging

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    VerifySerializer,
    CookieTokenRefreshSerializer,
)

logger = logging.getLogger(__name__)


class UserRegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    authentication_classes = []

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(
                description="Validation failed (username, email, or password)"
            ),
        },
        description="Registers a new user and sends a verification email with a token link.",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if "username" in serializer.errors:
                return Response(
                    dict(message=serializer.errors["username"][0]), status=400
                )
            if "email" in serializer.errors:
                return Response(
                    dict(message=f"Email : {serializer.errors['email'][0]}"), status=400
                )
            if "password" in serializer.errors:
                return Response(
                    dict(message=f"Password : {serializer.errors['password'][0]}"),
                    status=400,
                )

        user = serializer.save()
        token = tokens.RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        absurl = f"{current_site}{reverse('users:email-verify')}?token={str(token)}"
        send_email.delay(
            subject="Register verification for video creator !",
            recipient_list=[user.email],
            message=f"Thank you, here is the verification link : {absurl}",
        )

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class VerifyEmail(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = VerifySerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="token",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Verification token sent to user's email",
            )
        ],
        responses={
            200: OpenApiResponse(description="Email successfully verified"),
            400: OpenApiResponse(description="Invalid, expired, or already-used token"),
        },
        description="Verifies a user's email using the token sent after registration.",
    )
    def get(self, request):
        token = request.GET.get("token")
        try:
            load = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")

        except jwt.ExpiredSignatureError:
            return Response({"error": "Token Expired"}, status=400)

        except jwt.DecodeError:
            return Response({"error": "Invalid Token"}, status=400)

        user = get_user_model().objects.get(id=load["user_id"])
        if user.is_verified:
            return Response(
                {"error": "User is already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.save()
        return Response({"email": "Successfully Activated"}, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (AllowAny,)

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
            400: OpenApiResponse(
                description="Invalid credentials or unverified account"
            ),
        },
        description="Authenticates a user and returns access/refresh tokens if credentials are valid and the account is verified.",
    )
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(
                {"detail": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(serializer.data, status=status.HTTP_200_OK)
        return response


class CookieTokenRefreshView(jwt_views.TokenRefreshView):
    serializer_class = CookieTokenRefreshSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        refresh = request.COOKIES.get("refresh_token")

        if not refresh:
            response.data = {"Message": "You need to set refresh token"}
            response.status_code = 400
            return super().finalize_response(request, response, *args, **kwargs)

        try:
            tokens.RefreshToken(refresh)
        except TokenError:
            response.data = {"Message": "This token has expired"}
            response.status_code = 400
            return super().finalize_response(request, response, *args, **kwargs)

        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    methods=["POST"],
    request=None,
    responses={
        204: OpenApiResponse(description="Successfully logged out and tokens revoked"),
        400: OpenApiResponse(description="Invalid or missing refresh token"),
    },
    description="Logs the user out by blacklisting the refresh token and deleting authentication cookies.",
)
@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        refresh_token = request.COOKIES.get("refresh_token")
        token = tokens.RefreshToken(refresh_token)
        token.blacklist()
        res = Response()
        res.delete_cookie(
            "access_token",
            samesite="Strict",
        )
        res.delete_cookie(
            "refresh_token",
            samesite="Strict",
        )
        res.delete_cookie("X-CSRFToken", samesite="None")
        res.delete_cookie("csrftoken", samesite="None")
        return res

    except Exception as exc:
        logger.error(exc)
        raise ParseError("Invalid token")
