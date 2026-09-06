"""Start the SEIRI server (application + run).

On every start it checks and updates the database schema
(startdb.ensure_schema), then starts the development server.
"""
import os
import secrets

from flask import Flask

from models import db
from routes import register_routes
from startdb import ensure_schema


def _load_secret_key(basedir):
    """Return the Flask secret key.

    Prefers the SECRET_KEY environment variable. Otherwise a random key is
    generated once and persisted in instance/secret_key (gitignored), so
    sessions stay valid across restarts without a hardcoded fallback.
    """
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key

    instance_dir = os.path.join(basedir, "instance")
    key_path = os.path.join(instance_dir, "secret_key")
    if os.path.exists(key_path):
        with open(key_path, "r", encoding="ascii") as f:
            key = f.read().strip()
        if key:
            return key

    key = secrets.token_hex(32)
    os.makedirs(instance_dir, exist_ok=True)
    with open(key_path, "w", encoding="ascii") as f:
        f.write(key)
    return key


def create_app(test_config=None):
    """Flask application factory."""
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))

    if test_config is None:
        app.config.from_mapping(SECRET_KEY=_load_secret_key(basedir))
    else:
        app.config.from_mapping(SECRET_KEY="test-secret-key")

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

    # Default port is 5001 - on macOS port 5000 is taken by the system
    # ControlCenter process (AirPlay), so we cannot start there.
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)