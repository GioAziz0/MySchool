"""
URL routing per le API del registro scolastico.

Tutte le route sono sottoposte all'URL prefix:
    /api/schools/<school_slug>/

Il router gestisce automaticamente:
  list   → GET  /resource/
  create → POST /resource/
  detail → GET  /resource/<pk>/
  update → PUT/PATCH /resource/<pk>/
  delete → DELETE /resource/<pk>/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SchoolClassViewSet,
    StudentEnrollmentViewSet,
    TeacherAssignmentViewSet,
    TeacherClassSubjectViewSet,
    LessonViewSet,
    GradeViewSet,
    HomeworkViewSet,
    StudentNoteViewSet,
    AbsenceViewSet,
    TardinessViewSet,
)

router = DefaultRouter()

router.register(r"classes",           SchoolClassViewSet,          basename="schoolclass")
router.register(r"enrollments",       StudentEnrollmentViewSet,    basename="enrollment")
router.register(r"assignments",       TeacherAssignmentViewSet,    basename="assignment")
router.register(r"class-subjects",    TeacherClassSubjectViewSet,  basename="classsubject")
router.register(r"lessons",           LessonViewSet,               basename="lesson")
router.register(r"grades",            GradeViewSet,                basename="grade")
router.register(r"homework",          HomeworkViewSet,             basename="homework")
router.register(r"notes",             StudentNoteViewSet,          basename="note")
router.register(r"absences",          AbsenceViewSet,              basename="absence")
router.register(r"tardinesses",       TardinessViewSet,            basename="tardiness")

urlpatterns = [
    path("", include(router.urls)),
]
