"""Application factory, configuration, database initialization and safe errors."""
import os
import re
import sqlite3
from datetime import timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, render_template, request, session
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect, CSRFError
from sqlalchemy import event, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from werkzeug.exceptions import HTTPException

from .models import AuditLog, Person, Room, User, db

ROOT = Path(__file__).resolve().parents[1]
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def sqlite_settings(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")


def create_app(test_config=None):
    load_dotenv(ROOT.parent / ".env", override=False)
    instance = ROOT.parent / "instance"
    instance.mkdir(exist_ok=True)
    app = Flask(__name__, template_folder=str(ROOT / "frontend" / "templates"),
                static_folder=str(ROOT / "frontend" / "static"), instance_path=str(instance))
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", ""),
        SQLALCHEMY_DATABASE_URI="sqlite:///gallery.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_SECURE=os.environ.get("APP_ENV") == "production",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        SESSION_REFRESH_EACH_REQUEST=False,
        MAX_CONTENT_LENGTH=16 * 1024,
        MAX_FORM_MEMORY_SIZE=16 * 1024,
        MAX_FORM_PARTS=20,
        WTF_CSRF_TIME_LIMIT=1800,
        DEBUG=False,
    )
    if test_config:
        app.config.update(test_config)
    if not re.fullmatch(r"[0-9a-fA-F]{64,}", app.config["SECRET_KEY"]):
        raise RuntimeError("Generate a SECRET_KEY from at least 32 random bytes with tools/setup_local.py.")
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    login_manager.session_protection = "strong"
    csrf.init_app(app)
    app.config["DUMMY_PASSWORD_HASH"] = generate_password_hash(os.urandom(32).hex(), method="scrypt")
    from .routes import web
    app.register_blueprint(web)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None
        if user and user.active and session.get("version") == user.session_version:
            return user
        return None

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; script-src 'none'; "
            "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        if app.config["SESSION_COOKIE_SECURE"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    def error_response(code):
        # Bypass Flask-Login's template context processor: during a database
        # outage, trying to load current_user again would fail inside the handler.
        return app.jinja_env.get_template("error.html").render(code=code), code

    def safe_error(error):
        code = getattr(error, "code", 500)
        db.session.rollback()
        if code == 400 and request.endpoint == "web.events" and request.method == "POST":
            db.session.add(AuditLog(user_id=current_user.id if current_user.is_authenticated else None,
                                   action="GALLERY_EVENT_REJECTED", details="Invalid form or CSRF token",
                                   result="REJECTED"))
            db.session.commit()
        return error_response(code)

    for code in (400, 404, 405, 409, 413, 429, 500):
        app.register_error_handler(code, safe_error)
    app.register_error_handler(CSRFError, safe_error)

    @app.errorhandler(403)
    def forbidden(error):
        db.session.rollback()
        db.session.add(AuditLog(user_id=current_user.id if current_user.is_authenticated else None,
                               action="AUTHORIZATION_DENIED", details="Protected route",
                               result="REJECTED"))
        db.session.commit()
        return error_response(403)

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        # Never include exception SQL/parameters (potentially sensitive) in responses or logs.
        app.logger.error("Database operation failed: %s", type(error).__name__)
        return error_response(503)

    @app.errorhandler(Exception)
    def unexpected_error(error):
        if isinstance(error, HTTPException):
            return safe_error(error)
        db.session.rollback()
        app.logger.error("Request failed: %s", type(error).__name__)
        return error_response(500)

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables. Never drop existing data."""
        db.create_all()
        click.echo("Database initialized; existing records preserved.")

    @app.cli.command("seed")
    def seed():
        """Add synthetic reference data and demo users; preserve existing users."""
        for role, username in (("admin", "admin11"), ("employee", "employee11"), ("guest", "guest11")):
            if db.session.scalar(select(User).where(User.username == username)):
                continue
            password = os.environ.get(f"SEED_{role.upper()}_PASSWORD", "")
            if not 12 <= len(password) <= 128:
                raise click.ClickException("Run tools/setup_local.py; seed passwords must be 12-128 characters.")
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
        # SQL seed contains reference data only, never credential material.
        from sqlalchemy import text
        for statement in (ROOT.parent / "database" / "seed.sql").read_text().split(";"):
            if statement.strip():
                db.session.execute(text(statement))
        db.session.commit()
        click.echo("Seed complete. Credentials are in ignored local-credentials.txt.")

    return app
