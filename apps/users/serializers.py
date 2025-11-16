from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt import (
    serializers as jwt_serializers,
    exceptions as jwt_exceptions,
)

from apps.users.utils import check_conditions


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    tokens = serializers.DictField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("email", "password", "tokens")

    def validate(self, attrs):
        request = self.context["request"]
        email = attrs.get("email", "")
        password = attrs.get("password", "")

        if not email:
            raise AuthenticationFailed("Email Required")

        auser = authenticate(email=email, password=password, request=request)

        if not auser:
            raise AuthenticationFailed("There is not a user with that credentials")
        if not auser.is_verified:
            raise AuthenticationFailed(
                "You have to verify your account to be able to have access to your account"
            )
        return {"tokens": auser.get_tokens()}


class VerifySerializer(serializers.Serializer):
    email = serializers.CharField(required=False, read_only=True, max_length=100)

    class Meta:
        fields = ("email",)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        exclude = ("password",)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("username", "password", "email")
        extra_kwargs = {
            "password": {"write_only": True},
            "is_verified": {"read_only": True},
        }
        optional_fields = ["first_name", "last_name"]

    def validate(self, attrs):
        password = attrs.get("password")

        if not check_conditions(password):
            raise AuthenticationFailed(
                "Your password must contain at least 8 chars ,uppercase ,lowercase ,digit"
            )

        return super().validate(attrs)

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data.get("password"))
        user.save()
        return user


class TokenRefreshSerializer(jwt_serializers.TokenRefreshSerializer):
    refresh = None

    def validate(self, attrs):
        attrs["refresh"] = self.context["request"].data.get("refresh_token")
        if attrs["refresh"]:
            return super().validate(attrs)
        else:
            raise jwt_exceptions.InvalidToken(
                "No valid token found in cookie 'refresh'"
            )
