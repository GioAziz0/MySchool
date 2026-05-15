from datetime import date

from django.shortcuts import render, redirect
from django.views import View

from users.models import UserRole


class _LoginRequired(View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request, *args, **kwargs)


class TeacherDashboardView(_LoginRequired):
    def get(self, request, school_slug):
        try:
            teacher_role = UserRole.objects.select_related("tenant").get(
                user=request.user,
                tenant__slug=school_slug,
                role=UserRole.ROLE_TEACHER,
                is_active=True,
            )
        except UserRole.DoesNotExist:
            return redirect("select-school")

        return render(request, "core/dashboard_teacher.html", {
            "tenant":      teacher_role.tenant,
            "user":        request.user,
            "school_slug": school_slug,
            "today":       date.today().isoformat(),
        })


class StudentDashboardView(_LoginRequired):
    def get(self, request, school_slug):
        try:
            role = UserRole.objects.select_related("tenant").get(
                user=request.user, tenant__slug=school_slug,
                role=UserRole.ROLE_STUDENT, is_active=True,
            )
        except UserRole.DoesNotExist:
            return redirect("select-school")

        return render(request, "core/dashboard_student.html", {
            "tenant":      role.tenant,
            "user":        request.user,
            "school_slug": school_slug,
            "role_label":  "Studente",
        })


class ParentDashboardView(_LoginRequired):
    def get(self, request, school_slug):
        try:
            role = UserRole.objects.select_related("tenant").get(
                user=request.user, tenant__slug=school_slug,
                role=UserRole.ROLE_PARENT, is_active=True,
            )
        except UserRole.DoesNotExist:
            return redirect("select-school")

        return render(request, "core/dashboard_parent.html", {
            "tenant":      role.tenant,
            "user":        request.user,
            "school_slug": school_slug,
            "role_label":  "Genitore",
        })


class AdminDashboardView(_LoginRequired):
    def get(self, request, school_slug):
        try:
            role = UserRole.objects.select_related("tenant").get(
                user=request.user, tenant__slug=school_slug,
                role=UserRole.ROLE_ADMIN, is_active=True,
            )
        except UserRole.DoesNotExist:
            return redirect("select-school")

        return render(request, "core/dashboard_admin.html", {
            "tenant":      role.tenant,
            "user":        request.user,
            "school_slug": school_slug,
            "role_label":  "Amministratore",
        })
