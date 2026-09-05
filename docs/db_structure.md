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
| `address2`     | `String(200)` | –                       | Address line 2                            |
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

## ORM mapping

| Python (Flask-SQLAlchemy) | SQL / database         |
|---------------------------|------------------------|
| `Status`                  | table `status`         |
| `Company`                 | table `company`        |
| `Profile`                 | table `profile`        |
| `Company.status`          | FK `status_id` → `status.id` |
| `Company.recruitment_label` | derived from `recruitment` |

## Connection configuration

The database URI is resolved in this order:

1. the `DATABASE_URL` environment variable,
2. the default `sqlite:///instance/seiri.db` (relative to the project folder).

Tests use the in-memory URI: `sqlite://`.
