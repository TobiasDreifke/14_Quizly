from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import RegistrationSerializer



class RegistrationView(APIView):
    """
    Handles new user registration.

    POST /api/register/  - Creates a new user account.

    Permissions: Open to all (no authentication required).

    Expected request body:
        {
            "username": "john",
            "email": "john@example.com",
            "password": "secret123",
            "repeated_password": "secret123"
        }

    Returns the created user's username, email, and user_id on success.
    Returns validation errors (e.g. email already exists, passwords don't match) on failure.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validates input via RegistrationSerializer and creates a new User.
        Passwords are hashed before saving — never stored in plain text.
        """
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            data = {
                'username': saved_account.username,
                'email': saved_account.email,
                'user_id': saved_account.pk,
            }
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Extends the default JWT login view to set tokens as HTTP-only cookies
    instead of returning them in the response body.

    POST /api/login/  - Authenticates a user and sets JWT cookies.

    Permissions: Open to all (no authentication required).

    Expected request body:
        { "username": "john", "password": "secret123" }

    On success, sets two HTTP-only cookies:
        access_token  - Short-lived token used for authenticating requests.
        refresh_token - Long-lived token used to obtain new access tokens.

    The response body only contains { "message": "Login successful" }.
    Tokens are never exposed in the response body to prevent XSS token theft.

    Cookie settings:
        httponly=True  - Inaccessible to JavaScript.
        secure=True    - Sent only over HTTPS.
        samesite="Lax" - Protects against CSRF while allowing top-level navigation.
    """

    def post(self, request, *args, **kwargs):
        """
        Calls the parent view to validate credentials and generate tokens,
        then moves both tokens from the response body into HTTP-only cookies.
        """
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        access = response.data.get("access")

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        response.data = {"message": "Login successful"}
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """
    Extends the default JWT token refresh view to read the refresh token
    from an HTTP-only cookie instead of the request body.

    POST /api/token/refresh/  - Issues a new access token using the refresh token cookie.

    Permissions: Open to all (the refresh token itself is the credential).

    On success, sets a new access_token cookie and returns:
        { "message": "Token refreshed successfully" }

    Returns 400 if no refresh token cookie is present.
    Returns 401 if the refresh token is invalid or expired.
    """

    def post(self, request, *args, **kwargs):
        """
        Reads the refresh token from cookies, validates it, and sets
        a new access_token cookie on the response.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"error": "Refresh token not provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"error": "Refresh token invalid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")
        response = Response({"message": "Token refreshed successfully"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response


class LogoutView(APIView):
    """
    Handles user logout by blacklisting the refresh token and clearing both cookies.

    POST /api/logout/  - Logs out the authenticated user.

    Permissions: Authentication required.

    On logout:
        1. Reads the refresh token from cookies.
        2. Blacklists the refresh token so it cannot be reused (requires
           'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS).
        3. Deletes both access_token and refresh_token cookies from the browser.

    If the refresh token is missing or already invalid, the logout proceeds
    silently — cookies are still cleared to ensure the user is logged out
    on the client side regardless.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Blacklists the refresh token if present, then clears both JWT cookies.
        Errors during blacklisting are intentionally suppressed — a missing or
        already-blacklisted token should not prevent a successful logout.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response({"message": "Logout successful"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response