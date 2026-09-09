"""Database models for the SEIRI – Praktikum application."""
import datetime
from zoneinfo import ZoneInfo

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BERLIN_TZ = ZoneInfo("Europe/Berlin")


def _utcnow():
    """Current UTC time (naive) — compatible across Python versions."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def berlin_time(value):
    """Convert a stored UTC timestamp to Europe/Berlin for display."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(BERLIN_TZ)


# Fixed recruitment states: "is the company looking for a trainee/praktikum?"
RECRUITMENT_LABELS = {
    "looking": "sucht",
    "not_looking": "sucht nicht",
    "unknown": "unbekannt",
}
RECRUITMENT_DEFAULT = "unknown"

# Default job title (used in the cover letter / PDF)
DEFAULT_POSITION = "Fachinformatiker – Daten und Prozessanalyse"


class Status(db.Model):
    """Application status that can be assigned to companies."""

    __tablename__ = "status"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

    companies = db.relationship("Company", back_populates="status")

    def __repr__(self):
        return f"<Status {self.name!r}>"


class Company(db.Model):
    """A company offering practical training (Praktikum) positions."""

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
    cover_letter_locked = db.Column(db.Boolean, nullable=False, default=False)
    status_id = db.Column(db.Integer, db.ForeignKey("status.id"))
    recruitment = db.Column(db.String(20), default=RECRUITMENT_DEFAULT)
    updated_at = db.Column(
        db.DateTime,
        default=_utcnow,
        onupdate=_utcnow,
    )

    status = db.relationship("Status", back_populates="companies")
    job_links = db.relationship(
        "JobLink",
        back_populates="company",
        cascade="all, delete-orphan",
        order_by="JobLink.id",
    )

    @property
    def recruitment_label(self):
        return RECRUITMENT_LABELS.get(self.recruitment or RECRUITMENT_DEFAULT)

    def __repr__(self):
        return f"<Company {self.name!r}>"


class JobLink(db.Model):
    """A link to a specific job offer for a company."""

    __tablename__ = "job_link"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    company = db.relationship("Company", back_populates="job_links")

    def __repr__(self):
        return f"<JobLink {self.url!r}>"


class JobSite(db.Model):
    """A website/portal where companies search for interns (standalone)."""

    __tablename__ = "job_site"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<JobSite {self.name!r}>"


class Profile(db.Model):
    """My personal data (single record, used in the cover letter / PDF)."""

    __tablename__ = "profile"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(160))
    address = db.Column(db.String(200))
    plz = db.Column(db.String(20))
    city = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    position = db.Column(db.String(200), default=DEFAULT_POSITION)
    cover_letter_template = db.Column(db.Text)

    def __repr__(self):
        return f"<Profile {self.full_name!r}>"


class Settings(db.Model):
    """Application settings (single row)."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    password_required = db.Column(db.Boolean, nullable=False, default=False)
    password_hash = db.Column(db.String(255))
    share_enabled = db.Column(db.Boolean, nullable=False, default=False)
    share_token = db.Column(db.String(64))
    google_search_enabled = db.Column(db.Boolean, nullable=False, default=True)
    design = db.Column(db.String(20), nullable=False, default="dark")


