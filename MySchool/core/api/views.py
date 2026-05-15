"""
ViewSet per le entità del registro scolastico.

Ogni ViewSet:
  1. Filtra il queryset sul tenant di request per sicurezza
  2. Controlla il permesso sull'operazione (HasRolePermission)
  3. Controlla lo scope sull'oggetto in get_object() (HasObjectScope)

Pattern permessi:
  permission_classes = [IsAuthenticated, IsActiveTenantMember, HasRolePermission("...")]

  Per le action in lettura (GET) viene usato il codename .read,
  per le azioni di scrittura il codename specifico (create/update/delete).
  Le azioni che richiedono permessi diversi per metodo HTTP usano
  get_permissions() per restituire il set corretto.
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import (
    SchoolClass,
    StudentEnrollment,
    TeacherAssignment,
    TeacherClassSubject,
    Grade,
    StudentNote,
    Homework,
    Absence,
    Tardiness,
    Lesson,
)

from users.api.permissions import (
    IsActiveTenantMember,
    HasRolePermission,
    HasObjectScope,
    CanJustify,
)

from .serializers import (
    SchoolClassSerializer,
    StudentEnrollmentSerializer,
    TeacherAssignmentSerializer,
    TeacherClassSubjectSerializer,
    LessonSerializer,
    GradeSerializer,
    StudentNoteSerializer,
    HomeworkSerializer,
    AbsenceSerializer,
    AbsenceJustifySerializer,
    TardinessSerializer,
    TardinessJustifySerializer,
    TardinessUpdateEntryTimeSerializer,
)

# Base permissions richieste da tutti i ViewSet
_BASE = [IsAuthenticated, IsActiveTenantMember]


# ==============================================================================
# Helper
# ==============================================================================

def _tenant(request):
    return request.tenant


# ==============================================================================
# SchoolClass
# ==============================================================================

class SchoolClassViewSet(viewsets.ModelViewSet):
    """
    CRUD sulle classi scolastiche.

    - Lettura  → teacher, student, parent (con scope)
    - Scrittura→ solo admin con permesso esplicito
    """

    serializer_class = SchoolClassSerializer

    def get_queryset(self):
        return SchoolClass.objects.filter(tenant=_tenant(self.request))

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "class.read"
        elif self.action == "create":
            codename = "class.create"
        elif self.action in ("update", "partial_update"):
            codename = "class.update"
        elif self.action == "destroy":
            codename = "class.delete"
        else:
            codename = "class.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def perform_create(self, serializer):
        serializer.save(tenant=_tenant(self.request))


# ==============================================================================
# StudentEnrollment
# ==============================================================================

class StudentEnrollmentViewSet(viewsets.ModelViewSet):
    """
    CRUD sulle iscrizioni studente.
    Gestione riservata agli admin; lettura per teacher/student/parent con scope.
    """

    serializer_class = StudentEnrollmentSerializer

    def get_queryset(self):
        return StudentEnrollment.objects.filter(
            school_class__tenant=_tenant(self.request)
        ).select_related("student", "school_class", "student__role__user")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "class.read"
        else:
            codename = "enrollment.manage"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# TeacherAssignment
# ==============================================================================

class TeacherAssignmentViewSet(viewsets.ModelViewSet):
    """
    CRUD sugli incarichi docente.
    Gestione riservata agli admin.
    """

    serializer_class = TeacherAssignmentSerializer

    def get_queryset(self):
        return TeacherAssignment.objects.filter(
            teacher__role__tenant=_tenant(self.request)
        ).select_related("teacher")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "class.read"
        else:
            codename = "assignment.manage"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# TeacherClassSubject
# ==============================================================================

class TeacherClassSubjectViewSet(viewsets.ModelViewSet):
    """
    Assegnazione insegnante-classe-materia.
    Gestione riservata agli admin.
    """

    serializer_class = TeacherClassSubjectSerializer

    def get_queryset(self):
        return TeacherClassSubject.objects.filter(
            assignment__teacher__role__tenant=_tenant(self.request)
        ).select_related("assignment", "school_class", "subject")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "class.read"
        else:
            codename = "assignment.manage"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# Grade
# ==============================================================================

class GradeViewSet(viewsets.ModelViewSet):
    """
    CRUD sui voti.

    - Lettura  → teacher, student, parent (scope su proprie classi/iscrizioni)
    - Scrittura→ teacher (scope classe + materia tramite TeacherClassSubject)
    """

    serializer_class = GradeSerializer

    def get_queryset(self):
        return Grade.objects.filter(
            student_enrollment__school_class__tenant=_tenant(self.request)
        ).select_related(
            "student_enrollment__student__role__user",
            "teacher_class_subject__subject",
            "teacher_class_subject__school_class",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "grade.read"
        elif self.action == "create":
            codename = "grade.create"
        elif self.action in ("update", "partial_update"):
            codename = "grade.update"
        elif self.action == "destroy":
            codename = "grade.delete"
        else:
            codename = "grade.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# Homework
# ==============================================================================

class HomeworkViewSet(viewsets.ModelViewSet):
    """
    CRUD sui compiti.

    - Lettura  → teacher, student, parent (scope su proprie classi)
    - Scrittura→ teacher (scope classe + materia)
    """

    serializer_class = HomeworkSerializer

    def get_queryset(self):
        return Homework.objects.filter(
            teacher_class_subject__school_class__tenant=_tenant(self.request)
        ).select_related(
            "teacher_class_subject__school_class",
            "teacher_class_subject__subject",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "homework.read"
        elif self.action == "create":
            codename = "homework.create"
        elif self.action in ("update", "partial_update"):
            codename = "homework.update"
        elif self.action == "destroy":
            codename = "homework.delete"
        else:
            codename = "homework.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# StudentNote
# ==============================================================================

class StudentNoteViewSet(viewsets.ModelViewSet):
    """
    CRUD sulle note disciplinari/informative.

    Solo gli insegnanti possono creare/leggere/modificare/eliminare note.
    Studenti e genitori non hanno accesso.
    """

    serializer_class = StudentNoteSerializer

    def get_queryset(self):
        return StudentNote.objects.filter(
            student_enrollment__school_class__tenant=_tenant(self.request)
        ).select_related(
            "student_enrollment__student__role__user",
            "teacher_assignment__teacher__role__user",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "note.read"
        elif self.action == "create":
            codename = "note.create"
        elif self.action in ("update", "partial_update"):
            codename = "note.update"
        elif self.action == "destroy":
            codename = "note.delete"
        else:
            codename = "note.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj


# ==============================================================================
# Absence
# ==============================================================================

class AbsenceViewSet(viewsets.ModelViewSet):
    """
    Gestione assenze.

    Permessi per HTTP method:
      POST   → teacher (codename absence.create)
      GET    → teacher, student, parent (absence.read)
      PUT/PATCH→ 405 Method Not Allowed (si usa l'action justify)
      DELETE → 405 Method Not Allowed (le assenze non si eliminano)

    Action speciale:
      POST /absences/<pk>/justify/ → CanJustify + HasObjectScope
    """

    serializer_class = AbsenceSerializer
    http_method_names = ["get", "post", "head", "options"]  # no PUT/PATCH/DELETE

    def get_queryset(self):
        return Absence.objects.filter(
            student_enrollment__school_class__tenant=_tenant(self.request)
        ).select_related(
            "student_enrollment__student__role__user",
            "student_enrollment__school_class",       # necessario per class_name nel serializer
            "teacher_assignment__teacher__role__user",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "absence.read"
        elif self.action == "create":
            codename = "absence.create"
        elif self.action == "justify":
            # CanJustify gestisce questo caso separatamente
            return [p() for p in _BASE + [CanJustify, HasObjectScope]]
        else:
            codename = "absence.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=["post"], url_path="justify")
    def justify(self, request, pk=None):
        """
        Giustifica un'assenza.
        Solo un genitore o uno studente maggiorenne con scope sul record.
        """
        absence = self.get_object()  # controlla scope
        serializer = AbsenceJustifySerializer(
            absence, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AbsenceSerializer(absence).data, status=status.HTTP_200_OK)


# ==============================================================================
# Tardiness
# ==============================================================================

class TardinessViewSet(viewsets.ModelViewSet):
    """
    Gestione ritardi.

    Permessi:
      POST       → teacher (tardiness.create)
      GET        → teacher, student, parent (tardiness.read)
      PATCH      → solo teacher per aggiornare entry_time (tardiness.update_entry_time)
      PUT/DELETE → 405

    Action:
      POST /tardinesses/<pk>/justify/ → CanJustify + HasObjectScope
    """

    serializer_class = TardinessSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return Tardiness.objects.filter(
            student_enrollment__school_class__tenant=_tenant(self.request)
        ).select_related(
            "student_enrollment__student__role__user",
            "teacher_assignment__teacher__role__user",
        )

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            codename = "tardiness.read"
        elif self.action == "create":
            codename = "tardiness.create"
        elif self.action == "partial_update":
            codename = "tardiness.update_entry_time"
        elif self.action == "justify":
            return [p() for p in _BASE + [CanJustify, HasObjectScope]]
        else:
            codename = "tardiness.read"

        return [p() for p in _BASE + [HasRolePermission(codename), HasObjectScope]]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH limitato al solo campo entry_time per gli insegnanti.
        """
        tardiness = self.get_object()
        serializer = TardinessUpdateEntryTimeSerializer(
            tardiness, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TardinessSerializer(tardiness).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="justify")
    def justify(self, request, pk=None):
        """
        Giustifica un ritardo.
        Solo un genitore o uno studente maggiorenne con scope sul record.
        """
        tardiness = self.get_object()
        serializer = TardinessJustifySerializer(
            tardiness, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TardinessSerializer(tardiness).data, status=status.HTTP_200_OK)


# ==============================================================================
# Lesson
# ==============================================================================

class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint read-only per le lezioni.

    Parametri opzionali:
      ?date=YYYY-MM-DD  → filtra le lezioni di uno specifico giorno
    """

    serializer_class = LessonSerializer

    def get_queryset(self):
        qs = Lesson.objects.filter(
            teacher_class_subject__school_class__tenant=_tenant(self.request)
        ).select_related(
            "teacher_class_subject__subject",
            "teacher_class_subject__school_class",
        )

        date_param = self.request.query_params.get("date")
        if date_param:
            qs = qs.filter(date=date_param)

        return qs.order_by("date", "hour")

    def get_permissions(self):
        return [p() for p in _BASE + [HasRolePermission("lesson.read")]]
