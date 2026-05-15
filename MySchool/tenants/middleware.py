"""
Middleware che risolve il tenant corrente e lo attacca a request.tenant.

Presuppone che lo slug della scuola sia nel path URL nella forma:
    /api/schools/<school_slug>/...

Se la URL non contiene uno slug valido, request.tenant è impostato a None
e le permission class rifiuteranno la richiesta.

Attivazione in settings.py:
    MIDDLEWARE = [
        ...
        "tenants.middleware.TenantMiddleware",
    ]
"""

from .models import Tenant


class TenantMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = self._resolve(request)
        return self.get_response(request)

    def _resolve(self, request):
        # Estrae lo slug dalla URL: /api/schools/<slug>/...
        # Adattare questo metodo se la struttura URL cambia
        # (es: subdomain, header X-School-Slug, ecc.).
        parts = request.path.strip("/").split("/")
        try:
            idx = parts.index("schools")
            slug = parts[idx + 1]
        except (ValueError, IndexError):
            return None

        return Tenant.objects.filter(slug=slug).first()
