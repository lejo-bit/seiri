"""Start the SEIRI server (application + run).

On every start it checks and updates the database schema
(startdb.ensure_schema), then starts the development server.
"""
import os
import secrets

from flask import Flask, flash, redirect, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db
from routes import limiter, register_routes
from startdb import ensure_schema


csrf = CSRFProtect()


def handle_csrf_error(reason):
    """Return a friendly page instead of a bare 400 on CSRF failure."""
    flash("Ihre Sitzung ist abgelaufen oder ungültig. Bitte versuchen Sie es erneut.", "error")
    referrer = request.referrer
    if referrer and request.host and request.host in referrer:
        return redirect(referrer)
    return redirect(url_for("index"))


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

    # --- security hardening (sessions, proxy, CSRF, headers) ---
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SEIRI_SECURE_COOKIES", "0") == "1",
    )

    if os.environ.get("BEHIND_PROXY", "0") == "1":
        # Trust a single reverse proxy (nginx) for the real client IP / scheme.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    csrf.init_app(app)
    app.errorhandler(CSRFError)(handle_csrf_error)
    limiter.init_app(app)

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
            "font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        )
        return response

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