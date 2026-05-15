from django.urls import path
from .web_views import (
    TeacherDashboardView,
    StudentDashboardView,
    ParentDashboardView,
    AdminDashboardView,
)

urlpatterns = [
    path("dashboard/<slug:school_slug>/teacher/", TeacherDashboardView.as_view(), name="dashboard-teacher"),
    path("dashboard/<slug:school_slug>/student/", StudentDashboardView.as_view(), name="dashboard-student"),
    path("dashboard/<slug:school_slug>/parent/",  ParentDashboardView.as_view(),  name="dashboard-parent"),
    path("dashboard/<slug:school_slug>/admin/",   AdminDashboardView.as_view(),   name="dashboard-admin"),
]
