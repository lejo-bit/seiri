# seiri

A Flask application **SEIRI – Praktikum** for tracking internship applications
(Fachinformatiker – Daten und Prozessanalyse). The whole workflow of sending
applications is supported:

- every company has a **status** (manage them in the „Status“ panel),
- a **„Suche?“ / recruitment** field (sucht / sucht nicht / unbekannt),
- a **website** and a stored **cover letter** (Anschreiben, text in the DB),
- a **„Mein Profil“** page with your personal data,
- a sortable list (by name / status / last change),
- a **„PDF generieren“** button — a clean A4 cover letter with the company data,
  your data and the current date.

The interface is styled with the **Bulma** CSS framework (dark theme). The UI
text is in German.

## Run

In the project directory, using the `.venv` virtual environment:

```bash
# (optional) create / update the database schema
.venv/bin/python startdb.py

# start the development server
.venv/bin/python run.py
```

On every start, `run.py` checks the existing database and updates its schema
(creates missing tables and columns — without deleting any data).

The app will be available at: **http://127.0.0.1:5001**

> Note: the default port is **5001**, because on macOS port 5000 is taken by the
> system ControlCenter process (AirPlay) and cannot be used. Port and host can
> be changed via environment variables:
>
> ```bash
> PORT=8080 HOST=127.0.0.1 .venv/bin/python run.py
> ```

## Structure

- `models.py` — database models (`Status`, `Company`, `Profile`) — see `docs/db_structure.md`
- `routes.py` — application routes
- `run.py` — application factory + server start
- `startdb.py` — database creation / automatic schema update
- `templates/` — HTML templates (Bulma)
- `static/css/app.css` — theme (dark, professional)
- `static/fonts/` — fonts used for PDF generation (Arial regular + bold)
- `docs/db_structure.md` — database structure documentation
