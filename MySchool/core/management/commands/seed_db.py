import random
from datetime import date, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from tenants.models import Tenant
from users.models import (
    User, UserRole, TeacherProfile, StudentProfile,
    ParentProfile, AdminProfile, ParentStudentRelation,
    Permission, RolePermission, AdminPermission,
)
from core.models import (
    SchoolClass, Subject, StudentEnrollment, TeacherAssignment,
    TeacherClassSubject, Lesson, Grade, StudentNote, Homework,
    Absence, Tardiness,
)

PASSWORD    = "Password123!"
SCHOOL_YEAR = "2025/2026"
YEAR_START  = date(2025, 9, 9)
TODAY       = date(2026, 5, 14)

_HOLIDAYS = frozenset({
    date(2025, 11, 1),
    date(2025, 12, 8),
    *(date(2025, 12, d) for d in range(22, 32)),
    *(date(2026, 1,  d) for d in range(1, 8)),
    *(date(2026, 4,  d) for d in range(3, 9)),
    date(2026, 4, 25),
    date(2026, 5, 1),
})

_LESSON_TOPICS = {
    "Matematica":       ["Equazioni differenziali", "Integrali", "Limiti e continuità",
                         "Derivate", "Geometria analitica", "Probabilità"],
    "Fisica":           ["Elettromagnetismo", "Ottica geometrica", "Onde meccaniche",
                         "Termodinamica", "Campo elettrico", "Circuiti RC"],
    "Italiano":         ["Leopardi — I Canti", "Manzoni — I Promessi Sposi",
                         "Dante — Paradiso", "Ungaretti", "Montale — Ossi di seppia",
                         "Svevo — La coscienza di Zeno"],
    "Storia":           ["Prima guerra mondiale", "Fascismo e nazismo",
                         "Seconda guerra mondiale", "Guerra fredda", "Resistenza italiana"],
    "Inglese":          ["Present perfect vs. simple past", "Reading comprehension",
                         "Essay writing", "Listening: BBC podcast", "Grammar review"],
    "Scienze Naturali": ["Genetica mendeliana", "Teoria dell'evoluzione",
                         "Biochimica — proteine", "Ecosistemi e biomi", "DNA e RNA"],
    "Informatica":      ["Algoritmi e complessità", "Database relazionali",
                         "Python — OOP", "Reti TCP/IP", "Sicurezza informatica"],
    "Sistemi e Reti":   ["Protocollo HTTP", "Architetture client-server",
                         "Configurazione router", "Firewall e DMZ"],
}


def _school_days():
    d = YEAR_START
    while d <= TODAY:
        if d.weekday() < 5 and d not in _HOLIDAYS:
            yield d
        d += timedelta(days=1)


class Command(BaseCommand):
    help = "Popola il database con dati di test. Tutti gli utenti: password Password123!"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._uid_counter = 0

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _uid(self):
        self._uid_counter += 1
        return f"FAKE{self._uid_counter:012d}"

    def _user(self, username, first_name, last_name, birth_year):
        u, _ = User.objects.get_or_create(
            username=username,
            defaults=dict(
                first_name=first_name,
                last_name=last_name,
                email=f"{username}@example.com",
                fiscal_code=self._uid(),
                birth_date=date(birth_year, random.randint(1, 12), random.randint(1, 28)),
            ),
        )
        u.set_password(PASSWORD)
        u.save(update_fields=["password"])
        return u

    # ------------------------------------------------------------------
    # entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        random.seed(42)
        self.stdout.write("Avvio seed del database…")
        with transaction.atomic():
            perm_map = self._setup_permissions()
            einstein = self._create_einstein(perm_map)
            self._create_registry_einstein(einstein)
            self._create_marconi(perm_map)
        self._print_summary()

    # ------------------------------------------------------------------
    # permissions
    # ------------------------------------------------------------------

    def _setup_permissions(self):
        P = Permission
        perms_data = [
            (P.SIGN_LESSON,        "Firma lezione",             P.CATEGORY_REGISTRY),
            (P.ASSIGN_GRADE,       "Assegna voto",              P.CATEGORY_REGISTRY),
            (P.WRITE_NOTE,         "Scrivi nota",               P.CATEGORY_REGISTRY),
            (P.RECORD_ABSENCE,     "Registra assenza",          P.CATEGORY_REGISTRY),
            (P.RECORD_TARDINESS,   "Registra ritardo",          P.CATEGORY_REGISTRY),
            (P.ASSIGN_HOMEWORK,    "Assegna compiti",           P.CATEGORY_REGISTRY),
            (P.JUSTIFY_ABSENCE,    "Giustifica assenza",        P.CATEGORY_REGISTRY),
            (P.JUSTIFY_TARDINESS,  "Giustifica ritardo",        P.CATEGORY_REGISTRY),
            (P.VIEW_GRADES,        "Visualizza voti",           P.CATEGORY_GRADEBOOK),
            (P.VIEW_ABSENCES,      "Visualizza assenze",        P.CATEGORY_GRADEBOOK),
            (P.VIEW_TARDINESS,     "Visualizza ritardi",        P.CATEGORY_GRADEBOOK),
            (P.VIEW_HOMEWORK,      "Visualizza compiti",        P.CATEGORY_GRADEBOOK),
            (P.VIEW_REGISTRY,      "Visualizza registro",       P.CATEGORY_GRADEBOOK),
            (P.VIEW_NOTES,         "Visualizza note",           P.CATEGORY_GRADEBOOK),
            (P.VIEW_USER_INFO,     "Visualizza dati personali", P.CATEGORY_PERSONAL),
            (P.CHANGE_USER_INFO,   "Modifica dati personali",   P.CATEGORY_PERSONAL),
            (P.MANAGE_CLASSES,     "Gestisci classi",           P.CATEGORY_ADMIN),
            (P.MANAGE_SUBJECTS,    "Gestisci materie",          P.CATEGORY_ADMIN),
            (P.MANAGE_ENROLLMENTS, "Gestisci iscrizioni",       P.CATEGORY_ADMIN),
            (P.MANAGE_ASSIGNMENTS, "Gestisci incarichi",        P.CATEGORY_ADMIN),
            (P.MANAGE_ROLES,       "Gestisci ruoli",            P.CATEGORY_ADMIN),
        ]

        perm_map = {}
        for codename, name, category in perms_data:
            p, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={"name": name, "category": category},
            )
            perm_map[codename] = p

        role_defaults = {
            UserRole.ROLE_TEACHER: [
                P.SIGN_LESSON, P.ASSIGN_GRADE, P.WRITE_NOTE,
                P.RECORD_ABSENCE, P.RECORD_TARDINESS, P.ASSIGN_HOMEWORK,
                P.VIEW_GRADES, P.VIEW_ABSENCES, P.VIEW_TARDINESS,
                P.VIEW_HOMEWORK, P.VIEW_REGISTRY, P.VIEW_NOTES,
                P.VIEW_USER_INFO,
            ],
            UserRole.ROLE_STUDENT: [
                P.VIEW_GRADES, P.VIEW_ABSENCES, P.VIEW_TARDINESS,
                P.VIEW_HOMEWORK, P.VIEW_REGISTRY, P.VIEW_NOTES,
                P.VIEW_USER_INFO,
            ],
            UserRole.ROLE_PARENT: [
                P.VIEW_GRADES, P.VIEW_ABSENCES, P.VIEW_TARDINESS,
                P.VIEW_HOMEWORK, P.VIEW_NOTES,
                P.JUSTIFY_ABSENCE, P.JUSTIFY_TARDINESS,
                P.VIEW_USER_INFO,
            ],
            UserRole.ROLE_ADMIN: [
                P.MANAGE_CLASSES, P.MANAGE_SUBJECTS, P.MANAGE_ENROLLMENTS,
                P.MANAGE_ASSIGNMENTS, P.MANAGE_ROLES, P.VIEW_USER_INFO,
            ],
        }

        for role, codenames in role_defaults.items():
            for codename in codenames:
                RolePermission.objects.get_or_create(
                    role=role, permission=perm_map[codename],
                )

        self.stdout.write(
            f"  ✓ {len(perm_map)} permessi, "
            f"{RolePermission.objects.count()} RolePermission"
        )
        return perm_map

    # ------------------------------------------------------------------
    # Einstein — struttura
    # ------------------------------------------------------------------

    def _create_einstein(self, perm_map):
        P = Permission

        tenant, _ = Tenant.objects.get_or_create(
            slug="liceo-einstein",
            defaults={"name": "Liceo Scientifico Einstein"},
        )

        # subjects
        subjects = {}
        for name in [
            "Matematica", "Fisica", "Italiano", "Storia",
            "Inglese", "Scienze Naturali", "Filosofia", "Arte e Immagine",
        ]:
            s, _ = Subject.objects.get_or_create(tenant=tenant, name=name)
            subjects[name] = s

        # classes
        cls_5ie, _ = SchoolClass.objects.get_or_create(
            tenant=tenant, name="5IE", school_year=SCHOOL_YEAR,
        )
        cls_4ie, _ = SchoolClass.objects.get_or_create(
            tenant=tenant, name="4IE", school_year=SCHOOL_YEAR,
        )

        # admins
        preside_perms = [
            P.MANAGE_CLASSES, P.MANAGE_SUBJECTS, P.MANAGE_ENROLLMENTS,
            P.MANAGE_ASSIGNMENTS, P.MANAGE_ROLES, P.VIEW_USER_INFO,
            P.CHANGE_USER_INFO, P.VIEW_GRADES, P.VIEW_NOTES,
        ]
        seg_perms = [
            P.MANAGE_ENROLLMENTS, P.MANAGE_ROLES,
            P.VIEW_USER_INFO, P.CHANGE_USER_INFO,
        ]
        for username, fn, ln, by, extra_perms in [
            ("preside.einstein",    "Maria", "Conti", 1968, preside_perms),
            ("segreteria.einstein", "Paolo", "Neri",  1975, seg_perms),
        ]:
            u = self._user(username, fn, ln, by)
            role, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_ADMIN,
                defaults={"is_active": True},
            )
            admin_profile, _ = AdminProfile.objects.get_or_create(role=role)
            for codename in extra_perms:
                AdminPermission.objects.get_or_create(
                    admin_profile=admin_profile,
                    permission=perm_map[codename],
                )

        # teachers + assignments
        teachers = {}
        assignments = {}
        for username, fn, ln, by, key in [
            ("prof.rossi",   "Marco", "Rossi",   1978, "rossi"),
            ("prof.bianchi", "Laura", "Bianchi", 1982, "bianchi"),
            ("prof.verde",   "Carla", "Verde",   1975, "verde"),
        ]:
            u = self._user(username, fn, ln, by)
            role, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_TEACHER,
                defaults={"is_active": True},
            )
            profile, _ = TeacherProfile.objects.get_or_create(role=role)
            ta, _ = TeacherAssignment.objects.get_or_create(
                teacher=profile, date_start=YEAR_START,
                defaults={"date_end": None},
            )
            teachers[key] = profile
            assignments[key] = ta

        # TeacherClassSubjects (9 total)
        # rossi:   Matematica+Fisica in 5IE, Matematica in 4IE
        # bianchi: Italiano+Storia in 5IE, Italiano in 4IE
        # verde:   Inglese+Scienze Naturali in 5IE, Inglese in 4IE
        tcs_defs = [
            ("rossi",   "Matematica",       cls_5ie),
            ("rossi",   "Fisica",           cls_5ie),
            ("rossi",   "Matematica",       cls_4ie),
            ("bianchi", "Italiano",         cls_5ie),
            ("bianchi", "Storia",           cls_5ie),
            ("bianchi", "Italiano",         cls_4ie),
            ("verde",   "Inglese",          cls_5ie),
            ("verde",   "Scienze Naturali", cls_5ie),
            ("verde",   "Inglese",          cls_4ie),
        ]
        # key: (teacher_key, subject_name, class_name)
        tcs_map = {}
        for tkey, sname, cls in tcs_defs:
            tcs, _ = TeacherClassSubject.objects.get_or_create(
                assignment=assignments[tkey],
                school_class=cls,
                subject=subjects[sname],
            )
            tcs_map[(tkey, sname, cls.name)] = tcs

        # students 5IE
        enrollments_5ie = []
        student_roles_5ie = []
        for username, fn, ln, by in [
            ("luca.verdi",      "Luca",    "Verdi",    2007),
            ("marco.ferrari",   "Marco",   "Ferrari",  2007),
            ("sofia.ricci",     "Sofia",   "Ricci",    2007),
            ("giulia.esposito", "Giulia",  "Esposito", 2008),
            ("antonio.mancini", "Antonio", "Mancini",  2007),
        ]:
            u = self._user(username, fn, ln, by)
            role, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_STUDENT,
                defaults={"is_active": True},
            )
            profile, _ = StudentProfile.objects.get_or_create(
                role=role, defaults={"enrollment_year": 2025},
            )
            enr, _ = StudentEnrollment.objects.get_or_create(
                student=profile, school_class=cls_5ie,
                defaults={"date_start": YEAR_START},
            )
            enrollments_5ie.append(enr)
            student_roles_5ie.append(role)

        # students 4IE
        enrollments_4ie = []
        student_roles_4ie = []
        for username, fn, ln, by in [
            ("emma.romano",    "Emma",   "Romano",   2008),
            ("matteo.colombo", "Matteo", "Colombo",  2008),
            ("alice.fontana",  "Alice",  "Fontana",  2009),
            ("davide.russo",   "Davide", "Russo",    2008),
        ]:
            u = self._user(username, fn, ln, by)
            role, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_STUDENT,
                defaults={"is_active": True},
            )
            profile, _ = StudentProfile.objects.get_or_create(
                role=role, defaults={"enrollment_year": 2025},
            )
            enr, _ = StudentEnrollment.objects.get_or_create(
                student=profile, school_class=cls_4ie,
                defaults={"date_start": YEAR_START},
            )
            enrollments_4ie.append(enr)
            student_roles_4ie.append(role)

        # parents
        for username, fn, ln, by, child_role, rel in [
            ("genitore.verdi",   "Anna",    "Verdi",   1975,
             student_roles_5ie[0], ParentStudentRelation.RELATION_MOTHER),
            ("genitore.ferrari", "Roberto", "Ferrari", 1972,
             student_roles_5ie[1], ParentStudentRelation.RELATION_FATHER),
            ("genitore.ricci",   "Franca",  "Ricci",   1973,
             student_roles_5ie[2], ParentStudentRelation.RELATION_GUARDIAN),
        ]:
            u = self._user(username, fn, ln, by)
            role, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_PARENT,
                defaults={"is_active": True},
            )
            ParentProfile.objects.get_or_create(role=role)
            ParentStudentRelation.objects.get_or_create(
                parent=role, student=child_role,
                defaults={"relation_type": rel},
            )

        self.stdout.write("  ✓ Einstein: struttura scolastica e utenti creati")

        return {
            "tenant": tenant,
            "tcs_map": tcs_map,
            "assignments": assignments,
            "enrollments_5ie": enrollments_5ie,
            "enrollments_4ie": enrollments_4ie,
        }

    # ------------------------------------------------------------------
    # Einstein — registro
    # ------------------------------------------------------------------

    def _create_registry_einstein(self, ctx):
        tcs_map  = ctx["tcs_map"]
        asn      = ctx["assignments"]
        e5       = ctx["enrollments_5ie"]
        e4       = ctx["enrollments_4ie"]

        # Weekly timetable: weekday → [(hour, tcs_key)]
        timetable = {
            0: [  # Monday
                (1, ("rossi",   "Matematica",       "5IE")),
                (2, ("rossi",   "Fisica",           "5IE")),
                (3, ("bianchi", "Italiano",         "5IE")),
                (4, ("bianchi", "Storia",           "5IE")),
                (5, ("verde",   "Inglese",          "5IE")),
            ],
            1: [  # Tuesday
                (1, ("rossi",   "Matematica",       "4IE")),
                (2, ("bianchi", "Italiano",         "4IE")),
                (3, ("verde",   "Inglese",          "4IE")),
                (4, ("verde",   "Scienze Naturali", "5IE")),
            ],
            2: [  # Wednesday
                (1, ("rossi",   "Matematica",       "5IE")),
                (2, ("rossi",   "Fisica",           "5IE")),
                (3, ("bianchi", "Italiano",         "5IE")),
                (4, ("verde",   "Inglese",          "5IE")),
            ],
            3: [  # Thursday
                (1, ("bianchi", "Italiano",         "4IE")),
                (2, ("bianchi", "Storia",           "5IE")),
                (3, ("rossi",   "Matematica",       "4IE")),
                (4, ("verde",   "Scienze Naturali", "5IE")),
            ],
            4: [  # Friday
                (1, ("verde",   "Inglese",          "5IE")),
                (2, ("verde",   "Inglese",          "4IE")),
                (3, ("rossi",   "Fisica",           "5IE")),
            ],
        }

        # --- Lessons (bulk) ---
        existing = set(
            Lesson.objects.filter(
                teacher_class_subject__in=tcs_map.values()
            ).values_list("teacher_class_subject_id", "date", "hour")
        )

        to_create = []
        for d in _school_days():
            wd = d.weekday()
            if wd not in timetable:
                continue
            for hour, tcs_key in timetable[wd]:
                tcs_obj = tcs_map[tcs_key]
                if (tcs_obj.id, d, hour) in existing:
                    continue
                subj  = tcs_key[1]
                desc  = random.choice(_LESSON_TOPICS.get(subj, ["Lezione"]))
                to_create.append(
                    Lesson(
                        teacher_class_subject=tcs_obj,
                        date=d, hour=hour, description=desc,
                    )
                )

        Lesson.objects.bulk_create(to_create, ignore_conflicts=True)

        # Index lessons
        tcs_id_to_key = {v.id: k for k, v in tcs_map.items()}
        lessons_by_tcs: dict[tuple, list[Lesson]] = {k: [] for k in tcs_map}
        lessons_by_date_class: dict[tuple, list[Lesson]] = {}

        for lesson in Lesson.objects.filter(teacher_class_subject__in=tcs_map.values()):
            key = tcs_id_to_key[lesson.teacher_class_subject_id]
            lessons_by_tcs[key].append(lesson)
            cls_name = key[2]
            lessons_by_date_class.setdefault((lesson.date, cls_name), []).append(lesson)

        total_lessons = sum(len(v) for v in lessons_by_tcs.values())
        self.stdout.write(f"  ✓ {total_lessons} lezioni Einstein")

        # --- Grades ---
        grade_count = 0
        desc_choices = ["Interrogazione orale", "Compito in classe", "Verifica scritta", "Test rapido"]
        for tcs_key, lesson_list in lessons_by_tcs.items():
            tcs_obj  = tcs_map[tcs_key]
            cls_name = tcs_key[2]
            enrollments = e5 if cls_name == "5IE" else e4

            if len(lesson_list) < 3:
                continue

            for enr in enrollments:
                n = random.randint(2, 3)
                for lesson in random.sample(lesson_list, n):
                    _, created = Grade.objects.get_or_create(
                        student_enrollment=enr,
                        teacher_class_subject=tcs_obj,
                        lesson=lesson,
                        defaults={
                            "date": lesson.date,
                            "value": Decimal(str(round(random.uniform(4.0, 10.0), 2))),
                            "description": random.choice(desc_choices),
                        },
                    )
                    if created:
                        grade_count += 1

        self.stdout.write(f"  ✓ {grade_count} voti Einstein")

        # --- Absences ---
        all_days = list(_school_days())
        absence_count = 0

        for enr in e5 + e4:
            cls_name    = "5IE" if enr in e5 else "4IE"
            absent_days = random.sample(all_days, 10)

            for d in absent_days:
                day_lessons = lessons_by_date_class.get((d, cls_name), [])
                if not day_lessons:
                    continue
                lesson = day_lessons[0]
                ta     = lesson.teacher_class_subject.assignment
                is_just = random.random() > 0.4
                _, created = Absence.objects.get_or_create(
                    student_enrollment=enr,
                    date=d,
                    defaults={
                        "teacher_assignment": ta,
                        "lesson": lesson,
                        "is_justified": is_just,
                        "justification": "Motivi di salute" if is_just else "",
                    },
                )
                if created:
                    absence_count += 1

        self.stdout.write(f"  ✓ {absence_count} assenze Einstein")

        # --- Tardiness ---
        tardiness_count = 0

        for enr in e5 + e4:
            cls_name     = "5IE" if enr in e5 else "4IE"
            absent_dates = set(
                Absence.objects.filter(student_enrollment=enr)
                .values_list("date", flat=True)
            )
            available = [d for d in all_days if d not in absent_dates]
            tardy_days = random.sample(available, min(4, len(available)))

            for d in tardy_days:
                day_lessons = lessons_by_date_class.get((d, cls_name), [])
                if not day_lessons:
                    continue
                lesson  = day_lessons[0]
                ta      = lesson.teacher_class_subject.assignment
                minutes = random.randint(8, 45)
                is_just = random.random() > 0.5
                Tardiness.objects.get_or_create(
                    student_enrollment=enr,
                    date=d,
                    defaults={
                        "teacher_assignment": ta,
                        "lesson": lesson,
                        "entry_time": time(8, minutes),
                        "needs_justification": minutes > 20,
                        "is_justified": is_just,
                        "justification": "Traffico" if is_just else "",
                    },
                )
                tardiness_count += 1

        self.stdout.write(f"  ✓ {tardiness_count} ritardi Einstein")

        # --- Homework ---
        hw_descriptions = [
            "Esercizi pag. 124 n. 1–5",
            "Studio del capitolo 7",
            "Traduzione del brano",
            "Risolvi i problemi assegnati in classe",
            "Prepara una sintesi di 2 pagine",
            "Ripassa per la verifica",
        ]
        hw_count = 0

        for tcs_key, lesson_list in lessons_by_tcs.items():
            tcs_obj = tcs_map[tcs_key]
            if len(lesson_list) < 4:
                continue
            for lesson in random.sample(lesson_list, 4):
                due = lesson.date + timedelta(days=random.randint(3, 10))
                _, created = Homework.objects.get_or_create(
                    teacher_class_subject=tcs_obj,
                    lesson=lesson,
                    defaults={
                        "assigned_date": lesson.date,
                        "due_date": due,
                        "description": random.choice(hw_descriptions),
                    },
                )
                if created:
                    hw_count += 1

        self.stdout.write(f"  ✓ {hw_count} compiti Einstein")

        # --- Notes ---
        # Each entry: (enrollment, teacher_assignment, class_name, is_disciplinary, text)
        note_specs = [
            (e5[0], asn["rossi"],   "5IE", True,
             "Comportamento scorretto durante la spiegazione"),
            (e5[1], asn["bianchi"], "5IE", False,
             "Studente distratto e poco partecipe"),
            (e5[2], asn["verde"],   "5IE", True,
             "Uso del cellulare non autorizzato"),
            (e4[0], asn["rossi"],   "4IE", False,
             "Partecipazione attiva e costruttiva"),
            (e4[1], asn["bianchi"], "4IE", True,
             "Linguaggio inappropriato rivolto al professore"),
            (e5[3], asn["verde"],   "5IE", False,
             "Assenza ripetuta al laboratorio di scienze"),
        ]
        note_count = 0

        for enr, ta, cls_name, is_disc, desc in note_specs:
            # Find a lesson taught by this teacher's assignment in the right class
            ta_lessons = [
                l
                for (d, cn), ls in lessons_by_date_class.items()
                if cn == cls_name
                for l in ls
                if l.teacher_class_subject.assignment_id == ta.id
            ]
            if not ta_lessons:
                continue
            lesson = random.choice(ta_lessons)
            _, created = StudentNote.objects.get_or_create(
                student_enrollment=enr,
                teacher_assignment=ta,
                lesson=lesson,
                defaults={
                    "date": lesson.date,
                    "description": desc,
                    "is_disciplinary": is_disc,
                },
            )
            if created:
                note_count += 1

        self.stdout.write(f"  ✓ {note_count} note Einstein")

    # ------------------------------------------------------------------
    # Marconi — dati minimali (solo per test multi-tenant)
    # ------------------------------------------------------------------

    def _create_marconi(self, perm_map):
        P = Permission

        tenant, _ = Tenant.objects.get_or_create(
            slug="itis-marconi",
            defaults={"name": "ITIS Guglielmo Marconi"},
        )

        subj_info, _ = Subject.objects.get_or_create(tenant=tenant, name="Informatica")
        subj_sis,  _ = Subject.objects.get_or_create(tenant=tenant, name="Sistemi e Reti")
        subj_mat,  _ = Subject.objects.get_or_create(tenant=tenant, name="Matematica")

        cls_3a, _ = SchoolClass.objects.get_or_create(
            tenant=tenant, name="3A", school_year=SCHOOL_YEAR,
        )

        # admin
        admin_u = self._user("admin.marconi", "Sergio", "Moretti", 1965)
        role, _ = UserRole.objects.get_or_create(
            user=admin_u, tenant=tenant, role=UserRole.ROLE_ADMIN,
            defaults={"is_active": True},
        )
        admin_profile, _ = AdminProfile.objects.get_or_create(role=role)
        for codename in [
            P.MANAGE_CLASSES, P.MANAGE_SUBJECTS, P.MANAGE_ENROLLMENTS,
            P.MANAGE_ASSIGNMENTS, P.MANAGE_ROLES, P.VIEW_USER_INFO,
        ]:
            AdminPermission.objects.get_or_create(
                admin_profile=admin_profile, permission=perm_map[codename],
            )

        # teacher
        gallo_u = self._user("prof.gallo", "Fabio", "Gallo", 1980)
        role_t, _ = UserRole.objects.get_or_create(
            user=gallo_u, tenant=tenant, role=UserRole.ROLE_TEACHER,
            defaults={"is_active": True},
        )
        profile_t, _ = TeacherProfile.objects.get_or_create(role=role_t)
        ta, _ = TeacherAssignment.objects.get_or_create(
            teacher=profile_t, date_start=YEAR_START,
            defaults={"date_end": None},
        )
        tcs_info, _ = TeacherClassSubject.objects.get_or_create(
            assignment=ta, school_class=cls_3a, subject=subj_info,
        )
        tcs_sis, _ = TeacherClassSubject.objects.get_or_create(
            assignment=ta, school_class=cls_3a, subject=subj_sis,
        )

        # students
        enrollments_m = []
        for username, fn, ln, by in [
            ("luca.m",  "Luca",  "Martini",   2009),
            ("sara.m",  "Sara",  "Coppola",   2009),
            ("piero.m", "Piero", "Battaglia", 2009),
        ]:
            u = self._user(username, fn, ln, by)
            role_s, _ = UserRole.objects.get_or_create(
                user=u, tenant=tenant, role=UserRole.ROLE_STUDENT,
                defaults={"is_active": True},
            )
            prof_s, _ = StudentProfile.objects.get_or_create(
                role=role_s, defaults={"enrollment_year": 2025},
            )
            enr, _ = StudentEnrollment.objects.get_or_create(
                student=prof_s, school_class=cls_3a,
                defaults={"date_start": YEAR_START},
            )
            enrollments_m.append(enr)

        # a handful of lessons (last 2 weeks) + grades
        recent_days = [d for d in _school_days() if d >= TODAY - timedelta(days=14)]
        tcs_cycle   = [tcs_info, tcs_sis, tcs_info, tcs_sis]
        lessons_m   = []

        for i, d in enumerate(recent_days[:8]):
            tcs_obj = tcs_cycle[i % len(tcs_cycle)]
            subj    = "Informatica" if tcs_obj is tcs_info else "Sistemi e Reti"
            desc    = random.choice(_LESSON_TOPICS.get(subj, ["Lezione"]))
            l, _ = Lesson.objects.get_or_create(
                teacher_class_subject=tcs_obj, date=d, hour=1,
                defaults={"description": desc},
            )
            lessons_m.append(l)

        for enr in enrollments_m:
            for lesson in lessons_m[:3]:
                Grade.objects.get_or_create(
                    student_enrollment=enr,
                    teacher_class_subject=lesson.teacher_class_subject,
                    lesson=lesson,
                    defaults={
                        "date": lesson.date,
                        "value": Decimal(str(round(random.uniform(5.0, 9.5), 2))),
                        "description": "Verifica pratica",
                    },
                )

        self.stdout.write("  ✓ ITIS Marconi: dati minimali creati")

    # ------------------------------------------------------------------
    # summary
    # ------------------------------------------------------------------

    def _print_summary(self):
        sep = "=" * 64

        def section(title, slug):
            self.stdout.write(f"\n  {title}  (slug: {slug})")
            self.stdout.write(f"  {'Username':25} {'Password':15} Ruolo")
            self.stdout.write(f"  {'-'*60}")

        def row(username, role_label):
            self.stdout.write(f"  {username:25} {'Password123!':15} {role_label}")

        self.stdout.write(f"\n{sep}")
        self.stdout.write("SEED COMPLETATO — CREDENZIALI DI TEST")
        self.stdout.write(sep)

        section("LICEO SCIENTIFICO EINSTEIN", "liceo-einstein")
        row("preside.einstein",    "Admin — Preside")
        row("segreteria.einstein", "Admin — Segreteria")
        row("prof.rossi",          "Insegnante — Matematica, Fisica (5IE + 4IE)")
        row("prof.bianchi",        "Insegnante — Italiano, Storia (5IE + 4IE)")
        row("prof.verde",          "Insegnante — Inglese, Scienze Nat. (5IE + 4IE)")
        row("luca.verdi",          "Studente — 5IE")
        row("marco.ferrari",       "Studente — 5IE")
        row("sofia.ricci",         "Studente — 5IE")
        row("giulia.esposito",     "Studente — 5IE")
        row("antonio.mancini",     "Studente — 5IE")
        row("emma.romano",         "Studente — 4IE")
        row("matteo.colombo",      "Studente — 4IE")
        row("alice.fontana",       "Studente — 4IE")
        row("davide.russo",        "Studente — 4IE")
        row("genitore.verdi",      "Genitore — madre di Luca Verdi")
        row("genitore.ferrari",    "Genitore — padre di Marco Ferrari")
        row("genitore.ricci",      "Genitore — tutore di Sofia Ricci")

        section("ITIS GUGLIELMO MARCONI", "itis-marconi")
        row("admin.marconi", "Admin")
        row("prof.gallo",    "Insegnante — Informatica, Sistemi e Reti (3A)")
        row("luca.m",        "Studente — 3A")
        row("sara.m",        "Studente — 3A")
        row("piero.m",       "Studente — 3A")

        self.stdout.write(f"\n  Endpoint utili:")
        self.stdout.write("  POST /api/auth/login/                    ← JWT nei cookie")
        self.stdout.write("  POST /api/auth/login/token/              ← JWT nel body")
        self.stdout.write("  GET  /api/schools/liceo-einstein/grades/")
        self.stdout.write("  GET  /api/schools/liceo-einstein/lessons/")
        self.stdout.write("  GET  /api/schools/liceo-einstein/absences/")
        self.stdout.write("  GET  /api/schools/itis-marconi/lessons/")
        self.stdout.write(f"{sep}\n")
