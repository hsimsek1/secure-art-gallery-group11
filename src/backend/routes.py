"""Login, logout, a database-backed dashboard, and one role check."""
import re

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select

from .models import AuditLog, Room, User, db

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

    user = db.session.scalar(select(User).where(User.username == username))
    if user is None or not user.check_password(password):
        db.session.add(AuditLog(user_id=user.id if user else None, action="LOGIN_FAILED"))
        db.session.commit()
        return render_template("login.html", error="Invalid username or password."), 401

    session.clear()
    login_user(user)
    session.permanent = True
    db.session.add(AuditLog(user_id=user.id, action="LOGIN_SUCCESS"))
    db.session.commit()
    return redirect(url_for("web.dashboard"))


@web.post("/logout")
@login_required
def logout():
    db.session.add(AuditLog(user_id=current_user.id, action="LOGOUT"))
    db.session.commit()
    logout_user()
    session.clear()
    return redirect(url_for("web.login"))


@web.get("/dashboard")
@login_required
def dashboard():
    rooms = db.session.scalars(select(Room).order_by(Room.id)).all()
    return render_template("dashboard.html", rooms=rooms)


@web.get("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)
    return render_template("admin.html")
