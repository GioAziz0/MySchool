"""
View di autenticazione — Fase 2.

Endpoint disponibili:
    POST /api/auth/login/         → login, JWT nei cookie (browser)
    POST /api/auth/login/token/   → login, JWT nel body (mobile / Postman)
    POST /api/auth/refresh/       → rinnova access token (cookie o body)
    POST /api/auth/logout/        → invalida refresh token e cancella cookie
"""

from django.conf import settings
from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


# ==============================================================================
# Helper
# ==============================================================================

def _set_auth_cookies(response: Response, access: str, refresh: str | None = None):
    """Imposta i cookie JWT sulla response."""
    response.set_cookie(
        settings.JWT_COOKIE_ACCESS,
        access,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )
    if refresh is not None:
        response.set_cookie(
            settings.JWT_COOKIE_REFRESH,
            refresh,
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            httponly=True,
            secure=settings.JWT_COOKIE_SECURE,
            samesite=settings.JWT_COOKIE_SAMESITE,
        )


def _delete_auth_cookies(response: Response):
    """Rimuove i cookie JWT dalla response."""
    response.delete_cookie(settings.JWT_COOKIE_ACCESS)
    response.delete_cookie(settings.JWT_COOKIE_REFRESH)


def _authenticate_or_error(request) -> tuple:
    """
    Valida username e password dalla request.
    Restituisce (user, None) in caso di successo, (None, Response) in caso di errore.
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return None, Response(
            {"detail": "Username e password sono obbligatori."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return None, Response(
            {"detail": "Credenziali non valide."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return user, None


def _user_data(user) -> dict:
    """Dati utente da includere nella response di login."""
    roles = [
        {
            "school_slug": r.tenant.slug,
            "school_name": r.tenant.name,
            "role": r.role,
        }
        for r in user.roles.filter(is_active=True).select_related("tenant")
    ]
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "roles": roles,
    }


# ==============================================================================
# Login — cookie (browser)
# ==============================================================================

class LoginView(APIView):
    """
    Autentica l'utente e imposta access + refresh token nei cookie HttpOnly.
    Destinato ai client browser: il token viene gestito automaticamente.

    POST /api/auth/login/
    Body: { "username": "...", "password": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        user, error = _authenticate_or_error(request)
        if error:
            return error

        refresh = RefreshToken.for_user(user)
        response = Response({"user": _user_data(user)}, status=status.HTTP_200_OK)
        _set_auth_cookies(response, str(refresh.access_token), str(refresh))
        return response


# ==============================================================================
# Login — token nel body (mobile / Postman)
# ==============================================================================

class LoginTokenView(APIView):
    """
    Autentica l'utente e restituisce access + refresh token nel body JSON.
    Destinato a client non-browser (app mobile, API testing, server-to-server).

    POST /api/auth/login/token/
    Body: { "username": "...", "password": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        user, error = _authenticate_or_error(request)
        if error:
            return error

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": _user_data(user),
            },
            status=status.HTTP_200_OK,
        )


# ==============================================================================
# Refresh
# ==============================================================================

class RefreshView(APIView):
    """
    Rinnova l'access token a partire dal refresh token.
    Legge il refresh token prima dal cookie, poi dal body JSON.
    Se ROTATE_REFRESH_TOKENS=True, emette anche un nuovo refresh token.

    POST /api/auth/refresh/
    Body (opzionale se c'è il cookie): { "refresh": "..." }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        # Legge il refresh token: prima dal cookie, poi dal body
        refresh_token = (
            request.COOKIES.get(settings.JWT_COOKIE_REFRESH)
            or request.data.get("refresh")
        )

        if not refresh_token:
            return Response(
                {"detail": "Refresh token mancante."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Delega la validazione e la rotazione a simplejwt
        serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = serializer.validated_data  # contiene "access" e opzionalmente "refresh"

        # Se il client usa i cookie, aggiorna i cookie
        if settings.JWT_COOKIE_REFRESH in request.COOKIES:
            response = Response({"detail": "Token aggiornato."}, status=status.HTTP_200_OK)
            _set_auth_cookies(
                response,
                access=data["access"],
                refresh=data.get("refresh"),  # presente solo se ROTATE_REFRESH_TOKENS=True
            )
            return response

        # Altrimenti restituisce i token nel body (client mobile)
        return Response(data, status=status.HTTP_200_OK)


# ==============================================================================
# Logout
# ==============================================================================

class LogoutView(APIView):
    """
    Invalida il refresh token (blacklist) e cancella i cookie JWT.
    Legge il refresh token prima dal cookie, poi dal body.

    POST /api/auth/logout/
    Body (opzionale se c'è il cookie): { "refresh": "..." }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = (
            request.COOKIES.get(settings.JWT_COOKIE_REFRESH)
            or request.data.get("refresh")
        )

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass  # già scaduto o invalido — va bene comunque

        response = Response({"detail": "Logout effettuato."}, status=status.HTTP_200_OK)
        _delete_auth_cookies(response)
        return response
