"""
Autenticazione JWT con supporto sia per cookie che per header Authorization.

Ordine di lettura del token:
    1. Cookie "access_token"  (browser web, login via cookie)
    2. Header "Authorization: Bearer <token>"  (client mobile, Postman, ecc.)

Questo permette di supportare entrambi i flussi con un'unica classe,
senza duplicare la logica di validazione del token (delegata a simplejwt).
"""

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class CookieJWTAuthentication(JWTAuthentication):

    def authenticate(self, request):
        # Prova prima il cookie
        raw_token = request.COOKIES.get(settings.JWT_COOKIE_ACCESS)

        # Se non c'è il cookie, prova l'header Authorization standard
        if raw_token is None:
            return super().authenticate(request)

        # Valida il token letto dal cookie (stessa logica di simplejwt)
        try:
            validated_token = self.get_validated_token(raw_token)
        except (InvalidToken, TokenError):
            return None  # token non valido → request non autenticata

        return self.get_user(validated_token), validated_token
