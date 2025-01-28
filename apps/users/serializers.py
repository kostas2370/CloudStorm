from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only = True)
    password = serializers.CharField(write_only = True)
    tokens = serializers.DictField(read_only = True)

    class Meta:
        model = get_user_model()
        fields = ("username", "password", "tokens")

    def validate(self, attrs):
        request = self.context['request']
        username = attrs.get("username", '')
        password = attrs.get("password", '')

        if not username:
            raise AuthenticationFailed("Υou need to add username")

        auser = authenticate(username = username, password = password, request=request)

        if not auser:
            raise AuthenticationFailed("There is not a user with that credentials")
        #if not auser.is_verified:
        #    raise AuthenticationFailed("You have to verify your account to be able to have access to your account")
        return {
            "tokens": auser.get_tokens()
        }