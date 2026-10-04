"""Flask setup and database commands."""
import os
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash

from .db import close_db, get_db
from .users import User

ROOT = Path(__file__).resolve().parents[2]
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    instance = ROOT / "instance"
    instance.mkdir(exist_ok=True)
    app = Flask(
        __name__,
        template_folder=str(ROOT / "src/frontend/templates"),
        static_folder=str(ROOT / "src/frontend/static"),
        instance_path=str(instance),
        instance_relative_config=True,
    )
    app.config.update(
        SECRET_KEY="",
        DATABASE=str(instance / "week6.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=False,
    )
    app.config.from_pyfile("config.py", silent=True)
    # Environment variables can override local settings without another library.
    for key in ("SECRET_KEY", "SEED_GUEST_PASSWORD", "SEED_EMPLOYEE_PASSWORD", "SEED_ADMIN_PASSWORD"):
        if key in os.environ:
            app.config[key] = os.environ[key]
    if test_config:
        app.config.update(test_config)
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("Run tools/setup_local.py to generate a local secret key.")

    app.teardown_appcontext(close_db)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return None
        row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return User(**row) if row else None

    from .routes import web
    app.register_blueprint(web)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", message="Administrator access required."), 403

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables without deleting existing records."""
        get_db().executescript((ROOT / "database/schema.sql").read_text())
        click.echo("Database initialized.")

    @app.cli.command("seed")
    def seed():
        """Create three demo accounts and synthetic reference records."""
        connection = get_db()
        connection.executescript((ROOT / "database/seed.sql").read_text())
        with connection:
            for role in ("guest", "employee", "admin"):
                username = role + "11"
                if connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
                    continue
                password = app.config.get(f"SEED_{role.upper()}_PASSWORD", "")
                if not 12 <= len(password) <= 128:
                    raise click.ClickException("Run tools/setup_local.py before seeding.")
                connection.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, generate_password_hash(password, method="scrypt"), role),
                )
        click.echo("Demo accounts, persons and rooms are ready.")

    return app
