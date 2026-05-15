import random
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import transaction

from users.models import (
    User, UserRole, Permission, RolePermission, AdminPermission,
    TeacherProfile, StudentProfile, ParentProfile, AdminProfile,
    ParentStudentRelation
)
from tenants.models import Tenant
from core.models import (
    SchoolClass, Subject, TeacherAssignment, StudentEnrollment, TeacherClassSubject
)

# Nomi fittizi per la generazione random
FIRST_NAMES = [
    "Mario", "Giuseppe", "Luigi", "Giovanni", "Francesco", "Antonio", "Paolo", "Andrea", "Marco", "Roberto", "Alessandro", "Luca", "Stefano", "Matteo", "Davide", "Anna", "Maria", "Giulia", "Laura", "Sara", "Francesca", "Elena", "Chiara", "Silvia", "Valentina", "Martina", "Daniela", "Federica", "Marta", "Alessia"
]
LAST_NAMES = [
    "Rossi", "Russo", "Ferrari", "Esposito", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco", "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano", "Mancini", "Rizzo", "Lombardi", "Moretti", "Barbieri", "Fontana", "Santoro", "Mariani", "Rinaldi", "Caruso", "Ferrara", "Galli", "Martini", "Leone"
]

SCHOOLS = [
    ("Liceo Scientifico Einstein", "einstein"),
    ("Istituto Tecnico Volta", "volta"),
    ("Liceo Classico Dante", "dante"),
    ("Istituto Comprensivo Manzoni", "manzoni"),
    ("Liceo Artistico Picasso", "picasso")
]
CLASSES = ["1A", "1B", "2A", "2B", "3A", "4A", "5A"]
SUBJECTS = ["Matematica", "Italiano", "Inglese", "Storia", "Scienze", "Fisica", "Educazione Fisica"]

class Command(BaseCommand):
    help = 'Popola il database con una mole estesa di dati fittizi per i test.'

    def generate_fiscal_code(self, i):
        return f"FC{i:014d}"

    def handle(self, *args, **kwargs):
        self.stdout.write("Avviando il seed ESTESO del DB (ci vorranno alcuni secondi)...")
        
        # Uso una singola transazione per rendere la scrittura nel DB enormemente più veloce in SQLite
        with transaction.atomic():
            self._seed()
            
        self.stdout.write(self.style.SUCCESS("Seed ESTESO completato con successo!"))
        
    def _seed(self):
        # Cache per una hash unica della password per sveltire enormemente la creazione
        pwd_hash = make_password("password123")

        # 1. Permessi
        self.stdout.write("Creazione Permessi...")
        PERMISSIONS = {
            "grade.create": "Crea voti",
            "grade.read": "Legge voti",
            "grade.update": "Modifica voti",
            "grade.delete": "Elimina voti",
            "homework.create": "Crea compiti",
            "homework.read": "Legge compiti",
            "homework.update": "Modifica compiti",
            "homework.delete": "Elimina compiti",
            "note.create": "Crea note",
            "note.read": "Legge note",
            "note.update": "Modifica note",
            "note.delete": "Elimina note",
            "absence.create": "Registra assenze",
            "absence.read": "Legge assenze",
            "tardiness.create": "Registra ritardi",
            "tardiness.read": "Legge ritardi",
            "tardiness.update_entry_time": "Modifica orario ritardo",
            "class.read": "Legge informazioni classe",
            "class.create": "Crea classe",
            "class.update": "Modifica classe",
            "class.delete": "Elimina classe",
            "enrollment.manage": "Gestisce iscrizioni",
            "assignment.manage": "Gestisce incarichi",
        }
        
        perms = {}
        for codename, desc in PERMISSIONS.items():
            perms[codename], _ = Permission.objects.get_or_create(codename=codename, defaults={"description": desc})

        # 2. Role Permissions
        ROLE_PERMS = {
            UserRole.ROLE_TEACHER: [
                "grade.create", "grade.read", "grade.update", "grade.delete",
                "homework.create", "homework.read", "homework.update", "homework.delete",
                "note.create", "note.read", "note.update", "note.delete",
                "absence.create", "absence.read",
                "tardiness.create", "tardiness.read", "tardiness.update_entry_time",
                "class.read"
            ],
            UserRole.ROLE_STUDENT: [
                "grade.read", "homework.read", "absence.read", "tardiness.read", "class.read"
            ],
            UserRole.ROLE_PARENT: [
                "grade.read", "homework.read", "absence.read", "tardiness.read", "class.read"
            ]
        }
        
        for role_name, codenames in ROLE_PERMS.items():
            for c in codenames:
                RolePermission.objects.get_or_create(role=role_name, permission=perms[c])

        # Permessi specifici per gli Admin Type
        admin_full_perms = list(perms.values())  # admin1: ha tutto
        # admin2: ha tutto TRANNE le azioni di gestione classi (class.create, class.update, class.delete)
        admin2_perms = [p for c, p in perms.items() if c not in ("class.create", "class.update", "class.delete")]

        # Creazione Superuser Globale
        if not User.objects.filter(username="superuser").exists():
            User.objects.create_superuser("superuser", "super@admin.com", "admin123", fiscal_code="SUPER00000000000", birth_date="1980-01-01")

        user_counter = 1

        for school_name, school_slug in SCHOOLS:
            self.stdout.write(f"\\nGenerazione Dati per: {school_name}...")
            tenant, _ = Tenant.objects.get_or_create(name=school_name, slug=school_slug)
            
            # Materie
            subject_objs = []
            for s_name in SUBJECTS:
                obj, _ = Subject.objects.get_or_create(tenant=tenant, name=s_name)
                subject_objs.append(obj)

            # --- ADMIN 1 (Può gestire Classi) ---
            u_admin1 = User.objects.create(
                username=f"admin1_{school_slug}", password=pwd_hash,
                fiscal_code=self.generate_fiscal_code(user_counter),
                birth_date="1970-01-01", first_name="Dirigente", last_name="Amministrativo"
            )
            user_counter += 1
            r_admin1 = UserRole.objects.create(user=u_admin1, tenant=tenant, role=UserRole.ROLE_ADMIN)
            p_admin1 = AdminProfile.objects.create(role=r_admin1)
            for p in admin_full_perms:
                AdminPermission.objects.create(admin_profile=p_admin1, permission=p)

            # --- ADMIN 2 (NON può gestire Classi) ---
            u_admin2 = User.objects.create(
                username=f"admin2_{school_slug}", password=pwd_hash,
                fiscal_code=self.generate_fiscal_code(user_counter),
                birth_date="1975-01-01", first_name="Segretario", last_name="Semplice"
            )
            user_counter += 1
            r_admin2 = UserRole.objects.create(user=u_admin2, tenant=tenant, role=UserRole.ROLE_ADMIN)
            p_admin2 = AdminProfile.objects.create(role=r_admin2)
            for p in admin2_perms:
                AdminPermission.objects.create(admin_profile=p_admin2, permission=p)

            # Insegnanti per questa scuola (es. 10 insegnanti)
            teachers_pool = []
            for _ in range(10):
                u_teach = User.objects.create(
                    username=f"prof_{school_slug}_{user_counter}", password=pwd_hash,
                    fiscal_code=self.generate_fiscal_code(user_counter),
                    birth_date="1985-05-05", 
                    first_name=random.choice(FIRST_NAMES), last_name=random.choice(LAST_NAMES)
                )
                user_counter += 1
                r_teach = UserRole.objects.create(user=u_teach, tenant=tenant, role=UserRole.ROLE_TEACHER)
                p_teach = TeacherProfile.objects.create(role=r_teach)
                assign = TeacherAssignment.objects.create(teacher=p_teach, date_start="2024-09-01")
                teachers_pool.append(assign)

            # Classi per questa scuola
            for class_name in CLASSES:
                s_class, _ = SchoolClass.objects.get_or_create(tenant=tenant, name=class_name, school_year="2024/2025")
                
                # Assegna di modo random materie e docenti a questa classe
                random.shuffle(subject_objs)
                for subj in subject_objs[:3]:  # Assegna 3 materie per ogni classe
                    assigned_teacher = random.choice(teachers_pool)
                    TeacherClassSubject.objects.create(
                        assignment=assigned_teacher, school_class=s_class, subject=subj
                    )

                # Popolazione di 20 Studenti (e 20 Genitori) per questa classe
                for _ in range(20):
                    s_fname = random.choice(FIRST_NAMES)
                    s_lname = random.choice(LAST_NAMES)
                    
                    # Studente
                    u_stud = User.objects.create(
                        username=f"stud_{school_slug}_{user_counter}", password=pwd_hash,
                        fiscal_code=self.generate_fiscal_code(user_counter),
                        birth_date="2010-09-01", 
                        first_name=s_fname, last_name=s_lname
                    )
                    user_counter += 1
                    r_stud = UserRole.objects.create(user=u_stud, tenant=tenant, role=UserRole.ROLE_STUDENT)
                    p_stud = StudentProfile.objects.create(role=r_stud, enrollment_year=2024)
                    StudentEnrollment.objects.create(student=p_stud, school_class=s_class, date_start="2024-09-01")

                    # Genitore (associato allo studente, stesso cognome)
                    p_fname = random.choice(FIRST_NAMES)
                    u_parent = User.objects.create(
                        username=f"gen_{school_slug}_{user_counter}", password=pwd_hash,
                        fiscal_code=self.generate_fiscal_code(user_counter),
                        birth_date="1970-04-04", 
                        first_name=p_fname, last_name=s_lname
                    )
                    user_counter += 1
                    r_parent = UserRole.objects.create(user=u_parent, tenant=tenant, role=UserRole.ROLE_PARENT)
                    ParentProfile.objects.create(role=r_parent)
                    ParentStudentRelation.objects.create(
                        parent=r_parent, student=r_stud, relation_type=random.choice(["mother", "father"])
                    )

        self.stdout.write(self.style.WARNING(
            "Tutti gli utenti standard creati (admin, prof, stud, gen) hanno la password: password123\\n"
            "Utente assoluto Django (Superuser): superuser / admin123"
        ))
