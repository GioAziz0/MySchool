# Documentazione Tecnica — MySchool 3.5

## Indice

1. [Architettura generale](#1-architettura-generale)
2. [Moduli Django](#2-moduli-django)
3. [Modelli dati](#3-modelli-dati)
4. [Autenticazione e sessioni](#4-autenticazione-e-sessioni)
5. [Sistema di ruoli e permessi](#5-sistema-di-ruoli-e-permessi)
6. [Multi-tenancy](#6-multi-tenancy)
7. [Logica di business dei moduli principali](#7-logica-di-business-dei-moduli-principali)

---

## 1. Architettura generale

MySchool adotta il pattern **MVC** nella declinazione Django (MVT: Model–View–Template) affiancato da un livello **REST API** con Django REST Framework.

```
Client Browser                    Client Mobile / Postman
      │                                     │
      │ Cookie HttpOnly (JWT)               │ Authorization: Bearer <token>
      ▼                                     ▼
┌─────────────────────────────────────────────────────┐
│                   Django Application                │
│                                                     │
│  ┌──────────────┐      ┌───────────────────────┐   │
│  │  Web Views   │      │      REST API          │   │
│  │  (Template)  │      │  (DRF ViewSet/APIView) │   │
│  └──────┬───────┘      └──────────┬────────────┘   │
│         │                         │                 │
│         └──────────┬──────────────┘                 │
│                    ▼                                │
│          ┌──────────────────┐                       │
│          │  Middleware stack │                       │
│          │  TenantMiddleware│ ← risolve request.tenant│
│          └──────────────────┘                       │
│                    ▼                                │
│          ┌──────────────────┐                       │
│          │   Models / ORM   │                       │
│          └──────────────────┘                       │
│                    ▼                                │
│              SQLite / DB                            │
└─────────────────────────────────────────────────────┘
```

### Principi architetturali chiave

- **URL-based multi-tenancy**: ogni richiesta alle API porta lo slug della scuola nel path (`/api/schools/<school_slug>/`). Il `TenantMiddleware` risolve lo slug nel modello `Tenant` corrispondente e lo inietta in `request.tenant`.
- **Autenticazione duale**: `CookieJWTAuthentication` legge il token prima dal cookie `access_token`, poi dall'header `Authorization: Bearer`. Entrambi i flussi condividono la stessa logica di validazione.
- **Permessi a tre livelli**: (1) autenticazione, (2) appartenenza attiva al tenant, (3) verifica del permesso per ruolo o admin, (4) verifica dello scope sull'oggetto specifico.
- **Tracciabilità tramite Lesson**: ogni azione sul registro (voto, assenza, compito, nota) deve essere collegata a una `Lesson` specifica, garantendo la riconducibilità all'ora in cui l'evento è avvenuto.

---

## 2. Moduli Django

### `tenants`

Gestisce il concetto di tenant (istituto scolastico). Contiene:
- Il modello `Tenant`
- Il middleware `TenantMiddleware` che risolve `request.tenant` dalla URL

### `users`

Gestisce utenti, ruoli, profili e permessi. Contiene:
- Modello utente custom (`User` estende `AbstractUser`)
- Il sistema di ruoli (`UserRole`, profili per ruolo)
- Il catalogo dei permessi (`Permission`, `RolePermission`, `AdminPermission`)
- Le API di autenticazione (login, refresh, logout) in `users/api/`
- Le web view per login, selezione scuola e ruolo in `users/web_views.py`
- Le classi di permesso DRF custom in `users/api/permissions.py`
- L'autenticazione JWT con cookie in `users/api/authentication.py`

### `core`

Contiene tutta la logica del registro scolastico. Contiene:
- I modelli principali: `SchoolClass`, `Subject`, `StudentEnrollment`, `TeacherAssignment`, `TeacherClassSubject`, `Lesson`, `Grade`, `StudentNote`, `Homework`, `Absence`, `Tardiness`
- I ViewSet REST in `core/api/views.py`
- I serializer in `core/api/serializers.py`
- Le dashboard web per ruolo in `core/web_views.py`

---

## 3. Modelli dati

### `tenants.Tenant`

Rappresenta un istituto scolastico.

| Campo        | Tipo                | Vincoli               | Note                          |
|--------------|---------------------|-----------------------|-------------------------------|
| `id`         | BigAutoField        | PK                    |                               |
| `name`       | CharField(200)      | NOT NULL              | Es: "Liceo Scientifico Einstein" |
| `slug`       | SlugField(100)      | UNIQUE, NOT NULL      | Es: "liceo-einstein"          |
| `created_at` | DateTimeField       | auto_now_add          |                               |

---

### `users.User`

Estende `django.contrib.auth.models.AbstractUser`. Aggiunge:

| Campo         | Tipo            | Vincoli               | Note                      |
|---------------|-----------------|-----------------------|---------------------------|
| `fiscal_code` | CharField(16)   | UNIQUE, NOT NULL      | Codice fiscale            |
| `birth_date`  | DateField       | NOT NULL              | Usato per maggiore età    |
| `phone`       | CharField(20)   | blank, null           | Numero di telefono        |

Eredita da `AbstractUser`: `username`, `password`, `first_name`, `last_name`, `email`, `is_active`, `is_staff`, `date_joined`, ecc.

---

### `users.UserRole`

Tabella ponte: collega un `User` a un `Tenant` con un ruolo specifico.

| Campo        | Tipo                | Vincoli                        | Note                             |
|--------------|---------------------|--------------------------------|----------------------------------|
| `id`         | BigAutoField        | PK                             |                                  |
| `user`       | FK → User           | CASCADE                        |                                  |
| `tenant`     | FK → Tenant         | CASCADE                        |                                  |
| `role`       | CharField(20)       | choices: teacher/student/parent/admin |                         |
| `is_active`  | BooleanField        | default=True                   | Disattiva senza eliminare        |
| `created_at` | DateTimeField       | auto_now_add                   |                                  |

**Vincolo**: `UNIQUE(user, tenant, role)` — un utente non può avere lo stesso ruolo due volte nella stessa scuola.

Un utente può avere più `UserRole` (es: insegna in due scuole, o è sia genitore che admin nella stessa scuola).

---

### Profili per ruolo

Ogni profilo ha una relazione `OneToOne` con `UserRole`.

| Modello           | Campo extra                    | Vincolo `limit_choices_to`   |
|-------------------|--------------------------------|-------------------------------|
| `TeacherProfile`  | —                              | `role='teacher'`              |
| `StudentProfile`  | `enrollment_year` (IntegerField)| `role='student'`             |
| `ParentProfile`   | —                              | `role='parent'`               |
| `AdminProfile`    | —                              | `role='admin'`                |

---

### `users.ParentStudentRelation`

Collega un genitore ai propri figli.

| Campo           | Tipo                | Note                           |
|-----------------|---------------------|--------------------------------|
| `parent`        | FK → UserRole       | `limit_choices_to role='parent'` |
| `student`       | FK → UserRole       | `limit_choices_to role='student'` |
| `relation_type` | CharField(20)       | choices: mother/father/guardian |

**Vincolo**: `UNIQUE(parent, student)`.

---

### `users.Permission`

Catalogo dei permessi disponibili.

| Campo        | Tipo            | Note                                  |
|--------------|-----------------|---------------------------------------|
| `codename`   | CharField(100)  | UNIQUE. Convenzione: `<entità>.<azione>` |
| `description`| CharField(255)  | blank                                 |

**Permessi definiti nel seed** (da `users/management/commands/seed_db.py`):

| Codename                    | Descrizione                      |
|-----------------------------|----------------------------------|
| `grade.create/read/update/delete`   | CRUD voti              |
| `homework.create/read/update/delete`| CRUD compiti           |
| `note.create/read/update/delete`    | CRUD note              |
| `absence.create/read`               | Registra/legge assenze |
| `tardiness.create/read/update_entry_time` | Ritardi          |
| `class.read/create/update/delete`   | Gestione classi        |
| `enrollment.manage`                 | Gestisce iscrizioni    |
| `assignment.manage`                 | Gestisce incarichi     |

---

### `users.RolePermission`

Associa un ruolo generico a un permesso (tutti gli utenti con quel ruolo lo possiedono).

| Campo        | Tipo         | Note                           |
|--------------|--------------|--------------------------------|
| `role`       | CharField(20)| choices: teacher/student/parent/admin |
| `permission` | FK → Permission | CASCADE                    |

**Vincolo**: `UNIQUE(role, permission)`.

---

### `users.AdminPermission`

Permesso granulare per singolo admin (gli admin non hanno permessi di default).

| Campo          | Tipo                | Note     |
|----------------|---------------------|----------|
| `admin_profile`| FK → AdminProfile   | CASCADE  |
| `permission`   | FK → Permission     | CASCADE  |

**Vincolo**: `UNIQUE(admin_profile, permission)`.

---

### `core.SchoolClass`

Classe scolastica appartenente a un tenant e a un anno scolastico.

| Campo         | Tipo           | Note                              |
|---------------|----------------|-----------------------------------|
| `tenant`      | FK → Tenant    | CASCADE                           |
| `name`        | CharField(50)  | Es: "5IE", "3A"                   |
| `school_year` | CharField(9)   | Formato "AAAA/AAAA". Es: 2024/2025|

**Vincolo**: `UNIQUE(tenant, name, school_year)`.

---

### `core.Subject`

Materia scolastica appartenente a un tenant.

| Campo         | Tipo           | Note                     |
|---------------|----------------|--------------------------|
| `tenant`      | FK → Tenant    | CASCADE                  |
| `name`        | CharField(100) | Es: "Matematica"         |
| `description` | TextField      | blank                    |

**Vincolo**: `UNIQUE(tenant, name)`.

---

### `core.StudentEnrollment`

Iscrizione di uno studente a una classe per un periodo.

| Campo          | Tipo                   | Note                              |
|----------------|------------------------|-----------------------------------|
| `student`      | FK → StudentProfile    | CASCADE                           |
| `school_class` | FK → SchoolClass       | CASCADE                           |
| `date_start`   | DateField              |                                   |
| `date_end`     | DateField              | null/blank — None se attiva       |

Ogni cambio di classe o anno scolastico produce una nuova iscrizione, preservando lo storico.

---

### `core.TeacherAssignment`

Incarico di un insegnante per un periodo scolastico.

| Campo        | Tipo                  | Note                       |
|--------------|-----------------------|----------------------------|
| `teacher`    | FK → TeacherProfile   | CASCADE                    |
| `date_start` | DateField             |                            |
| `date_end`   | DateField             | null/blank se attivo       |

---

### `core.TeacherClassSubject`

Associa un incarico insegnante a una specifica classe e materia.

| Campo          | Tipo                    | Note     |
|----------------|-------------------------|----------|
| `assignment`   | FK → TeacherAssignment  | CASCADE  |
| `school_class` | FK → SchoolClass        | CASCADE  |
| `subject`      | FK → Subject            | CASCADE  |

**Vincolo**: `UNIQUE(assignment, school_class, subject)`.

---

### `core.Lesson`

Firma di un'ora di lezione. È il punto di riferimento per tutte le azioni del registro.

| Campo                  | Tipo                       | Note                           |
|------------------------|----------------------------|--------------------------------|
| `teacher_class_subject`| FK → TeacherClassSubject   | CASCADE                        |
| `date`                 | DateField                  |                                |
| `hour`                 | PositiveSmallIntegerField  | validators: 1–12               |
| `description`          | TextField                  | Argomenti trattati, blank      |

**Vincolo**: `UNIQUE(teacher_class_subject, date, hour)`.

---

### `core.Grade`

Voto assegnato a uno studente.

| Campo                  | Tipo                       | Note                           |
|------------------------|----------------------------|--------------------------------|
| `student_enrollment`   | FK → StudentEnrollment     | CASCADE                        |
| `teacher_class_subject`| FK → TeacherClassSubject   | CASCADE                        |
| `lesson`               | FK → Lesson                | **PROTECT** (no cancellazione) |
| `date`                 | DateField                  |                                |
| `value`                | DecimalField(4,2)          | validators: 1.00–10.00         |
| `description`          | TextField                  | blank                          |

---

### `core.StudentNote`

Nota scritta da un insegnante su uno studente (informativa o disciplinare).

| Campo                | Tipo                    | Note                           |
|----------------------|-------------------------|--------------------------------|
| `student_enrollment` | FK → StudentEnrollment  | CASCADE                        |
| `teacher_assignment` | FK → TeacherAssignment  | CASCADE                        |
| `lesson`             | FK → Lesson             | **PROTECT**                    |
| `date`               | DateField               |                                |
| `description`        | TextField               |                                |
| `is_disciplinary`    | BooleanField            | default=False                  |

---

### `core.Homework`

Compito assegnato da un insegnante a una classe.

| Campo                  | Tipo                       | Note                      |
|------------------------|----------------------------|---------------------------|
| `teacher_class_subject`| FK → TeacherClassSubject   | CASCADE                   |
| `lesson`               | FK → Lesson                | **PROTECT**               |
| `assigned_date`        | DateField                  |                           |
| `due_date`             | DateField                  | Data di consegna          |
| `description`          | TextField                  |                           |

---

### `core.Absence`

Assenza giornaliera di uno studente.

| Campo                | Tipo                    | Note                           |
|----------------------|-------------------------|--------------------------------|
| `student_enrollment` | FK → StudentEnrollment  | CASCADE                        |
| `teacher_assignment` | FK → TeacherAssignment  | CASCADE                        |
| `lesson`             | FK → Lesson             | **PROTECT**                    |
| `date`               | DateField               |                                |
| `is_justified`       | BooleanField            | default=False, read-only via API |
| `justification`      | TextField               | blank, scrivibile solo via `justify` |

**Vincolo**: `UNIQUE(student_enrollment, date)` — un solo record per studente per giorno.
**Nota**: PUT/PATCH/DELETE disabilitati; la giustifica avviene tramite action `POST .../justify/`.

---

### `core.Tardiness`

Ritardo di uno studente.

| Campo                | Tipo                    | Note                               |
|----------------------|-------------------------|------------------------------------|
| `student_enrollment` | FK → StudentEnrollment  | CASCADE                            |
| `teacher_assignment` | FK → TeacherAssignment  | CASCADE                            |
| `lesson`             | FK → Lesson             | **PROTECT**                        |
| `date`               | DateField               |                                    |
| `entry_time`         | TimeField               | Ora di ingresso                    |
| `needs_justification`| BooleanField            | default=True (es: oltre 20 min)    |
| `is_justified`       | BooleanField            | default=False, read-only via API   |
| `justification`      | TextField               | blank, scrivibile solo via `justify` |

**Nota**: PUT e DELETE disabilitati; PATCH limitato al solo campo `entry_time` (via `TardinessUpdateEntryTimeSerializer`).

---

## 4. Autenticazione e sessioni

### Flusso browser (cookie)

```
Client                          Server
  │                               │
  │  POST /api/auth/login/        │
  │  {username, password}         │
  │ ─────────────────────────────►│
  │                               │  authenticate()
  │                               │  RefreshToken.for_user(user)
  │◄───────────────────────────── │
  │  200 OK + Set-Cookie:         │
  │    access_token  (60 min)     │
  │    refresh_token (7 giorni)   │
  │                               │
  │  GET /api/schools/<slug>/...  │
  │  Cookie: access_token=<jwt>   │
  │ ─────────────────────────────►│
  │                               │  CookieJWTAuthentication.authenticate()
  │                               │  → legge cookie → valida token
  │◄───────────────────────────── │
  │  200 OK + dati                │
```

### Flusso mobile / API (token nel body)

- `POST /api/auth/login/token/` → restituisce `access` e `refresh` nel body JSON
- Il client include `Authorization: Bearer <access_token>` in ogni richiesta
- `CookieJWTAuthentication` prova prima il cookie, poi l'header

### Token refresh

- `POST /api/auth/refresh/` legge il refresh token prima dal cookie, poi dal body
- Con `ROTATE_REFRESH_TOKENS=True`, ogni refresh emette un nuovo refresh token e blacklista il vecchio

### Logout

- `POST /api/auth/logout/` blacklista il refresh token e cancella i cookie
- La blacklist è gestita da `rest_framework_simplejwt.token_blacklist`

### Classe `CookieJWTAuthentication`

Estende `JWTAuthentication` di simplejwt. Ordine di lettura del token:
1. Cookie `access_token`
2. Header `Authorization: Bearer <token>`

### Configurazione JWT (settings.py)

| Parametro                   | Valore         |
|-----------------------------|----------------|
| `ACCESS_TOKEN_LIFETIME`     | 60 minuti      |
| `REFRESH_TOKEN_LIFETIME`    | 7 giorni       |
| `ROTATE_REFRESH_TOKENS`     | True           |
| `BLACKLIST_AFTER_ROTATION`  | True           |
| `JWT_COOKIE_SECURE`         | False (dev) / True (prod) |
| `JWT_COOKIE_SAMESITE`       | Lax            |

---

## 5. Sistema di ruoli e permessi

### Livelli di controllo (applicati in sequenza)

1. **`IsAuthenticated`** — globale in `DEFAULT_PERMISSION_CLASSES`
2. **`IsActiveTenantMember`** — verifica che `request.tenant` esista e che l'utente abbia almeno un ruolo attivo in quel tenant
3. **`HasRolePermission(codename)`** — factory che genera una classe permesso DRF; controlla se almeno uno dei ruoli attivi dell'utente nel tenant possiede il permesso con quel codename
4. **`HasObjectScope`** — object-level permission; verifica che l'utente abbia scope sull'oggetto specifico

### Logica di scope per tipo di oggetto

| Tipo oggetto         | Teacher                          | Student               | Parent                       | Admin   |
|----------------------|----------------------------------|-----------------------|------------------------------|---------|
| `SchoolClass`        | proprie classi (via TCS)         | propria classe attiva | classi dei figli             | illimitato |
| `StudentEnrollment`  | studenti nelle proprie classi    | propria iscrizione    | iscrizioni dei figli         | illimitato |
| `Grade`              | propria classe **e** materia     | propri voti           | voti dei figli               | illimitato |
| `Homework`           | propria classe e materia         | propria classe attiva | classi dei figli             | illimitato |
| `StudentNote`        | derivato dall'iscrizione         | —                     | —                            | illimitato |
| `Absence/Tardiness`  | derivato dall'iscrizione         | propria               | dei figli                    | illimitato |

### Permessi di default per ruolo (da seed)

| Ruolo    | Permessi                                                                          |
|----------|-----------------------------------------------------------------------------------|
| Teacher  | grade.*, homework.*, note.*, absence.create/read, tardiness.create/read/update_entry_time, class.read |
| Student  | grade.read, homework.read, absence.read, tardiness.read, class.read              |
| Parent   | grade.read, homework.read, absence.read, tardiness.read, class.read              |
| Admin    | Nessuno di default — ogni permesso va concesso esplicitamente via AdminPermission |

### `CanJustify`

Permesso speciale per giustificare assenze e ritardi:
- Genitore → sempre autorizzato
- Studente maggiorenne (≥ 18 anni, verificato su `birth_date`) → autorizzato
- Insegnante e admin → non autorizzati

---

## 6. Multi-tenancy

### Meccanismo

Il `TenantMiddleware` estrae lo slug dalla URL:

```
/api/schools/liceo-einstein/grades/
              └──────────────┘
                 school_slug
```

Lo slug viene usato per una query `Tenant.objects.filter(slug=slug).first()` il cui risultato è assegnato a `request.tenant`. Se lo slug non è presente o non corrisponde a nessun tenant, `request.tenant = None` e tutte le permission class rifiutano la richiesta.

### Isolamento dati

Ogni ViewSet filtra il queryset sul tenant corrente:
```python
SchoolClass.objects.filter(tenant=request.tenant)
Grade.objects.filter(student_enrollment__school_class__tenant=request.tenant)
```

Questo garantisce che un utente autenticato in un tenant non possa mai accedere ai dati di un altro tenant, anche se ne fosse membro.

### Doppio seed

Sono presenti due comandi `seed_db`:
- `core/management/commands/seed_db.py` — seed realistico con due scuole (Liceo Einstein e ITIS Marconi), utenti nominali, orario settimanale completo, voti, assenze, ritardi, note e compiti
- `users/management/commands/seed_db.py` — seed esteso con 5 scuole generate casualmente, 10 insegnanti e 20 studenti per classe

---

## 7. Logica di business dei moduli principali

### Firma lezione (Lesson)

Un insegnante "firma un'ora" creando un record `Lesson` collegato al suo `TeacherClassSubject`. La lezione è obbligatoria come riferimento per ogni azione registrata in quell'ora (voti, assenze, note, compiti). Il vincolo `on_delete=PROTECT` su `lesson` nei modelli correlati impedisce la cancellazione di una lezione finché esistono record ad essa collegati.

### Assenze

- Un solo record `Absence` per studente per giorno (`UNIQUE(student_enrollment, date)`)
- PUT/PATCH/DELETE sono disabilitati a livello HTTP (`http_method_names = ["get", "post", "head", "options"]`)
- La giustifica avviene tramite action dedicata `POST /absences/<pk>/justify/` accessibile solo a `CanJustify` + `HasObjectScope`

### Ritardi

- PATCH è permesso solo per correggere `entry_time` (serializer `TardinessUpdateEntryTimeSerializer`)
- La giustifica segue lo stesso meccanismo delle assenze

### Voti

- Lo scope dell'insegnante su `Grade` richiede la corrispondenza sia della classe che della materia (via `TeacherClassSubject`): un insegnante di Matematica non può vedere i voti di Italiano nella stessa classe

### Compiti (Homework)

- Il modello `Homework` è implementato a livello di API REST (CRUD completo)
- Non esiste un sistema di consegna digitale, feedback o gestione allegati — il modello registra solo descrizione e date
