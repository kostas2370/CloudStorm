from rest_framework_simplejwt import authentication as jwt_authentication


def enforce_csrf(request):
    return


class CustomAuthentication(jwt_authentication.JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = request.COOKIES.get("access_token") or None

        if header is None and raw_token is None:
            return None

        if raw_token is None:
            raw_token = self.get_raw_token(header)

        validated_token = self.get_validated_token(raw_token)

        enforce_csrf(request)
        return self.get_user(validated_token), validated_token
