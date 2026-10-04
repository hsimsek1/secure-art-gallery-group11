"""Login, logout, a database-backed dashboard, and one role check."""
import re

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from .db import get_db, record_auth
from .users import User

web = Blueprint("web", __name__)


@web.get("/")
def index():
    return redirect(url_for("web.dashboard" if current_user.is_authenticated else "web.login"))


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    if not re.fullmatch(r"[a-z0-9_]{1,40}", username) or not 1 <= len(password) <= 128:
        return render_template("login.html", error="Enter a valid username and password."), 400

    row = get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None or not check_password_hash(row["password_hash"], password):
        record_auth("LOGIN_FAILED", row["id"] if row else None)
        return render_template("login.html", error="Invalid username or password."), 401

    session.clear()
    login_user(User(**row))
    session.permanent = True
    record_auth("LOGIN_SUCCESS", row["id"])
    return redirect(url_for("web.dashboard"))


@web.post("/logout")
@login_required
def logout():
    record_auth("LOGOUT", current_user.id)
    logout_user()
    session.clear()
    return redirect(url_for("web.login"))


@web.get("/dashboard")
@login_required
def dashboard():
    rooms = get_db().execute("SELECT * FROM rooms ORDER BY id").fetchall()
    return render_template("dashboard.html", rooms=rooms)


@web.get("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)
    return render_template("admin.html")
