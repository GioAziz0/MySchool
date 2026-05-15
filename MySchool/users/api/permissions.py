"""
Classi di permesso DRF per il sistema mySchool.

Flusso di controllo per ogni operazione:
  1. IsAuthenticated       → già globale in settings
  2. IsActiveTenantMember  → utente ha un ruolo attivo in request.tenant
  3. HasRolePermission(codename) → il ruolo può fare questa azione?
  4. HasObjectScope        → check_object_permissions() → scope sull'oggetto

Scope dell'insegnante su Grade/Note/ecc. verifica SEMPRE classe + materia
tramite TeacherClassSubject, non solo la classe.
"""

from __future__ import annotations

from datetime import date

from rest_framework.permissions import BasePermission, SAFE_METHODS

from users.models import (
    UserRole,
    RolePermission,
    AdminPermission,
    ParentStudentRelation,
)


# ==============================================================================
# Helpers interni
# ==============================================================================

def _get_active_roles(user, tenant):
    """Restituisce tutti i UserRole attivi dell'utente in questo tenant."""
    return UserRole.objects.filter(
        user=user,
        tenant=tenant,
        is_active=True,
    ).select_related("tenant")


def _is_adult(user) -> bool:
    """True se l'utente ha almeno 18 anni."""
    today = date.today()
    bd = user.birth_date
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return age >= 18


def _role_has_permission(role: UserRole, codename: str) -> bool:
    """Verifica se un singolo UserRole possiede il permesso dato."""
    if role.role == UserRole.ROLE_ADMIN:
        # Gli admin hanno solo permessi esplicitamente concessi
        return AdminPermission.objects.filter(
            admin_profile__role=role,
            permission__codename=codename,
        ).exists()

    return RolePermission.objects.filter(
        role=role.role,
        permission__codename=codename,
    ).exists()


def _user_has_permission(user, tenant, codename: str) -> bool:
    """
    True se almeno uno dei ruoli attivi dell'utente nel tenant
    possiede il permesso dato.
    """
    return any(
        _role_has_permission(role, codename)
        for role in _get_active_roles(user, tenant)
    )


# ==============================================================================
# Scope helpers (usati da HasObjectScope)
# ==============================================================================

def _scope_enrollment(role: UserRole, enrollment) -> bool:
    """
    Scope su una StudentEnrollment:
      Studente  → solo la propria iscrizione
      Genitore  → iscrizioni dei propri figli
      Insegnante→ studenti iscritti in una classe in cui ha un TCS attivo
    """
    from core.models import TeacherClassSubject

    if role.role == UserRole.ROLE_STUDENT:
        return (
            hasattr(role, "student_profile")
            and enrollment.student == role.student_profile
        )

    if role.role == UserRole.ROLE_PARENT:
        return ParentStudentRelation.objects.filter(
            parent=role,
            student=enrollment.student.role,
        ).exists()

    if role.role == UserRole.ROLE_TEACHER:
        return TeacherClassSubject.objects.filter(
            assignment__teacher=role.teacher_profile,
            school_class=enrollment.school_class,
        ).exists()

    return False


def _scope_grade(role: UserRole, grade) -> bool:
    """
    Scope su un Grade:
      Insegnante → SOLO se ha un TCS per quella classe E quella materia specifica
      Studente   → solo i propri voti (via enrollment)
      Genitore   → voti dei propri figli (via enrollment)
    """
    if role.role == UserRole.ROLE_TEACHER:
        from core.models import TeacherClassSubject
        return TeacherClassSubject.objects.filter(
            assignment__teacher=role.teacher_profile,
            school_class=grade.student_enrollment.school_class,
            subject=grade.teacher_class_subject.subject,
        ).exists()

    # Studente e genitore: scope derivato dall'enrollment
    return _scope_enrollment(role, grade.student_enrollment)


def _scope_homework(role: UserRole, homework) -> bool:
    """
    Scope su un Homework:
      Insegnante → solo i propri compiti (via TCS)
      Studente   → compiti della propria classe attiva
      Genitore   → compiti delle classi dei propri figli
    """
    from core.models import TeacherClassSubject, StudentEnrollment

    school_class = homework.teacher_class_subject.school_class

    if role.role == UserRole.ROLE_TEACHER:
        return TeacherClassSubject.objects.filter(
            assignment__teacher=role.teacher_profile,
            school_class=school_class,
            subject=homework.teacher_class_subject.subject,
        ).exists()

    if role.role == UserRole.ROLE_STUDENT:
        return StudentEnrollment.objects.filter(
            student=role.student_profile,
            school_class=school_class,
            date_end__isnull=True,
        ).exists()

    if role.role == UserRole.ROLE_PARENT:
        children_roles = ParentStudentRelation.objects.filter(
            parent=role,
        ).values("student")
        return StudentEnrollment.objects.filter(
            student__role__in=children_roles,
            school_class=school_class,
            date_end__isnull=True,
        ).exists()

    return False


def _scope_class(role: UserRole, school_class) -> bool:
    """
    Scope su una SchoolClass:
      Insegnante → le proprie classi (via TCS)
      Studente   → la propria classe attiva
      Genitore   → le classi dei propri figli
    """
    from core.models import TeacherClassSubject, StudentEnrollment

    if role.role == UserRole.ROLE_TEACHER:
        return TeacherClassSubject.objects.filter(
            assignment__teacher=role.teacher_profile,
            school_class=school_class,
        ).exists()

    if role.role == UserRole.ROLE_STUDENT:
        return StudentEnrollment.objects.filter(
            student=role.student_profile,
            school_class=school_class,
            date_end__isnull=True,
        ).exists()

    if role.role == UserRole.ROLE_PARENT:
        children_roles = ParentStudentRelation.objects.filter(
            parent=role,
        ).values("student")
        return StudentEnrollment.objects.filter(
            student__role__in=children_roles,
            school_class=school_class,
            date_end__isnull=True,
        ).exists()

    return False


def _role_has_scope(role: UserRole, obj) -> bool:
    """Dispatch dello scope in base al tipo di oggetto."""
    from core.models import (
        StudentEnrollment,
        SchoolClass,
        Grade,
        StudentNote,
        Homework,
        Absence,
        Tardiness,
    )

    # Admin: scope illimitato sulla propria scuola
    if role.role == UserRole.ROLE_ADMIN:
        return True

    if isinstance(obj, Grade):
        return _scope_grade(role, obj)

    if isinstance(obj, Homework):
        return _scope_homework(role, obj)

    if isinstance(obj, (StudentNote, Absence, Tardiness)):
        return _scope_enrollment(role, obj.student_enrollment)

    if isinstance(obj, StudentEnrollment):
        return _scope_enrollment(role, obj)

    if isinstance(obj, SchoolClass):
        return _scope_class(role, obj)

    return False


def _user_has_scope(user, tenant, obj) -> bool:
    """True se almeno uno dei ruoli attivi dell'utente ha scope sull'oggetto."""
    return any(
        _role_has_scope(role, obj)
        for role in _get_active_roles(user, tenant)
    )


# ==============================================================================
# Permission classes DRF
# ==============================================================================

class IsActiveTenantMember(BasePermission):
    """
    Verifica che:
    1. request.tenant sia stato risolto dal middleware (non None)
    2. L'utente abbia almeno un ruolo attivo in quel tenant
    """

    message = "Non sei membro attivo di questa scuola."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False
        return _get_active_roles(request.user, tenant).exists()


def HasRolePermission(codename: str):
    """
    Factory che restituisce una permission class DRF che controlla
    se l'utente ha il permesso `codename` in request.tenant.

    Uso:
        permission_classes = [IsAuthenticated, IsActiveTenantMember,
                              HasRolePermission("grade.create")]
    """

    class _HasRolePermission(BasePermission):
        message = f"Non hai il permesso di eseguire questa operazione ({codename})."

        def has_permission(self, request, view):
            tenant = getattr(request, "tenant", None)
            if tenant is None:
                return False
            return _user_has_permission(request.user, tenant, codename)

    _HasRolePermission.__name__ = f"HasRolePermission_{codename}"
    return _HasRolePermission


class HasObjectScope(BasePermission):
    """
    Controlla che l'utente abbia scope sull'oggetto specifico.
    Va usato nel metodo get_object() del ViewSet insieme a
    self.check_object_permissions(request, obj).
    """

    message = "Non hai accesso a questo oggetto."

    def has_object_permission(self, request, view, obj):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False
        return _user_has_scope(request.user, tenant, obj)


class CanJustify(BasePermission):
    """
    Permesso per giustificare assenze e ritardi:
      - Genitore → sempre
      - Studente maggiorenne (>= 18 anni) → sì
      - Insegnante / admin → no
    """

    message = "Solo un genitore o uno studente maggiorenne può giustificare."

    def has_permission(self, request, view):
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return False

        roles = _get_active_roles(request.user, tenant)
        for role in roles:
            if role.role == UserRole.ROLE_PARENT:
                return True
            if role.role == UserRole.ROLE_STUDENT and _is_adult(request.user):
                return True

        return False

    def has_object_permission(self, request, view, obj):
        # Lo scope (figlio/proprio) è già garantito da HasObjectScope
        return self.has_permission(request, view)
