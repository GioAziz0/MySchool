# MySchool 3.5

![Stato](https://img.shields.io/badge/stato-in%20sviluppo-yellow)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-6.0-green)
![License](https://img.shields.io/badge/licenza-da%20definire-lightgrey)

> Registro elettronico scolastico multi-tenant con API REST e interfaccia web, progettato per gestire voti, presenze, compiti e comunicazioni in istituti scolastici italiani.

---

## Descrizione

MySchool è un registro elettronico avanzato che consente a più istituti scolastici (tenant) di operare in modo completamente isolato sulla stessa piattaforma. Ogni scuola gestisce le proprie classi, materie, insegnanti e studenti tramite un sistema di ruoli e permessi granulari. Il sistema espone un'API REST protetta da JWT e una web UI basata su template Django.

---

## Stack tecnologico

| Componente           | Tecnologia                                      |
|----------------------|-------------------------------------------------|
| Backend framework    | Django 6.0                                      |
| API REST             | Django REST Framework                           |
| Autenticazione       | djangorestframework-simplejwt (JWT + blacklist) |
| Database (sviluppo)  | SQLite 3                                        |
| Linguaggio           | Python 3.12                                     |
| Template engine      | Django Templates                                |
| Multi-tenancy        | Middleware URL-based (slug nel path)            |

---

## Installazione e avvio

### Prerequisiti

- Python 3.12+
- pip

### Sviluppo

```bash
# 1. Clona il repository
git clone <repo-url>
cd MySchool3.5/MySchool

# 2. Crea e attiva l'ambiente virtuale
python -m venv venv
source venv/bin/activate       # Linux/macOS
venv\Scripts\activate          # Windows

# 3. Installa le dipendenze
pip install django djangorestframework djangorestframework-simplejwt

# 4. Applica le migrazioni
python manage.py migrate

# 5. Popola il database con dati di test
python manage.py seed_db       # seed completo (core/management/commands/)
# oppure
python manage.py seed_db       # seed esteso (users/management/commands/)

# 6. Avvia il server di sviluppo
python manage.py runserver
```

Il server sarà disponibile su `http://127.0.0.1:8000`.


## Funzionalità

### Implementate ✅

- **Autenticazione JWT** — login con cookie HttpOnly (browser) e token nel body (mobile/API)
- **Multi-tenancy** — isolamento completo tra scuole tramite slug nell'URL
- **Gestione ruoli** — Teacher, Student, Parent, Admin con permessi granulari per ruolo e per singolo admin
- **Classi e materie** — CRUD completo con scope per tenant
- **Iscrizioni studenti** — storico completo dei cambi classe/anno
- **Incarichi insegnanti** — assegnazione classe+materia per periodo
- **Registro lezioni** — firma ora (Lesson), argomenti trattati
- **Voti** — CRUD con scope per materia e classe
- **Compiti** — assegnazione con data di consegna
- **Assenze** — registrazione giornaliera, giustifica (genitore o studente maggiorenne)
- **Ritardi** — registrazione con ora ingresso, giustifica, correzione orario (solo insegnante)
- **Note disciplinari** — note informative e disciplinari su studenti
- **Dashboard web** — viste HTML per insegnante, studente, genitore, admin

### Roadmap / In sviluppo 🚧 / ❌

- **Circolari e documenti** — compilazione, firma e presa visione digitale — non implementato
- **Sistema compiti avanzato** — stile Google Classroom (consegna digitale, feedback) — non implementato
- **Notifiche** — push/email per eventi registro — non implementato
- **Gestione orario scolastico** — UI per la configurazione del calendario — non implementato
- **Report e statistiche** — dashboard analitiche per admin e docenti — non implementato

---

## Documentazione

La cartella `docs/` contiene i documenti di progetto:

- [DOCUMENTAZIONE](docs/DOCUMENTAZIONE.md)
- [MANUALE UTENTE](docs/MANUALE_UTENTE.md)
- [DIAGRAMMA DEI CASI D'USO](docs/CASI_D'USO.pdf)
- [DIAGRAMMA DELLE CLASSI](docs/DIAGRAMMA_DELLE_CLASSI.pdf)

---

## Struttura del progetto

```
MySchool3.5/
├── docs/                          # Documentazione (questa cartella)
└── MySchool/                      # Root del progetto Django
    ├── manage.py
    ├── db.sqlite3
    ├── reset_db.sh
    ├── MySchool/                  # Configurazione progetto
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    ├── tenants/                   # App multi-tenancy
    │   ├── models.py              # Tenant
    │   ├── middleware.py          # TenantMiddleware
    │   └── migrations/
    ├── users/                     # App utenti e autenticazione
    │   ├── models.py              # User, UserRole, profili, permessi
    │   ├── web_views.py           # Login, selezione scuola/ruolo, logout
    │   ├── web_urls.py
    │   ├── api/
    │   │   ├── views.py           # LoginView, RefreshView, LogoutView
    │   │   ├── urls.py
    │   │   ├── authentication.py  # CookieJWTAuthentication
    │   │   └── permissions.py     # IsActiveTenantMember, HasRolePermission, ecc.
    │   ├── management/commands/
    │   │   └── seed_db.py         
    │   └── migrations/
    └── core/                      # App registro scolastico
        ├── models.py              # SchoolClass, Lesson, Grade, Absence, ecc.
        ├── web_views.py           # Dashboard per ruolo
        ├── web_urls.py
        ├── api/
        │   ├── views.py           # ViewSet per tutte le entità
        │   ├── urls.py
        │   └── serializers.py
        ├── management/commands/
        │   └── seed_db.py         # Seed realistico (Einstein + Marconi)
        ├── templates/core/        # HTML dashboard
        └── migrations/
```
