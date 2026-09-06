# Database structure

## Overview

The **SEIRI – Praktikum** application uses **SQLite** (by default the file
`instance/seiri.db`) managed by **Flask-SQLAlchemy** (version 3.1.1).

The models are defined in `models.py`, where the shared
`db = SQLAlchemy()` instance is initialised in the application factory
(`create_app()` in `run.py`).

> Tables are created / updated with:
> ```
> python run.py
> ```
> which calls `startdb.ensure_schema()` on every start (it creates missing
> tables and columns via `ALTER TABLE`, preserving existing data). You can also
> run it explicitly: `python startdb.py`.

## Model: `Status`

Represents an **application status** that can be assigned to companies. Maps to
the table `status`.

| Column | Type         | Constraints     | Description           |
|--------|--------------|-----------------|-----------------------|
| `id`   | `Integer`    | `PRIMARY KEY`   | Status identifier     |
| `name` | `String(80)` | `NOT NULL`, UNIQUE | Status name       |

Related records: a `Status` can be used by many `Company` records (one-to-many).

## Model: `Company`

Represents a **company offering a practical training (Praktikum) position**.
Maps to the table `company`.

### Columns

| Column         | Type          | Constraints             | Description                              |
|----------------|---------------|-------------------------|------------------------------------------|
| `id`           | `Integer`     | `PRIMARY KEY`, AUTOINC  | Company identifier                        |
| `name`         | `String(120)` | `NOT NULL`              | Company name (required)                   |
| `address`      | `String(200)` | –                       | Address line 1                            |
| `address2`     | `String(200)` | –                       | PLZ (postal code)                            |
| `city`         | `String(120)` | –                       | City / postcode                           |
| `email`        | `String(120)` | –                       | Company e-mail                            |
| `phone`        | `String(40)`  | –                       | Phone number                              |
| `description`  | `Text`        | –                       | Company / offer description               |
| `website`      | `String(255)` | –                       | Website URL                               |
| `cover_letter` | `Text`        | –                       | Cover letter (Anschreiben) text           |
| `status_id`    | `Integer`     | FK → `status.id`        | Assigned status (optional)                |
| `recruitment`  | `String(20)`  | –                       | Recruitment state (sucht / sucht nicht / unbekannt) |
| `updated_at`   | `DateTime`    | –                       | Last-change timestamp (auto)              |

### Recruitment states

`recruitment` stores one of the codes defined in `RECRUITMENT_LABELS`:
`looking` (sucht), `not_looking` (sucht nicht), `unknown` (unbekannt). The
displayed label is available via the `recruitment_label` property. The default
for new companies is `unknown`.

### Notes

- `name` is required; validation happens in the application layer
  (`routes.py`, `new_company` / `edit_company`).
- `status_id` is optional — a company may be saved without a status and assigned
  one later from the detail page.
- `updated_at` is set automatically on insert and on every update (including a
  status change); it backs the „Letzte Änderung“ column and sorting.
- `job_links` is a one-to-many relationship to `JobLink`; links are removed
  automatically when the company is deleted.

### SQL equivalent (SQLite)

```sql
CREATE TABLE company (
    id          INTEGER NOT NULL,
    name        VARCHAR(120) NOT NULL,
    address     VARCHAR(200),
    address2    VARCHAR(200),
    city        VARCHAR(120),
    email       VARCHAR(120),
    phone       VARCHAR(40),
    description TEXT,
    website     VARCHAR(255),
    cover_letter TEXT,
    status_id   INTEGER,
    recruitment VARCHAR(20),
    updated_at  DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY(status_id) REFERENCES status (id)
);
```

## Model: `JobLink`

Represents a **link to a specific job offer** for a company. Maps to the
table `job_link`. A company can have many links (one-to-many).

| Column       | Type          | Constraints        | Description               |
|--------------|---------------|--------------------|---------------------------|
| `id`         | `Integer`     | `PRIMARY KEY`      | Link identifier           |
| `company_id` | `Integer`     | FK → `company.id`  | Owning company (required) |
| `url`        | `String(500)` | `NOT NULL`         | The job-offer URL         |

Related records: a `JobLink` belongs to one `Company`
(`Company.job_links`); links are deleted automatically when the company is
deleted (`cascade="all, delete-orphan"`).

### SQL equivalent (SQLite)

```sql
CREATE TABLE job_link (
    id         INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    url        VARCHAR(500) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(company_id) REFERENCES company (id)
);
```

## Model: `JobSite`

Represents a **standalone internship website/portal** (where companies search
for interns). Maps to the table `job_site`. It is **not linked to companies**.

| Column | Type          | Constraints   | Description          |
|--------|---------------|---------------|----------------------|
| `id`   | `Integer`     | `PRIMARY KEY` | Site identifier      |
| `name` | `String(120)` | `NOT NULL`    | Site name (required) |
| `url`  | `String(500)` | `NOT NULL`    | Site URL (required)  |

### SQL equivalent (SQLite)

```sql
CREATE TABLE job_site (
    id   INTEGER NOT NULL,
    name VARCHAR(120) NOT NULL,
    url  VARCHAR(500) NOT NULL,
    PRIMARY KEY (id)
);
```

## Model: `Profile`

Holds a single row with **my personal data**, used in the cover letter header
and signature (PDF). Maps to the table `profile`.

| Column     | Type          | Description                     |
|------------|---------------|---------------------------------|
| `id`       | `Integer`     | Primary key (always `1`)        |
| `full_name`| `String(160)` | Full name                       |
| `address`  | `String(200)` | Street address                  |
| `city`     | `String(120)` | City / postcode                 |
| `email`    | `String(120)` | E-mail                          |
| `phone`    | `String(40)`  | Phone                           |
| `position` | `String(200)` | Job title (default: Fachinformatiker – Daten und Prozessanalyse) |

## Model: `Settings`

Holds a single row with **application settings**. Maps to the table `settings`.

| Column              | Type          | Constraints                  | Description                       |
|---------------------|---------------|------------------------------|-----------------------------------|
| `id`                | `Integer`     | `PRIMARY KEY` (always `1`)   | Settings identifier               |
| `password_required` | `Boolean`     | `NOT NULL`, default `False`  | Admin area requires a password    |
| `password_hash`     | `String(255)` | –                            | Hashed admin password (pbkdf2)    |
| `share_enabled`     | `Boolean`     | `NOT NULL`, default `False`  | Shared list enabled               |
| `share_token`       | `String(64)`  | –                            | Secret token for the share link   |

## ORM mapping

| Python (Flask-SQLAlchemy) | SQL / database         |
|---------------------------|------------------------|
| `Status`                  | table `status`         |
| `Company`                 | table `company`        |
| `Profile`                 | table `profile`        |
| `JobLink`                 | table `job_link`       |
| `JobSite`                 | table `job_site`       |
| `Settings`                | table `settings`       |
| `Company.status`          | FK `status_id` → `status.id` |
| `Company.job_links`       | one-to-many → `job_link` (cascade delete) |
| `Company.recruitment_label` | derived from `recruitment` |

## Connection configuration

The database URI is resolved in this order:

1. the `DATABASE_URL` environment variable,
2. the default `sqlite:///instance/seiri.db` (relative to the project folder).

Tests use the in-memory URI: `sqlite://`.
