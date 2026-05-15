from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    
    fiscal_code = models.CharField(
        max_length=16,
        blank=False,
        null=False,
        unique=True,
        verbose_name="Codice fiscale",
        help_text="16 caratteri alfanumerici. Unico per ogni utente."
    )

    birth_date = models.DateField(
        blank=False,
        null=False,
        verbose_name="Data di nascita"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Numero di telefono"
    )

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
    
class UserRole(models.Model):
    """
    Collega un User a un Tenant (scuola) con un ruolo specifico.

    Questa è la tabella "ponte" del sistema: ogni riga risponde alla domanda
    "chi è questa persona, in questa scuola, con quale ruolo?"

    Esempi di record in questa tabella:
    ┌─────────────────┬──────────────────────────┬──────────┬───────────┐
    │ user            │ tenant                   │ role     │ is_active │
    ├─────────────────┼──────────────────────────┼──────────┼───────────┤
    │ mario.rossi     │ Liceo Einstein           │ teacher  │ True      │
    │ mario.rossi     │ Liceo Galileo            │ teacher  │ True      │
    │ anna.bianchi    │ Liceo Einstein           │ parent   │ True      │
    │ anna.bianchi    │ Liceo Einstein           │ admin    │ True      │
    └─────────────────┴──────────────────────────┴──────────┴───────────┘

    Mario insegna in due scuole → ha due UserRole distinti.
    Anna è sia genitore che admin nella stessa scuola → anche lei due UserRole.
    """

    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"
    ROLE_PARENT  = "parent"
    ROLE_ADMIN   = "admin"

    ROLE_CHOICES = [
        (ROLE_TEACHER, "Insegnante"),
        (ROLE_STUDENT, "Studente"),
        (ROLE_PARENT,  "Genitore"),
        (ROLE_ADMIN,   "Amministratore"),
    ]

    user = models.ForeignKey(
        # "accounts.User" è la stringa lazy: Django risolve il riferimento
        # al modello a runtime, evitando problemi di import circolari.
        # Equivale a: from accounts.models import User
        "users.User",
        on_delete=models.CASCADE,
        related_name="roles",
        verbose_name="Utente",
        # on_delete=CASCADE: se l'utente viene eliminato, anche i suoi
        # ruoli vengono eliminati automaticamente.
        # related_name="roles": permette di fare user.roles.all()
        # per ottenere tutti i ruoli di un utente.
    )

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="user_roles",
        verbose_name="Scuola",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name="Ruolo",
        # choices limita i valori accettati a quelli definiti in ROLE_CHOICES.
        # Django lo valida nei form e lo mostra come menu a tendina nell'admin.
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Attivo",
        help_text=(
            "Permette di disabilitare un ruolo senza eliminarlo. "
            "Es: uno studente che si trasferisce non viene cancellato, "
            "ma il suo ruolo viene disattivato per preservare lo storico dei voti."
        )
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data assegnazione ruolo")

    class Meta:
        verbose_name = "Ruolo utente"
        verbose_name_plural = "Ruoli utenti"
        # unique_together: garantisce che lo stesso utente non possa avere
        # lo stesso ruolo due volte nella stessa scuola.
        # Il database rifiuterà il secondo inserimento con un errore di integrità.
        constraints = [
            models.UniqueConstraint(
                fields=["user", "tenant", "role"],
                name="unique_user_tenant_role"
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.get_role_display()} @ {self.tenant}"
        # get_role_display() è un metodo generato automaticamente da Django
        # per i campi con choices: restituisce la versione leggibile
        # (es: "Insegnante" invece di "teacher").

# ==============================================================================
# LIVELLO 3: PROFILI SPECIFICI PER RUOLO
# ==============================================================================
# Ogni profilo ha una relazione OneToOne con UserRole.
#
# OneToOneField vs ForeignKey:
# - ForeignKey: un UserRole può avere MOLTI voti (uno-a-molti)
# - OneToOneField: un UserRole può avere AL MASSIMO UN profilo (uno-a-uno)
#   È come una ForeignKey con unique=True.
#   Permette di accedere al profilo con: user_role.teacher_profile
#   invece di: user_role.teacherprofile_set.first()
# ==============================================================================

class TeacherProfile(models.Model):
    """
    Dati specifici di un insegnante.
    Esiste solo per UserRole con role='teacher'.
    """

    role = models.OneToOneField(
        UserRole,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={"role": UserRole.ROLE_TEACHER},
        verbose_name="Ruolo associato",
        # limit_choices_to: nel form admin mostra solo i UserRole
        # che hanno role='teacher'. Non è un vincolo a livello di database,
        # ma filtra l'elenco a tendina per evitare errori.
    )

    class Meta:
        verbose_name = "Profilo insegnante"
        verbose_name_plural = "Profili insegnanti"

    def __str__(self):
        return f"Profilo insegnante: {self.role.user}"


class StudentProfile(models.Model):
    """
    Dati specifici di uno studente.
    Esiste solo per UserRole con role='student'.

    """

    role = models.OneToOneField(
        UserRole,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": UserRole.ROLE_STUDENT},
        verbose_name="Ruolo associato",
    )

    enrollment_year = models.IntegerField(
        verbose_name="Anno di iscrizione",
        help_text="Es: 2024 per l'anno scolastico 2024/2025."
    )

    class Meta:
        verbose_name = "Profilo studente"
        verbose_name_plural = "Profili studenti"

    def __str__(self):
        return f"Profilo studente: {self.role.user}"


class ParentProfile(models.Model):
    """
    Dati specifici di un genitore.
    Esiste solo per UserRole con role='parent'.

    Il collegamento ai figli è gestito tramite ParentStudentRelation (sotto),
    che è un modello separato perché la relazione ha attributi propri
    (es: tipo di relazione: madre/padre/tutore legale).
    """

    role = models.OneToOneField(
        UserRole,
        on_delete=models.CASCADE,
        related_name="parent_profile",
        limit_choices_to={"role": UserRole.ROLE_PARENT},
        verbose_name="Ruolo associato",
    )

    class Meta:
        verbose_name = "Profilo genitore"
        verbose_name_plural = "Profili genitori"

    def __str__(self):
        return f"Profilo genitore: {self.role.user}"


class ParentStudentRelation(models.Model):
    """
    Collega un genitore ai propri figli nel sistema.

    Perché un modello separato invece di ManyToManyField in ParentProfile?
    Perché questa relazione ha un attributo proprio: relation_type
    (madre, padre, tutore legale, ecc.). Quando una relazione ha attributi,
    serve un modello esplicito.

    Esempi di record:
    ┌─────────────────┬─────────────────┬────────────────┐
    │ parent          │ student         │ relation_type  │
    ├─────────────────┼─────────────────┼────────────────┤
    │ Anna (genitore) │ Luca (studente) │ madre          │
    │ Marco (genitor) │ Luca (studente) │ padre          │
    └─────────────────┴─────────────────┴────────────────┘
    """

    RELATION_MOTHER  = "mother"
    RELATION_FATHER  = "father"
    RELATION_GUARDIAN = "guardian"

    RELATION_CHOICES = [
        (RELATION_MOTHER,   "Madre"),
        (RELATION_FATHER,   "Padre"),
        (RELATION_GUARDIAN, "Tutore legale"),
    ]

    parent = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name="children_relations",
        limit_choices_to={"role": UserRole.ROLE_PARENT},
        verbose_name="Genitore",
    )

    student = models.ForeignKey(
        UserRole,
        on_delete=models.CASCADE,
        related_name="parent_relations",
        limit_choices_to={"role": UserRole.ROLE_STUDENT},
        verbose_name="Studente (figlio/a)",
    )

    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_CHOICES,
        verbose_name="Tipo di relazione",
    )

    class Meta:
        verbose_name = "Relazione genitore-studente"
        verbose_name_plural = "Relazioni genitore-studente"
        constraints = [
            models.UniqueConstraint(
                fields=["parent", "student"],
                name="unique_parent_student"
                # Un genitore non può essere collegato due volte allo stesso figlio.
            )
        ]

    def __str__(self):
        return (
            f"{self.get_relation_type_display()} di {self.student.user}: "
            f"{self.parent.user}"
        )


class AdminProfile(models.Model):
    """
    Dati specifici di un amministratore.
    Esiste solo per UserRole con role='admin'.

    I permessi di un admin sono configurabili individualmente tramite
    AdminPermission. L'ambito (scope) è illimitato per definizione:
    un admin può operare su tutte le classi e tutti gli utenti della
    propria scuola, ma solo sulle operazioni per cui ha il permesso.
    """

    role = models.OneToOneField(
        UserRole,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        limit_choices_to={"role": UserRole.ROLE_ADMIN},
        verbose_name="Ruolo associato",
    )

    class Meta:
        verbose_name = "Profilo amministratore"
        verbose_name_plural = "Profili amministratori"

    def __str__(self):
        return f"Profilo admin: {self.role.user} @ {self.role.tenant}"


# ==============================================================================
# SISTEMA PERMESSI
# ==============================================================================
# Permission     → catalogo di operazioni possibili (codenames)
# RolePermission → associa un ruolo (stringa) a una Permission:
#                  tutti gli utenti con quel ruolo la possiedono
# AdminPermission→ associa un singolo AdminProfile a una Permission:
#                  consente permessi granulari per singolo admin
# ==============================================================================


class Permission(models.Model):
    """
    Catalogo dei permessi disponibili nel sistema.

    I codenames seguono la convenzione <entità>.<azione>.
    Es: 'grade.create', 'absence.justify'.
    """

    codename = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Codename",
        help_text="Identificatore univoco del permesso. Es: grade.create",
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrizione",
    )

    class Meta:
        verbose_name = "Permesso"
        verbose_name_plural = "Permessi"
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class RolePermission(models.Model):
    """
    Associa un ruolo generico a un permesso.

    Tutti gli utenti con quel ruolo possiedono automaticamente il permesso.
    Non si applica agli admin, che usano AdminPermission.
    """

    role = models.CharField(
        max_length=20,
        choices=UserRole.ROLE_CHOICES,
        verbose_name="Ruolo",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
        verbose_name="Permesso",
    )

    class Meta:
        verbose_name = "Permesso per ruolo"
        verbose_name_plural = "Permessi per ruolo"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="unique_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.get_role_display()} → {self.permission}"


class AdminPermission(models.Model):
    """
    Permesso granulare assegnato manualmente a un singolo admin.

    Gli admin non hanno permessi di default: ogni permesso deve essere
    concesso esplicitamente tramite questo modello dal superuser.
    """

    admin_profile = models.ForeignKey(
        AdminProfile,
        on_delete=models.CASCADE,
        related_name="granted_permissions",
        verbose_name="Admin",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="admin_permissions",
        verbose_name="Permesso",
    )

    class Meta:
        verbose_name = "Permesso admin"
        verbose_name_plural = "Permessi admin"
        constraints = [
            models.UniqueConstraint(
                fields=["admin_profile", "permission"],
                name="unique_admin_permission",
            )
        ]

    def __str__(self):
        return f"{self.admin_profile} → {self.permission}"

