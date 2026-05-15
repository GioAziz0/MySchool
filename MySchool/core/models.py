from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class SchoolClass(models.Model):
    """Una classe scolastica appartenente a una scuola e a un anno scolastico."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="school_classes",
        verbose_name="Scuola",
    )

    name = models.CharField(
        max_length=50,
        verbose_name="Nome classe",
        help_text="Es: 5IE, 3A, 1B",
    )

    school_year = models.CharField(
        max_length=9,
        verbose_name="Anno scolastico",
        help_text="Formato AAAA/AAAA. Es: 2024/2025",
    )

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classi"
        ordering = ["school_year", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name", "school_year"],
                name="unique_class_per_year_per_school",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.school_year})"


class Subject(models.Model):
    """Una materia scolastica appartenente a una scuola."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name="Scuola",
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Nome materia",
        help_text="Es: Matematica, Italiano, Fisica",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descrizione",
    )

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materie"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_subject_per_school",
            )
        ]

    def __str__(self):
        return self.name


# ==============================================================================
# ENTITÀ DI PERIODO: ISCRIZIONE STUDENTE E INCARICO INSEGNANTE
# ==============================================================================
# Queste entità rappresentano un "periodo" in cui
# uno studente è iscritto a una classe o un insegnante ha un incarico attivo.
# Permettono di gestire anni scolastici diversi o cambi di classe/sezione
# mantenendo lo storico completo dei dati (voti, note, assenze, ecc.).
# ==============================================================================

class StudentEnrollment(models.Model):
    """
    Iscrizione di uno studente a una classe per un determinato periodo.

    Ogni cambio di classe o anno scolastico produce una nuova iscrizione,
    lasciando invariata quella precedente per preservare lo storico.

    Esempi di record:
    ┌──────────────┬────────┬────────────┬────────────┐
    │ student      │ class  │ date_start │ date_end   │
    ├──────────────┼────────┼────────────┼────────────┤
    │ luca.verdi   │ 4IE    │ 2023-09-11 │ 2024-06-10 │
    │ luca.verdi   │ 5IE    │ 2024-09-09 │ None       │  ← iscrizione attiva
    └──────────────┴────────┴────────────┴────────────┘
    """

    student = models.ForeignKey(
        "users.StudentProfile",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Studente",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name="Classe",
    )

    date_start = models.DateField(verbose_name="Data inizio")

    date_end = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data fine",
        help_text="Lasciare vuoto se l'iscrizione è ancora attiva.",
    )

    class Meta:
        verbose_name = "Iscrizione studente"
        verbose_name_plural = "Iscrizioni studenti"
        ordering = ["-date_start"]

    def __str__(self):
        return f"{self.student.role.user} — {self.school_class}"


class TeacherAssignment(models.Model):
    """
    Incarico di un insegnante per un determinato periodo scolastico.

    Le associazioni con classi e materie vengono specificate tramite
    TeacherClassSubject: un insegnante può insegnare materie diverse
    in classi diverse, ma una sola materia per classe nell'ambito
    dello stesso incarico.
    """

    teacher = models.ForeignKey(
        "users.TeacherProfile",
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Insegnante",
    )

    date_start = models.DateField(verbose_name="Data inizio")

    date_end = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data fine",
        help_text="Lasciare vuoto se l'incarico è ancora attivo.",
    )

    class Meta:
        verbose_name = "Incarico insegnante"
        verbose_name_plural = "Incarichi insegnanti"
        ordering = ["-date_start"]

    def __str__(self):
        end = self.date_end or "attivo"
        return f"{self.teacher.role.user} ({self.date_start} → {end})"


class TeacherClassSubject(models.Model):
    """
    Associa un incarico insegnante a una specifica classe e materia.

    Un insegnante può insegnare più materie nella stessa classe e materie
    diverse in classi diverse. Il vincolo impedisce solo di assegnare la
    stessa materia due volte allo stesso insegnante nella stessa classe.

    Esempi di record per un insegnante di Italiano e Storia:
    ┌────────────────┬────────┬─────────┐
    │ assignment     │ class  │ subject │
    ├────────────────┼────────┼─────────┤
    │ rossi (24/25)  │ 5IE    │ Italiano│
    │ rossi (24/25)  │ 5IE    │ Storia  │
    │ rossi (24/25)  │ 3B     │ Italiano│
    └────────────────┴────────┴─────────┘
    """

    assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name="class_subjects",
        verbose_name="Incarico",
    )

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="teacher_class_subjects",
        verbose_name="Classe",
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="teacher_class_subjects",
        verbose_name="Materia",
    )

    class Meta:
        verbose_name = "Assegnazione classe-materia"
        verbose_name_plural = "Assegnazioni classe-materia"
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "school_class", "subject"],
                name="unique_subject_per_teacher_per_class",
            )
        ]

    def __str__(self):
        return (
            f"{self.assignment.teacher.role.user} — "
            f"{self.subject} ({self.school_class})"
        )


# ==============================================================================
# REGISTRO: LEZIONI, VOTI, NOTE, COMPITI, PRESENZE
# ==============================================================================
# Lesson è l'entità centrale del registro: "firmare un'ora" significa
# che l'insegnante certifica la propria presenza e può agire su quell'ora
# (assegnare voti, scrivere note, registrare assenze/ritardi, ecc.).
#
# Grade, Homework e Lesson referenziano TeacherClassSubject perché
# richiedono il contesto completo insegnante + classe + materia.
# StudentNote, Absence e Tardiness referenziano TeacherAssignment
# perché possono essere registrate da qualsiasi insegnante.
# Tutte le entità registrabili hanno un campo lesson obbligatorio: ogni azione
# deve essere ricondotta alla lezione durante la quale è avvenuta (tracciabilità
# e responsabilità dell'insegnante). on_delete=PROTECT impedisce l'eliminazione
# di una lezione finché esistono record ad essa collegati.
# ==============================================================================

class Lesson(models.Model):
    """
    Firma di un'ora sul registro da parte di un insegnante.

    Certifica che l'insegnante ha tenuto quella lezione in quella classe
    per quella materia. È il punto di riferimento per le azioni
    didattiche legate a una specifica ora (voti orali, compiti, ecc.).
    """

    teacher_class_subject = models.ForeignKey(
        TeacherClassSubject,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Insegnante / Classe / Materia",
    )

    date = models.DateField(verbose_name="Data")

    hour = models.PositiveSmallIntegerField(
        verbose_name="Ora",
        help_text="Numero progressivo dell'ora nella giornata. Es: 1 per la prima ora.",
        validators=[MinValueValidator(1), MaxValueValidator(12)],
    )

    description = models.TextField(
        blank=True,
        verbose_name="Argomenti trattati",
    )

    class Meta:
        verbose_name = "Lezione"
        verbose_name_plural = "Lezioni"
        ordering = ["date", "hour"]
        constraints = [
            models.UniqueConstraint(
                fields=["teacher_class_subject", "date", "hour"],
                name="unique_lesson_per_teacher_class_hour",
            )
        ]

    def __str__(self):
        tcs = self.teacher_class_subject
        return f"{tcs.subject} — {tcs.school_class} — {self.date} ora {self.hour}"


class Grade(models.Model):
    """Voto assegnato a uno studente da un insegnante per una materia."""

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Iscrizione studente",
    )

    teacher_class_subject = models.ForeignKey(
        TeacherClassSubject,
        on_delete=models.CASCADE,
        related_name="grades",
        verbose_name="Insegnante / Materia",
        # Già contiene materia e classe: non serve un campo subject separato.
    )

    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.PROTECT,
        related_name="grades",
        verbose_name="Lezione di riferimento",
    )

    date = models.DateField(verbose_name="Data")

    value = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        verbose_name="Voto",
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Voto da 1.00 a 10.00.",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descrizione",
        help_text="Es: interrogazione orale, compito in classe, verifica scritta.",
    )

    class Meta:
        verbose_name = "Voto"
        verbose_name_plural = "Voti"
        ordering = ["-date"]

    def __str__(self):
        student = self.student_enrollment.student.role.user
        subject = self.teacher_class_subject.subject
        return f"{student} — {subject}: {self.value}"


class StudentNote(models.Model):
    """
    Nota scritta da un insegnante su uno studente.

    Può essere informativa (es: comportamento) o disciplinare.
    Non è legata a una materia specifica: qualsiasi insegnante
    può registrare una nota tramite il proprio TeacherAssignment.
    """

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="Iscrizione studente",
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name="Insegnante",
    )

    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.PROTECT,
        related_name="notes",
        verbose_name="Lezione di riferimento",
    )

    date = models.DateField(verbose_name="Data")

    description = models.TextField(verbose_name="Descrizione")

    is_disciplinary = models.BooleanField(
        default=False,
        verbose_name="Disciplinare",
        help_text="True se la nota ha rilevanza disciplinare.",
    )

    class Meta:
        verbose_name = "Nota"
        verbose_name_plural = "Note"
        ordering = ["-date"]

    def __str__(self):
        kind = "disciplinare" if self.is_disciplinary else "informativa"
        student = self.student_enrollment.student.role.user
        return f"Nota {kind} — {student} ({self.date})"


class Homework(models.Model):
    """Compito assegnato da un insegnante a una classe per una materia."""

    teacher_class_subject = models.ForeignKey(
        TeacherClassSubject,
        on_delete=models.CASCADE,
        related_name="homework_assignments",
        verbose_name="Insegnante / Classe / Materia",
    )

    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.PROTECT,
        related_name="homework_assignments",
        verbose_name="Lezione di riferimento",
    )

    assigned_date = models.DateField(verbose_name="Data assegnazione")

    due_date = models.DateField(verbose_name="Data consegna")

    description = models.TextField(verbose_name="Descrizione")

    class Meta:
        verbose_name = "Compito"
        verbose_name_plural = "Compiti"
        ordering = ["due_date"]

    def __str__(self):
        tcs = self.teacher_class_subject
        return f"{tcs.subject} — {tcs.school_class} — consegna: {self.due_date}"


class Absence(models.Model):
    """
    Assenza giornaliera di uno studente.

    L'insegnante che registra l'assenza è tipicamente quello presente
    durante l'appello (prima ora o ora corrente).
    Un solo record per studente per giorno: vincolo unique_absence_per_student_per_day.
    """

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="absences",
        verbose_name="Iscrizione studente",
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name="recorded_absences",
        verbose_name="Insegnante che registra",
    )

    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.PROTECT,
        related_name="absences",
        verbose_name="Lezione di riferimento",
    )

    date = models.DateField(verbose_name="Data")

    is_justified = models.BooleanField(
        default=False,
        verbose_name="Giustificata",
    )

    justification = models.TextField(
        blank=True,
        verbose_name="Motivazione giustifica",
    )

    class Meta:
        verbose_name = "Assenza"
        verbose_name_plural = "Assenze"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["student_enrollment", "date"],
                name="unique_absence_per_student_per_day",
            )
        ]

    def __str__(self):
        student = self.student_enrollment.student.role.user
        return f"Assenza — {student} ({self.date})"


class Tardiness(models.Model):
    """
    Ritardo di uno studente: ingresso successivo all'orario di inizio lezioni.

    needs_justification: True se il ritardo supera la soglia che richiede
    giustificazione scritta (es: oltre 15 minuti).
    is_justified: True se la giustificazione è stata presentata e accettata.
    """

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="tardinesses",
        verbose_name="Iscrizione studente",
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name="recorded_tardinesses",
        verbose_name="Insegnante che registra",
    )

    lesson = models.ForeignKey(
        "Lesson",
        on_delete=models.PROTECT,
        related_name="tardinesses",
        verbose_name="Lezione di riferimento",
    )

    date = models.DateField(verbose_name="Data")

    entry_time = models.TimeField(verbose_name="Ora di ingresso")

    needs_justification = models.BooleanField(
        default=True,
        verbose_name="Da giustificare",
        help_text="True se il ritardo richiede giustificazione scritta.",
    )

    is_justified = models.BooleanField(
        default=False,
        verbose_name="Giustificato",
    )

    justification = models.TextField(
        blank=True,
        verbose_name="Motivazione giustifica",
    )

    class Meta:
        verbose_name = "Ritardo"
        verbose_name_plural = "Ritardi"
        ordering = ["-date", "entry_time"]

    def __str__(self):
        student = self.student_enrollment.student.role.user
        return f"Ritardo — {student} ({self.date} ore {self.entry_time})"
