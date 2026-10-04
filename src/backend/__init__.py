"""Flask setup and two database commands."""
import os
import sqlite3
from datetime import timedelta
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import event, select, text
from sqlalchemy.engine import Engine

from .models import User, db

ROOT = Path(__file__).resolve().parents[2]
login_manager = LoginManager()
csrf = CSRFProtect()


@event.listens_for(Engine, "connect")
def enable_foreign_keys(connection, _):
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")


def create_app(test_config=None):
    load_dotenv(ROOT / ".env")
    instance = ROOT / "instance"
    instance.mkdir(exist_ok=True)
    app = Flask(
        __name__,
        template_folder=str(ROOT / "src/frontend/templates"),
        static_folder=str(ROOT / "src/frontend/static"),
        instance_path=str(instance),
    )
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", ""),
        SQLALCHEMY_DATABASE_URI="sqlite:///week6.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
        MAX_CONTENT_LENGTH=16 * 1024,
        DEBUG=False,
    )
    if test_config:
        app.config.update(test_config)
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("Run tools/setup_local.py to generate a local secret key.")

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except ValueError:
            return None

    from .routes import web
    app.register_blueprint(web)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", message="Administrator access required."), 403

    @app.cli.command("init-db")
    def init_db():
        """Create missing tables without deleting existing records."""
        db.create_all()
        click.echo("Database initialized.")

    @app.cli.command("seed")
    def seed():
        """Create three demo accounts and synthetic reference records."""
        for role in ("guest", "employee", "admin"):
            username = role + "11"
            if db.session.scalar(select(User).where(User.username == username)):
                continue
            password = os.environ.get(f"SEED_{role.upper()}_PASSWORD", "")
            if not 12 <= len(password) <= 128:
                raise click.ClickException("Run tools/setup_local.py before seeding.")
            user = User(username=username, role=role)
            user.set_password(password)
            db.session.add(user)
        # This is a fixed SQL file, never constructed from browser input.
        for statement in (ROOT / "database/seed.sql").read_text().split(";"):
            if statement.strip():
                db.session.execute(text(statement))
        db.session.commit()
        click.echo("Demo accounts, persons and rooms are ready.")

    return app
