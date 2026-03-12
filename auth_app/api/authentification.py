from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework import exceptions


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the access token from an HTTP-only cookie
    instead of the Authorization header.

    This approach improves security by preventing JavaScript from accessing the token,
    which mitigates XSS-based token theft. The frontend never handles the token directly —
    it is set and cleared exclusively by the backend via Set-Cookie headers.

    Configured in settings.py as the default authentication class:
        REST_FRAMEWORK = {
            "DEFAULT_AUTHENTICATION_CLASSES": [
                "auth_app.authentication.CookieJWTAuthentication",
            ]
        }

    Cookie name: 'access_token' (must match the name set during login).
    """

    def authenticate(self, request):
        """
        Attempts to authenticate the request using the 'access_token' cookie.

        Returns:
            Tuple of (user, validated_token) if authentication succeeds.
            None if no access token cookie is present (request is treated as anonymous).

        Raises:
            AuthenticationFailed if the token is present but invalid or expired.
            Returning None (instead of raising) when the cookie is absent allows
            DRF to fall through to other authentication backends if configured.
        """
        access_token = request.COOKIES.get("access_token")

        if access_token is None:
            return None

        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            raise exceptions.AuthenticationFailed(
                "Invalid or expired access token")
