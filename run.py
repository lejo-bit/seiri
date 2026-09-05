"""Uruchomienie serwera SEIRI (aplikacja + start).

Przy każdym starcie sprawdza i aktualizuje bazę danych (startdb.ensure_schema),
a następnie uruchamia serwer deweloperski.
"""
import os

from flask import Flask

from models import db
from routes import register_routes
from startdb import ensure_schema


def create_app(test_config=None):
    """Fabryka aplikacji Flask."""
    app = Flask(__name__)
    app.config.from_mapping(SECRET_KEY=os.environ.get("SECRET_KEY", "dev"))

    basedir = os.path.abspath(os.path.dirname(__file__))
    if test_config is None:
        default_db_path = os.path.join(basedir, "instance", "seiri.db")
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=os.environ.get(
                "DATABASE_URL",
                "sqlite:///" + default_db_path,
            ),
        )
    else:
        app.config.update(test_config)

    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    db.init_app(app)
    register_routes(app)
    return app


if __name__ == "__main__":
    app = create_app()
    ensure_schema(app)

    # Domyślny port 5001 — na macOS port 5000 jest zajęty przez systemowy
    # proces ControlCenter (AirPlay), więc tam nie wystartujemy.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
