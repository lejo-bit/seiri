"""SEIRI application routes — split out for readability."""
import csv
import datetime
import io
import os
import secrets

from fpdf import FPDF
from sqlalchemy.orm import selectinload
from flask import (
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from models import (
    DEFAULT_POSITION,
    RECRUITMENT_DEFAULT,
    RECRUITMENT_LABELS,
    Company,
    JobLink,
    JobSite,
    Profile,
    Settings,
    Status,
    db,
)

FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "fonts")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _fields_from_form():
    """Read and trim the company fields from the form."""
    return {
        "name": request.form.get("name", "").strip(),
        "address": request.form.get("address", "").strip(),
        "address2": request.form.get("address2", "").strip(),
        "city": request.form.get("city", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "description": request.form.get("description", "").strip(),
        "website": request.form.get("website", "").strip(),
        "cover_letter": request.form.get("cover_letter", "").strip(),
        "cover_letter_locked": request.form.get("cover_letter_locked") is not None,
        "status_id": request.form.get("status_id", type=int),
        "recruitment": request.form.get("recruitment", "").strip(),
    }


def _clean_recruitment(value):
    return value if value in RECRUITMENT_LABELS else RECRUITMENT_DEFAULT


def _clean_website(value):
    """Normalise the website URL so only http(s) schemes are stored
    (prevents XSS via javascript:/data: URLs)."""
    value = value.strip()
    if not value:
        return ""
    if value.lower().startswith(("http://", "https://")):
        return value
    return "https://" + value


def _apply_company_form(company, fields):
    """Apply the form fields to the Company object."""
    company.name = fields["name"]
    company.address = fields["address"]
    company.address2 = fields["address2"]
    company.city = fields["city"]
    company.email = fields["email"]
    company.phone = fields["phone"]
    company.description = fields["description"]
    company.website = _clean_website(fields["website"])
    company.cover_letter = fields["cover_letter"]
    company.cover_letter_locked = fields["cover_letter_locked"]
    company.status_id = fields["status_id"]
    company.recruitment = _clean_recruitment(fields["recruitment"])


def _validate_company(fields):
    """Returns an error message, or None when the data is valid."""
    if not fields["name"]:
        return "Das Feld „Name des Unternehmens“ ist erforderlich."
    return None


def _statuses():
    return Status.query.order_by(Status.name.asc()).all()


def _get_profile():
    """Return (creating if needed) the single record of my personal data."""
    profile = db.session.get(Profile, 1)
    if profile is None:
        profile = Profile(id=1, position=DEFAULT_POSITION)
        db.session.add(profile)
        db.session.commit()
    return profile


def _get_settings():
    """Return (creating if needed) the single settings record."""
    settings = db.session.get(Settings, 1)
    if settings is None:
        settings = Settings(id=1)
        db.session.add(settings)
        db.session.commit()
    return settings


def _password_enforced(settings=None):
    st = settings or _get_settings()
    return bool(st.password_required and st.password_hash)


def _is_authed():
    return session.get("admin_ok") is True


def _ordered_companies():
    """All companies ordered by name, with their status and links loaded."""
    return (
        Company.query.options(selectinload(Company.job_links))
        .outerjoin(Status, Company.status_id == Status.id)
        .order_by(Company.name.asc())
        .all()
    )


def _companies_csv():
    """Build a CSV (semicolon-separated, UTF-8 with BOM) of all companies."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        ["Name", "Adresse", "PLZ", "Stadt", "E-Mail", "Telefon", "Website", "Stellenangebote", "Status", "Sucht?"]
    )
    for company in _ordered_companies():
        links = " | ".join(link.url for link in company.job_links)
        writer.writerow(
            [
                company.name or "",
                company.address or "",
                company.address2 or "",
                company.city or "",
                company.email or "",
                company.phone or "",
                company.website or "",
                links,
                company.status.name if company.status else "",
                company.recruitment_label or "",
            ]
        )
    data = "\ufeff" + buf.getvalue()
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="unternehmen.csv"'},
    )


# --------------------------------------------------------------------------- #
# Company
# --------------------------------------------------------------------------- #
def index():
    sort = request.args.get("sort", "updated")
    direction = request.args.get("dir", "desc")
    q = request.args.get("q", "").strip()
    if sort not in ("name", "status", "updated", "recruitment"):
        sort = "updated"
    if direction not in ("asc", "desc"):
        direction = "desc"

    order_cols = {
        "name": Company.name,
        "status": Status.name,
        "updated": Company.updated_at,
        "recruitment": Company.recruitment,
    }
    query = Company.query.outerjoin(Status, Company.status_id == Status.id)
    if q:
        query = query.filter(Company.name.ilike(f"%{q}%"))
    column = order_cols[sort]
    companies = query.order_by(
        column.asc() if direction == "asc" else column.desc()
    ).all()
    return render_template(
        "index.html",
        companies=companies,
        sort=sort,
        direction=direction,
        q=q,
    )


def new_company():
    statuses = _statuses()
    company = Company()
    if request.method == "POST":
        fields = _fields_from_form()
        _apply_company_form(company, fields)
        if not company.cover_letter:
            company.cover_letter = _get_profile().cover_letter_template or ""
        error = _validate_company(fields)
        if error:
            flash(error, "error")
            return render_template("company_form.html", company=company, statuses=statuses)
        db.session.add(company)
        db.session.commit()
        flash(f"Firma „{company.name}“ wurde hinzugefügt.", "success")
        return redirect(url_for("company_detail", company_id=company.id))
    profile = _get_profile()
    return render_template(
        "company_form.html",
        company=None,
        statuses=statuses,
        cover_letter_template=profile.cover_letter_template or "",
    )


def edit_company(company_id):
    company = Company.query.get_or_404(company_id)
    statuses = _statuses()
    if request.method == "POST":
        fields = _fields_from_form()
        _apply_company_form(company, fields)
        error = _validate_company(fields)
        if error:
            flash(error, "error")
            return render_template("company_form.html", company=company, statuses=statuses)
        db.session.commit()
        flash(f"Firma „{company.name}“ wurde aktualisiert.", "success")
        return redirect(url_for("company_detail", company_id=company.id))
    return render_template("company_form.html", company=company, statuses=statuses)


def company_detail(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template("company_detail.html", company=company, statuses=_statuses())


def change_status(company_id):
    """Quickly change the status from the company detail page."""
    company = Company.query.get_or_404(company_id)
    status_id = request.form.get("status_id", type=int)
    status = db.session.get(Status, status_id) if status_id else None
    if status is None:
        flash("Bitte wählen Sie einen gültigen Status.", "error")
        return redirect(url_for("company_detail", company_id=company.id))
    company.status_id = status.id
    db.session.commit()
    flash(f"Status der Firma geändert auf „{status.name}“.", "success")
    return redirect(url_for("company_detail", company_id=company.id))


def delete_company(company_id):
    """Delete a company (POST, from the detail page)."""
    company = Company.query.get_or_404(company_id)
    name = company.name
    db.session.delete(company)
    db.session.commit()
    flash(f"Firma „{name}“ wurde gelöscht.", "success")
    return redirect(url_for("index"))


def add_job_link(company_id):
    """Add a job-offer link to a company."""
    company = Company.query.get_or_404(company_id)
    url = _clean_website(request.form.get("url", ""))
    if not url:
        flash("Bitte eine gültige URL angeben.", "error")
        return redirect(url_for("company_detail", company_id=company.id))
    db.session.add(JobLink(company_id=company.id, url=url))
    db.session.commit()
    flash("Link hinzugefügt.", "success")
    return redirect(url_for("company_detail", company_id=company.id))


def delete_job_link(link_id):
    """Delete a job-offer link."""
    link = db.session.get(JobLink, link_id)
    if link is None:
        abort(404)
    company_id = link.company_id
    db.session.delete(link)
    db.session.commit()
    flash("Link gelöscht.", "success")
    return redirect(url_for("company_detail", company_id=company_id))


def sites():
    """List of internship sites (standalone, not linked to companies)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = _clean_website(request.form.get("url", ""))
        if not name or not url:
            flash("Bitte Name und URL angeben.", "error")
        else:
            db.session.add(JobSite(name=name, url=url))
            db.session.commit()
            flash("Seite hinzugefügt.", "success")
        return redirect(url_for("sites"))

    site_list = JobSite.query.order_by(JobSite.name.asc()).all()
    return render_template("sites.html", sites=site_list)


def delete_site(site_id):
    """Delete an internship site."""
    site = db.session.get(JobSite, site_id)
    if site is None:
        abort(404)
    db.session.delete(site)
    db.session.commit()
    flash("Seite gelöscht.", "success")
    return redirect(url_for("sites"))


# --------------------------------------------------------------------------- #
# Admin panel (statuses, profile, password)
# --------------------------------------------------------------------------- #
def statuses():
    """Legacy URL — redirects to the admin panel."""
    return redirect(url_for("admin"))


def delete_status(status_id):
    """Legacy URL — deletion happens in the admin panel."""
    return redirect(url_for("admin"))


def profile():
    """Legacy URL — editing happens in the admin panel."""
    return redirect(url_for("admin"))


def admin():
    settings = _get_settings()
    enforced = _password_enforced(settings)

    if request.method == "POST":
        action = request.form.get("action", "")
        if enforced and not _is_authed():
            flash("Bitte zuerst das Passwort eingeben.", "error")
            return redirect(url_for("admin"))

        if action == "add_status":
            name = request.form.get("name", "").strip()
            duplicate = Status.query.filter(
                db.func.lower(Status.name) == name.lower()
            ).first()
            if not name:
                flash("Der Name des Status ist erforderlich.", "error")
            elif duplicate:
                flash(f"Der Status „{name}“ existiert bereits.", "error")
            else:
                db.session.add(Status(name=name))
                db.session.commit()
                flash(f"Status „{name}“ wurde hinzugefügt.", "success")
        elif action == "delete_status":
            status_id = request.form.get("status_id", type=int)
            status = db.session.get(Status, status_id) if status_id else None
            if status is None:
                flash("Status nicht gefunden.", "error")
            else:
                used = Company.query.filter(Company.status_id == status.id).count()
                if used:
                    flash(
                        f"Der Status „{status.name}“ kann nicht gelöscht werden — er "
                        f"wird von {used} "
                        f"{'Firma' if used == 1 else 'Firmen'} verwendet.",
                        "error",
                    )
                else:
                    db.session.delete(status)
                    db.session.commit()
                    flash(f"Status „{status.name}“ wurde gelöscht.", "success")
        elif action == "save_profile":
            data = _get_profile()
            data.full_name = request.form.get("full_name", "").strip()
            data.address = request.form.get("address", "").strip()
            data.plz = request.form.get("plz", "").strip()
            data.city = request.form.get("city", "").strip()
            data.email = request.form.get("email", "").strip()
            data.phone = request.form.get("phone", "").strip()
            data.position = request.form.get("position", "").strip() or DEFAULT_POSITION
            data.cover_letter_template = request.form.get("cover_letter_template", "").strip()
            db.session.commit()
            flash("Profildaten gespeichert.", "success")
        elif action == "apply_template":
            template = request.form.get("cover_letter_template", "").strip()
            if not template:
                flash("Bitte zuerst ein Anschreiben-Muster eingeben.", "error")
            else:
                data = _get_profile()
                data.cover_letter_template = template
                companies = Company.query.all()
                updated = 0
                skipped = 0
                for company in companies:
                    if company.cover_letter_locked:
                        skipped += 1
                    else:
                        company.cover_letter = template
                        updated += 1
                db.session.commit()
                if skipped:
                    flash(
                        f"Anschreiben-Muster auf {updated} Firmen angewendet "
                        f"({skipped} geschützt übersprungen).",
                        "success",
                    )
                else:
                    flash(f"Anschreiben-Muster auf {updated} Firmen angewendet.", "success")
        elif action == "save_password":
            _handle_password_form(settings)
        elif action == "save_share":
            settings.share_enabled = request.form.get("share_enabled") is not None
            if settings.share_enabled and not settings.share_token:
                settings.share_token = secrets.token_hex(16)
            db.session.commit()
            flash("Teilen-Einstellungen gespeichert.", "success")
        elif action == "regenerate_token":
            settings.share_token = secrets.token_hex(16)
            db.session.commit()
            flash("Neuer Link erstellt. Der alte Link funktioniert nicht mehr.", "success")
        return redirect(url_for("admin"))

    if enforced and not _is_authed():
        return render_template("adminpanel.html", mode="login", settings=settings)

    return render_template(
        "adminpanel.html",
        mode="panel",
        statuses=_statuses(),
        profile=_get_profile(),
        settings=settings,
    )


def _handle_password_form(settings):
    """Process the password form and flash feedback."""
    required = request.form.get("password_required") is not None
    if not required:
        settings.password_required = False
        db.session.commit()
        flash("Passwort ist nicht mehr erforderlich.", "success")
        return

    pw = request.form.get("password", "")
    confirm = request.form.get("password_confirm", "")
    if not settings.password_hash and not pw:
        flash("Bitte setzen Sie ein Passwort.", "error")
        return
    if pw or confirm:
        if pw != confirm:
            flash("Die Passwörter stimmen nicht überein.", "error")
            return
        if len(pw) < 6:
            flash("Das Passwort muss mindestens 6 Zeichen haben.", "error")
            return
        settings.password_hash = generate_password_hash(pw, method="pbkdf2:sha256")
    settings.password_required = True
    db.session.commit()
    flash("Einstellungen gespeichert.", "success")


def admin_login():
    settings = _get_settings()
    if not settings.password_hash:
        return redirect(url_for("admin"))
    password = request.form.get("password", "")
    if check_password_hash(settings.password_hash, password):
        session["admin_ok"] = True
        flash("Angemeldet.", "success")
    else:
        flash("Falsches Passwort.", "error")
    return redirect(url_for("admin"))


def admin_logout():
    session.pop("admin_ok", None)
    flash("Abgemeldet.", "success")
    return redirect(url_for("admin"))



def company_pdf(company_id):
    company = Company.query.get_or_404(company_id)
    profile_data = _get_profile()

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.set_margins(24, 20, 24)
    pdf.set_text_color(25, 25, 25)
    pdf.add_font("inter", "", os.path.join(FONT_DIR, "inter.ttf"))
    pdf.add_font("inter", "B", os.path.join(FONT_DIR, "inter-bold.ttf"))
    pdf.add_page()

    # --- sender (my personal data) ---
    pdf.set_font("inter", "B", 11)
    if profile_data.full_name:
        pdf.cell(0, 6, profile_data.full_name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("inter", "", 9.5)
    sender = []
    if profile_data.address:
        sender.append(profile_data.address)
    city_line = " ".join(filter(None, [profile_data.plz, profile_data.city]))
    if city_line:
        sender.append(city_line)
    if profile_data.phone:
        sender.append(f"Tel.: {profile_data.phone}")
    if profile_data.email:
        sender.append(profile_data.email)
    for line in sender:
        pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # --- company (recipient) ---
    if company.name:
        pdf.set_font("inter", "B", 10)
        pdf.cell(0, 6, company.name, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("inter", "", 10)
    if company.address:
        pdf.cell(0, 5, company.address, new_x="LMARGIN", new_y="NEXT")
    if company.address2 and company.city:
        pdf.cell(0, 5, f"{company.address2} {company.city}", new_x="LMARGIN", new_y="NEXT")
    elif company.address2:
        pdf.cell(0, 5, company.address2, new_x="LMARGIN", new_y="NEXT")
    elif company.city:
        pdf.cell(0, 5, company.city, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # --- date / place (above the title) + title ---
    today = datetime.date.today().strftime("%d.%m.%Y")
    dateline = f"{profile_data.city}, {today}" if profile_data.city else today
    pdf.set_font("inter", "", 10)
    pdf.cell(0, 6, dateline, new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.ln(3)

    position = (profile_data.position or DEFAULT_POSITION).strip()
    subject = f"Bewerbung um einen Praktikumsplatz: {position}"
    pdf.set_font("inter", "B", 11)
    pdf.cell(0, 7, subject, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # --- cover letter (body) ---
    body = (company.cover_letter or "").strip()
    if not body:
        body = (
            "Sehr geehrte Damen und Herren,\n\n[Hier das Anschreiben eintragen — "
            "Feld „Anschreiben“ auf der Firmenseite.]"
        )
    pdf.set_font("inter", "", 11)
    pdf.multi_cell(0, 6.5, body)
    pdf.ln(10)

    # --- closing and signature ---
    pdf.set_font("inter", "", 11)
    pdf.cell(0, 6, "Mit freundlichen Grüßen", new_x="LMARGIN", new_y="NEXT")
    if profile_data.full_name:
        pdf.set_font("inter", "B", 11)
        pdf.cell(0, 6, profile_data.full_name, new_x="LMARGIN", new_y="NEXT")

    data = bytes(pdf.output())
    filename = f"bewerbung-{company.id}.pdf"
    return Response(
        data,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- #
# Shared, read-only company list (no password, just a secret link)
# --------------------------------------------------------------------------- #
def share_list(token):
    """Read-only list of companies, reachable via a secret token."""
    settings = _get_settings()
    if not settings.share_enabled or not settings.share_token or settings.share_token != token:
        abort(404)
    return render_template(
        "share.html",
        companies=_ordered_companies(),
        token=token,
    )


def share_export(token):
    """CSV export for the shared list (same token gate)."""
    settings = _get_settings()
    if not settings.share_enabled or not settings.share_token or settings.share_token != token:
        abort(404)
    return _companies_csv()


def admin_export():
    """CSV export for the admin (requires login when password is enforced)."""
    settings = _get_settings()
    if _password_enforced(settings) and not _is_authed():
        return redirect(url_for("admin"))
    return _companies_csv()


# --------------------------------------------------------------------------- #
# Route registration
# --------------------------------------------------------------------------- #
def register_routes(app):
    """Register all routes on the application."""
    app.add_url_rule("/", view_func=index)
    app.add_url_rule("/companies/new", view_func=new_company, methods=["GET", "POST"])
    app.add_url_rule(
        "/companies/<int:company_id>/edit",
        view_func=edit_company,
        methods=["GET", "POST"],
    )
    app.add_url_rule("/companies/<int:company_id>", view_func=company_detail)
    app.add_url_rule("/companies/<int:company_id>/pdf", view_func=company_pdf)
    app.add_url_rule(
        "/companies/<int:company_id>/status",
        view_func=change_status,
        methods=["POST"],
    )
    app.add_url_rule(
        "/companies/<int:company_id>/delete",
        view_func=delete_company,
        methods=["POST"],
    )
    app.add_url_rule(
        "/companies/<int:company_id>/links",
        view_func=add_job_link,
        methods=["POST"],
    )
    app.add_url_rule(
        "/links/<int:link_id>/delete",
        view_func=delete_job_link,
        methods=["POST"],
    )
    app.add_url_rule("/sites", view_func=sites, methods=["GET", "POST"])
    app.add_url_rule(
        "/sites/<int:site_id>/delete",
        view_func=delete_site,
        methods=["POST"],
    )
    app.add_url_rule("/profile", view_func=profile, methods=["GET", "POST"])
    app.add_url_rule("/statuses", view_func=statuses, methods=["GET", "POST"])
    app.add_url_rule("/admin", view_func=admin, methods=["GET", "POST"])
    app.add_url_rule("/admin/login", view_func=admin_login, methods=["POST"])
    app.add_url_rule("/admin/logout", view_func=admin_logout, methods=["POST"])
    app.add_url_rule("/share/<token>", view_func=share_list)
    app.add_url_rule("/share/<token>/export.csv", view_func=share_export)
    app.add_url_rule("/admin/export.csv", view_func=admin_export)



