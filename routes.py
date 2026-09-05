"""SEIRI application routes — split out for readability."""
import datetime
import os

from fpdf import FPDF
from flask import (
    Response,
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
        "status_id": request.form.get("status_id", type=int),
        "recruitment": request.form.get("recruitment", "").strip(),
    }


def _clean_recruitment(value):
    return value if value in RECRUITMENT_LABELS else RECRUITMENT_DEFAULT


def _apply_company_form(company, fields):
    """Apply the form fields to the Company object."""
    company.name = fields["name"]
    company.address = fields["address"]
    company.address2 = fields["address2"]
    company.city = fields["city"]
    company.email = fields["email"]
    company.phone = fields["phone"]
    company.description = fields["description"]
    company.website = fields["website"]
    company.cover_letter = fields["cover_letter"]
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


# --------------------------------------------------------------------------- #
# Company
# --------------------------------------------------------------------------- #
def index():
    sort = request.args.get("sort", "updated")
    direction = request.args.get("dir", "desc")
    recruitment = request.args.get("rec", "").strip()
    if sort not in ("name", "status", "updated"):
        sort = "updated"
    if direction not in ("asc", "desc"):
        direction = "desc"
    if recruitment not in ("", "looking", "not_looking", "unknown"):
        recruitment = ""

    order_cols = {
        "name": Company.name,
        "status": Status.name,
        "updated": Company.updated_at,
    }
    query = Company.query.outerjoin(Status, Company.status_id == Status.id)
    if recruitment:
        query = query.filter(Company.recruitment == recruitment)
    column = order_cols[sort]
    companies = query.order_by(
        column.asc() if direction == "asc" else column.desc()
    ).all()
    return render_template(
        "index.html",
        companies=companies,
        sort=sort,
        direction=direction,
        recruitment=recruitment,
    )


def new_company():
    statuses = _statuses()
    company = Company()
    if request.method == "POST":
        fields = _fields_from_form()
        _apply_company_form(company, fields)
        error = _validate_company(fields)
        if error:
            flash(error, "error")
            return render_template("company_form.html", company=company, statuses=statuses)
        db.session.add(company)
        db.session.commit()
        flash(f"Firma „{company.name}“ wurde hinzugefügt.", "success")
        return redirect(url_for("company_detail", company_id=company.id))
    return render_template("company_form.html", company=None, statuses=statuses)


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
            data.city = request.form.get("city", "").strip()
            data.email = request.form.get("email", "").strip()
            data.phone = request.form.get("phone", "").strip()
            data.position = request.form.get("position", "").strip() or DEFAULT_POSITION
            db.session.commit()
            flash("Profildaten gespeichert.", "success")
        elif action == "save_password":
            _handle_password_form(settings)
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
    if profile_data.city:
        sender.append(profile_data.city)
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
    if company.address2:
        pdf.cell(0, 5, company.address2, new_x="LMARGIN", new_y="NEXT")
    if company.city:
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
    app.add_url_rule("/profile", view_func=profile, methods=["GET", "POST"])
    app.add_url_rule("/statuses", view_func=statuses, methods=["GET", "POST"])
    app.add_url_rule("/admin", view_func=admin, methods=["GET", "POST"])
    app.add_url_rule("/admin/login", view_func=admin_login, methods=["POST"])
    app.add_url_rule("/admin/logout", view_func=admin_logout, methods=["POST"])



