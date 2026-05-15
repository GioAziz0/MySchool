from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserRole


_ROLE_URL = {
    UserRole.ROLE_TEACHER: "dashboard-teacher",
    UserRole.ROLE_STUDENT: "dashboard-student",
    UserRole.ROLE_PARENT:  "dashboard-parent",
    UserRole.ROLE_ADMIN:   "dashboard-admin",
}

_ROLE_LABEL = {
    UserRole.ROLE_TEACHER: "Insegnante",
    UserRole.ROLE_STUDENT: "Studente",
    UserRole.ROLE_PARENT:  "Genitore",
    UserRole.ROLE_ADMIN:   "Amministratore",
}

_ROLE_ICON = {
    UserRole.ROLE_TEACHER: "👨‍🏫",
    UserRole.ROLE_STUDENT: "🎓",
    UserRole.ROLE_PARENT:  "👥",
    UserRole.ROLE_ADMIN:   "⚙️",
}


def _set_jwt_cookies(response, user):
    refresh = RefreshToken.for_user(user)
    common = dict(
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
    )
    response.set_cookie(
        settings.JWT_COOKIE_ACCESS,
        str(refresh.access_token),
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        **common,
    )
    response.set_cookie(
        settings.JWT_COOKIE_REFRESH,
        str(refresh),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        **common,
    )


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("select-school")
        return render(request, "users/login.html")

    def post(self, request):
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            return render(request, "users/login.html", {
                "error": "Inserisci username e password.",
                "username": username,
            })

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, "users/login.html", {
                "error": "Credenziali non valide.",
                "username": username,
            })

        login(request, user)
        response = redirect("select-school")
        _set_jwt_cookies(response, user)
        return response


class SelectSchoolView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        roles = (
            UserRole.objects
            .filter(user=request.user, is_active=True)
            .select_related("tenant")
            .order_by("tenant__name")
        )

        # Raggruppa per tenant
        seen = {}
        for role in roles:
            t = role.tenant
            if t.id not in seen:
                seen[t.id] = {"tenant": t, "roles": []}
            seen[t.id]["roles"].append({
                "code":  role.role,
                "label": _ROLE_LABEL[role.role],
                "icon":  _ROLE_ICON[role.role],
            })

        return render(request, "users/select_school.html", {
            "tenants": list(seen.values()),
            "user": request.user,
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        school_slug = request.POST.get("school_slug", "").strip()
        if not school_slug:
            return redirect("select-school")

        roles = list(
            UserRole.objects
            .filter(user=request.user, tenant__slug=school_slug, is_active=True)
            .values_list("role", flat=True)
        )

        if not roles:
            return redirect("select-school")

        if len(roles) == 1:
            url = reverse(_ROLE_URL[roles[0]], kwargs={"school_slug": school_slug})
            return HttpResponseRedirect(url)

        # Più ruoli → selezione ruolo
        request.session["pending_school"] = school_slug
        return redirect("select-role")


class SelectRoleView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        school_slug = request.session.get("pending_school")
        if not school_slug:
            return redirect("select-school")

        roles = (
            UserRole.objects
            .filter(user=request.user, tenant__slug=school_slug, is_active=True)
            .select_related("tenant")
        )
        if not roles.exists():
            return redirect("select-school")

        tenant = roles.first().tenant
        role_list = [
            {"code": r.role, "label": _ROLE_LABEL[r.role], "icon": _ROLE_ICON[r.role]}
            for r in roles
        ]

        return render(request, "users/select_role.html", {
            "tenant":    tenant,
            "roles":     role_list,
            "user":      request.user,
            "school_slug": school_slug,
        })

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        school_slug = request.session.get("pending_school", "")
        role = request.POST.get("role", "")

        valid = UserRole.objects.filter(
            user=request.user,
            tenant__slug=school_slug,
            role=role,
            is_active=True,
        ).exists()

        if not valid or role not in _ROLE_URL:
            return redirect("select-role")

        request.session.pop("pending_school", None)
        url = reverse(_ROLE_URL[role], kwargs={"school_slug": school_slug})
        return HttpResponseRedirect(url)


class LogoutView(View):
    def post(self, request):
        refresh_token = request.COOKIES.get(settings.JWT_COOKIE_REFRESH)
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        logout(request)
        response = redirect("login")
        response.delete_cookie(settings.JWT_COOKIE_ACCESS)
        response.delete_cookie(settings.JWT_COOKIE_REFRESH)
        return response
