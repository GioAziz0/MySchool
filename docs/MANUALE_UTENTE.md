# Manuale degli Endpoint e delle Funzionalità — MySchool 3.5

## Indice

1. [Convenzioni](#1-convenzioni)
2. [Autenticazione](#2-autenticazione)
3. [Classi scolastiche](#3-classi-scolastiche)
4. [Iscrizioni studenti](#4-iscrizioni-studenti)
5. [Incarichi insegnanti](#5-incarichi-insegnanti)
6. [Assegnazioni insegnante-classe-materia](#6-assegnazioni-insegnante-classe-materia)
7. [Lezioni](#7-lezioni)
8. [Voti](#8-voti)
9. [Compiti](#9-compiti)
10. [Note disciplinari](#10-note-disciplinari)
11. [Assenze](#11-assenze)
12. [Ritardi](#12-ritardi)
13. [Viste Web](#13-viste-web)
14. [Funzionalità non ancora implementate](#14-funzionalità-non-ancora-implementate)

---

## 1. Convenzioni

### URL base

- **API REST**: `http://<host>/api/`
- **Web (browser)**: `http://<host>/`

### Prefisso API per le risorse scolastiche

Tutte le risorse del registro si trovano sotto:

```
/api/schools/<school_slug>/
```

Dove `<school_slug>` è l'identificatore URL della scuola (es: `liceo-einstein`).

### Autenticazione

Le API richiedono un JWT valido, fornito in uno dei due modi:
- **Cookie**: `access_token=<jwt>` (impostato automaticamente dal login via browser)
- **Header**: `Authorization: Bearer <jwt>` (per client mobile e test API)

### Formato risposte

Tutte le risposte sono in formato JSON. Gli errori seguono lo schema DRF standard:

```json
{ "detail": "Messaggio di errore." }
```

oppure con errori per campo:

```json
{ "campo": ["Messaggio di errore."] }
```

### Paginazione

Le liste sono paginate con `PAGE_SIZE = 50`. La risposta include:

```json
{
  "count": 100,
  "next": "http://.../api/schools/.../grades/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## 2. Autenticazione

### `POST /api/auth/login/`

Login con restituzione dei token JWT nei cookie HttpOnly. Destinato ai client browser.

**Ruoli autorizzati**: tutti (endpoint pubblico)

**Body**:

| Campo      | Tipo   | Obbligatorio | Note                  |
|------------|--------|--------------|-----------------------|
| `username` | string | Sì           |                       |
| `password` | string | Sì           |                       |

**Risposta 200 OK**:

```json
{
  "user": {
    "id": 1,
    "username": "prof.rossi",
    "first_name": "Marco",
    "last_name": "Rossi",
    "email": "prof.rossi@example.com",
    "roles": [
      {
        "school_slug": "liceo-einstein",
        "school_name": "Liceo Scientifico Einstein",
        "role": "teacher"
      }
    ]
  }
}
```

I cookie `access_token` (60 min) e `refresh_token` (7 giorni) vengono impostati automaticamente.

**Risposta 400**: username o password mancanti  
**Risposta 401**: credenziali non valide

---

### `POST /api/auth/login/token/`

Login con restituzione dei token JWT nel body JSON. Destinato a client mobile e API testing.

**Ruoli autorizzati**: tutti (endpoint pubblico)

**Body**: uguale a `/api/auth/login/`

**Risposta 200 OK**:

```json
{
  "access": "<access_token_jwt>",
  "refresh": "<refresh_token_jwt>",
  "user": { ... }
}
```

---

### `POST /api/auth/refresh/`

Rinnova l'access token. Legge il refresh token prima dal cookie, poi dal body.

**Ruoli autorizzati**: tutti (endpoint pubblico)

**Body** (se non si usa il cookie):

| Campo     | Tipo   | Obbligatorio |
|-----------|--------|--------------|
| `refresh` | string | Sì (se no cookie) |

**Risposta 200 OK** (client cookie):

```json
{ "detail": "Token aggiornato." }
```

**Risposta 200 OK** (client mobile):

```json
{ "access": "<nuovo_access_token>" }
```

Con `ROTATE_REFRESH_TOKENS=True`, include anche `"refresh": "<nuovo_refresh_token>"`.

**Risposta 401**: token scaduto o non valido

---

### `POST /api/auth/logout/`

Invalida il refresh token (blacklist) e cancella i cookie JWT.

**Ruoli autorizzati**: utente autenticato

**Body** (se non si usa il cookie):

| Campo     | Tipo   | Obbligatorio |
|-----------|--------|--------------|
| `refresh` | string | No           |

**Risposta 200 OK**:

```json
{ "detail": "Logout effettuato." }
```

---

## 3. Classi scolastiche

Base URL: `/api/schools/<school_slug>/classes/`

### `GET /api/schools/<school_slug>/classes/`

Elenca le classi scolastiche del tenant.

**Permesso**: `class.read` (teacher, student, parent con scope)

**Risposta 200 OK**:

```json
{
  "results": [
    { "id": 1, "name": "5IE", "school_year": "2025/2026", "tenant": 1 },
    { "id": 2, "name": "4IE", "school_year": "2025/2026", "tenant": 1 }
  ]
}
```

---

### `POST /api/schools/<school_slug>/classes/`

Crea una nuova classe scolastica.

**Permesso**: `class.create` (tipicamente admin)

**Body**:

| Campo         | Tipo   | Obbligatorio | Note                        |
|---------------|--------|--------------|-----------------------------|
| `name`        | string | Sì           | Es: "5IE"                   |
| `school_year` | string | Sì           | Formato "AAAA/AAAA"         |

**Risposta 201 Created**: oggetto classe creato

---

### `GET /api/schools/<school_slug>/classes/<pk>/`

Dettaglio di una classe.

**Permesso**: `class.read` + scope sulla classe

---

### `PUT/PATCH /api/schools/<school_slug>/classes/<pk>/`

Aggiorna una classe.

**Permesso**: `class.update` + scope

---

### `DELETE /api/schools/<school_slug>/classes/<pk>/`

Elimina una classe.

**Permesso**: `class.delete` + scope

---

## 4. Iscrizioni studenti

Base URL: `/api/schools/<school_slug>/enrollments/`

Tutte le operazioni CRUD standard (list, create, retrieve, update, destroy).

**Permesso lettura**: `class.read` + scope sull'iscrizione  
**Permesso scrittura**: `enrollment.manage` (tipicamente admin)

**Campi principali**:

| Campo          | Tipo    | Note                        |
|----------------|---------|-----------------------------|
| `id`           | integer |                             |
| `student`      | integer | FK → StudentProfile         |
| `school_class` | integer | FK → SchoolClass            |
| `date_start`   | date    | formato ISO: YYYY-MM-DD     |
| `date_end`     | date    | null se ancora attiva       |
| `student_name` | string  | read-only (calcolato)       |

---

## 5. Incarichi insegnanti

Base URL: `/api/schools/<school_slug>/assignments/`

CRUD standard.

**Permesso lettura**: `class.read`  
**Permesso scrittura**: `assignment.manage` (admin)

**Campi principali**:

| Campo        | Tipo    | Note                    |
|--------------|---------|-------------------------|
| `id`         | integer |                         |
| `teacher`    | integer | FK → TeacherProfile     |
| `date_start` | date    |                         |
| `date_end`   | date    | null se attivo          |

---

## 6. Assegnazioni insegnante-classe-materia

Base URL: `/api/schools/<school_slug>/class-subjects/`

CRUD standard.

**Permesso lettura**: `class.read`  
**Permesso scrittura**: `assignment.manage` (admin)

**Campi principali**:

| Campo          | Tipo    | Note                         |
|----------------|---------|------------------------------|
| `id`           | integer |                              |
| `assignment`   | integer | FK → TeacherAssignment       |
| `school_class` | integer | FK → SchoolClass             |
| `subject`      | integer | FK → Subject                 |
| `subject_name` | string  | read-only (calcolato)        |
| `class_name`   | string  | read-only (calcolato)        |

---

## 7. Lezioni

Base URL: `/api/schools/<school_slug>/lessons/`

**Solo lettura** (read-only ViewSet: list, retrieve).

**Permesso**: `lesson.read`

### `GET /api/schools/<school_slug>/lessons/`

Elenca le lezioni. Supporta filtro per data.

**Query parameters**:

| Parametro | Tipo | Obbligatorio | Note                          |
|-----------|------|--------------|-------------------------------|
| `date`    | date | No           | Formato YYYY-MM-DD. Filtra per giorno specifico |

**Risposta 200 OK**:

```json
{
  "results": [
    {
      "id": 1,
      "teacher_class_subject": 3,
      "date": "2026-05-14",
      "hour": 1,
      "description": "Equazioni differenziali",
      "subject_name": "Matematica",
      "class_name": "5IE"
    }
  ]
}
```

---

### `GET /api/schools/<school_slug>/lessons/<pk>/`

Dettaglio di una lezione.

---

## 8. Voti

Base URL: `/api/schools/<school_slug>/grades/`

CRUD standard (list, create, retrieve, update, destroy).

**Permesso lettura**: `grade.read` + scope  
**Permesso creazione**: `grade.create` + scope (solo insegnante con TCS per quella classe e materia)  
**Permesso modifica**: `grade.update` + scope  
**Permesso cancellazione**: `grade.delete` + scope

### `GET /api/schools/<school_slug>/grades/`

**Risposta 200 OK**:

```json
{
  "results": [
    {
      "id": 10,
      "student_enrollment": 2,
      "teacher_class_subject": 3,
      "lesson": 15,
      "date": "2026-03-10",
      "value": "7.50",
      "description": "Interrogazione orale",
      "student_name": "Luca Verdi",
      "subject_name": "Matematica",
      "class_name": "5IE"
    }
  ]
}
```

### `POST /api/schools/<school_slug>/grades/`

**Body**:

| Campo                    | Tipo    | Obbligatorio | Note               |
|--------------------------|---------|--------------|--------------------|
| `student_enrollment`     | integer | Sì           |                    |
| `teacher_class_subject`  | integer | Sì           |                    |
| `lesson`                 | integer | Sì           |                    |
| `date`                   | date    | Sì           |                    |
| `value`                  | decimal | Sì           | Range: 1.00–10.00  |
| `description`            | string  | No           |                    |

**Risposta 201 Created**: oggetto voto creato

---

## 9. Compiti

Base URL: `/api/schools/<school_slug>/homework/`

CRUD standard.

**Permesso lettura**: `homework.read` + scope  
**Permesso creazione**: `homework.create` + scope (insegnante)  
**Permesso modifica**: `homework.update` + scope  
**Permesso cancellazione**: `homework.delete` + scope

**Campi principali**:

| Campo                   | Tipo    | Obbligatorio | Note                  |
|-------------------------|---------|--------------|-----------------------|
| `id`                    | integer | —            | read-only             |
| `teacher_class_subject` | integer | Sì           | FK                    |
| `lesson`                | integer | Sì           | FK                    |
| `assigned_date`         | date    | Sì           |                       |
| `due_date`              | date    | Sì           | Data di consegna      |
| `description`           | string  | Sì           |                       |
| `subject_name`          | string  | —            | read-only (calcolato) |
| `class_name`            | string  | —            | read-only (calcolato) |

---

## 10. Note disciplinari

Base URL: `/api/schools/<school_slug>/notes/`

CRUD standard. Solo gli insegnanti hanno accesso (studenti e genitori non hanno `note.read`).

**Permesso lettura**: `note.read` + scope  
**Permesso creazione**: `note.create` + scope  
**Permesso modifica**: `note.update` + scope  
**Permesso cancellazione**: `note.delete` + scope

**Campi principali**:

| Campo                | Tipo    | Obbligatorio | Note                    |
|----------------------|---------|--------------|-------------------------|
| `id`                 | integer | —            |                         |
| `student_enrollment` | integer | Sì           |                         |
| `teacher_assignment` | integer | Sì           |                         |
| `lesson`             | integer | Sì           |                         |
| `date`               | date    | Sì           |                         |
| `description`        | string  | Sì           |                         |
| `is_disciplinary`    | boolean | No           | default: false          |

---

## 11. Assenze

Base URL: `/api/schools/<school_slug>/absences/`

**Metodi HTTP disponibili**: GET, POST (PUT/PATCH/DELETE disabilitati)

### `GET /api/schools/<school_slug>/absences/`

**Permesso**: `absence.read` + scope

**Risposta 200 OK**:

```json
{
  "results": [
    {
      "id": 5,
      "student_enrollment": 2,
      "teacher_assignment": 1,
      "lesson": 10,
      "date": "2026-04-15",
      "is_justified": true,
      "justification": "Motivi di salute",
      "student_name": "Luca Verdi",
      "class_name": "5IE"
    }
  ]
}
```

---

### `POST /api/schools/<school_slug>/absences/`

Registra un'assenza.

**Permesso**: `absence.create` (insegnante con scope)

**Body**:

| Campo                | Tipo    | Obbligatorio | Note                              |
|----------------------|---------|--------------|-----------------------------------|
| `student_enrollment` | integer | Sì           |                                   |
| `teacher_assignment` | integer | Sì           |                                   |
| `lesson`             | integer | Sì           |                                   |
| `date`               | date    | Sì           |                                   |

> `is_justified` e `justification` sono **read-only** in questa action.

**Risposta 201 Created**: oggetto assenza  
**Risposta 400**: `UNIQUE(student_enrollment, date)` violato — studente già assente in quel giorno

---

### `POST /api/schools/<school_slug>/absences/<pk>/justify/`

Giustifica un'assenza.

**Permesso**: `CanJustify` (genitore o studente maggiorenne) + `HasObjectScope`

**Body**:

| Campo          | Tipo    | Obbligatorio | Note                   |
|----------------|---------|--------------|------------------------|
| `is_justified` | boolean | Sì           |                        |
| `justification`| string  | No           | Motivazione testuale   |

**Risposta 200 OK**: oggetto assenza aggiornato con `is_justified: true`

---

## 12. Ritardi

Base URL: `/api/schools/<school_slug>/tardinesses/`

**Metodi HTTP disponibili**: GET, POST, PATCH (PUT/DELETE disabilitati)

### `GET /api/schools/<school_slug>/tardinesses/`

**Permesso**: `tardiness.read` + scope

**Risposta 200 OK**:

```json
{
  "results": [
    {
      "id": 3,
      "student_enrollment": 2,
      "teacher_assignment": 1,
      "lesson": 8,
      "date": "2026-03-20",
      "entry_time": "08:25:00",
      "needs_justification": true,
      "is_justified": false,
      "justification": ""
    }
  ]
}
```

---

### `POST /api/schools/<school_slug>/tardinesses/`

Registra un ritardo.

**Permesso**: `tardiness.create` (insegnante)

**Body**:

| Campo                | Tipo    | Obbligatorio | Note                              |
|----------------------|---------|--------------|-----------------------------------|
| `student_enrollment` | integer | Sì           |                                   |
| `teacher_assignment` | integer | Sì           |                                   |
| `lesson`             | integer | Sì           |                                   |
| `date`               | date    | Sì           |                                   |
| `entry_time`         | time    | Sì           | Formato HH:MM:SS                  |
| `needs_justification`| boolean | No           | default: true                     |

---

### `PATCH /api/schools/<school_slug>/tardinesses/<pk>/`

Corregge l'ora di ingresso. Solo il campo `entry_time` è modificabile.

**Permesso**: `tardiness.update_entry_time` (insegnante)

**Body**:

| Campo        | Tipo | Obbligatorio |
|--------------|------|--------------|
| `entry_time` | time | Sì           |

---

### `POST /api/schools/<school_slug>/tardinesses/<pk>/justify/`

Giustifica un ritardo.

**Permesso**: `CanJustify` (genitore o studente maggiorenne) + scope

**Body**: uguale a `absences/<pk>/justify/`

---

## 13. Viste Web

Le seguenti rotte servono interfacce HTML (template Django). Sono accessibili da browser e usano la sessione Django + cookie JWT.

| Metodo | Path                                    | Vista                | Note                                         |
|--------|-----------------------------------------|----------------------|----------------------------------------------|
| GET    | `/login/`                               | `LoginView`          | Form di login                                |
| POST   | `/login/`                               | `LoginView`          | Autentica, imposta cookie JWT, reindirizza   |
| POST   | `/logout/`                              | `LogoutView`         | Blacklist refresh token, cancella cookie     |
| GET    | `/select-school/`                       | `SelectSchoolView`   | Lista scuole e ruoli dell'utente             |
| POST   | `/select-school/`                       | `SelectSchoolView`   | Sceglie la scuola, reindirizza alla dashboard|
| GET    | `/select-role/`                         | `SelectRoleView`     | Selezione ruolo (solo se l'utente ha più ruoli) |
| POST   | `/select-role/`                         | `SelectRoleView`     | Conferma ruolo selezionato                   |
| GET    | `/dashboard/<school_slug>/teacher/`     | `TeacherDashboardView` | Dashboard insegnante                       |
| GET    | `/dashboard/<school_slug>/student/`     | `StudentDashboardView` | Dashboard studente                         |
| GET    | `/dashboard/<school_slug>/parent/`      | `ParentDashboardView`  | Dashboard genitore                         |
| GET    | `/dashboard/<school_slug>/admin/`       | `AdminDashboardView`   | Dashboard amministratore                   |

**Flusso di navigazione web**:

```
/login/
  └─ POST credenziali valide
       └─ /select-school/
            ├─ 1 ruolo → /dashboard/<slug>/<role>/
            └─ n ruoli → /select-role/
                              └─ /dashboard/<slug>/<role>/
```

---

## 14. Funzionalità non ancora implementate

### Circolari e documenti 🚧

Il sistema prevede la gestione di circolari scolastiche con:
- Compilazione di moduli digitali
- Firma digitale da parte degli utenti
- Tracciamento della "presa visione"

Questa funzionalità è descritta come **parzialmente implementata** nel contesto del progetto ma non è presente nel codebase attuale (nessun modello `Circular`, `Document` o simile è definito nei modelli né nelle API).

### Sistema compiti avanzato (stile Google Classroom) ❌

Il modello `Homework` attuale registra solo la descrizione e le date del compito assegnato alla classe. Non è presente:
- Consegna digitale dei compiti da parte degli studenti
- Allegati (file upload)
- Feedback/correzione da parte dell'insegnante
- Stato di consegna per studente
- Notifiche di scadenza

### Notifiche ❌

Nessun sistema di notifiche (push, email, SMS) è implementato.

### Gestione orario scolastico (UI) ❌

Il seed genera un orario fisso hardcoded. Non esiste un'interfaccia o API per la configurazione dinamica dell'orario settimanale.

### Report e statistiche ❌

Non sono presenti endpoint o viste per:
- Media voti per studente/materia/classe
- Riepilogo assenze/ritardi
- Statistiche di condotta
- Export CSV/PDF del registro

### Gestione materie (CRUD API) ❌

Il modello `Subject` esiste, ma non è presente un ViewSet o endpoint REST per il CRUD delle materie. La gestione avviene solo tramite Django Admin.
