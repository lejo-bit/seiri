"""Modele bazy danych dla aplikacji SEIRI – Praktikum."""
import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _utcnow():
    """Aktualny czas UTC (naive) — zgodny z różnymi wersjami Pythona."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


# Feste Rekrutierungs-Zustände („sucht das Unternehmen jemanden für ein Praktikum?“)
RECRUITMENT_LABELS = {
    "looking": "sucht",
    "not_looking": "sucht nicht",
    "unknown": "unbekannt",
}
RECRUITMENT_DEFAULT = "unknown"

# Domyślna nazwa stanowiska (używana w liście / PDF)
DEFAULT_POSITION = "Fachinformatiker – Daten und Prozessanalyse"


class Status(db.Model):
    """Status aplikacji, który może być przypisany firmom."""

    __tablename__ = "status"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    companies = db.relationship("Company", back_populates="status")

    def __repr__(self):
        return f"<Status {self.name!r}>"


class Company(db.Model):
    """Firma oferująca miejsca praktyk."""

    __tablename__ = "company"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    address2 = db.Column(db.String(200))
    city = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    cover_letter = db.Column(db.Text)
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"))
    recruitment = db.Column(db.String(20), default=RECRUITMENT_DEFAULT)
    updated_at = db.Column(
        db.DateTime,
        default=_utcnow,
        onupdate=_utcnow,
    )

    status = db.relationship("Status", back_populates="companies")

    @property
    def recruitment_label(self):
        return RECRUITMENT_LABELS.get(self.recruitment or RECRUITMENT_DEFAULT)

    def __repr__(self):
        return f"<Company {self.name!r}>"


class Profile(db.Model):
    """Moje dane (jeden rekord, używany w liście motywacyjnym / PDF)."""

    __tablename__ = "profile"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(160))
    address = db.Column(db.String(200))
    city = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    position = db.Column(db.String(200), default=DEFAULT_POSITION)

    def __repr__(self):
        return f"<Profile {self.full_name!r}>"


