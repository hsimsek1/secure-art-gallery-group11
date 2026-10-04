"""The functions that handle requests from the browser."""
from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from .db import get_db, record_auth
from .users import User

# A Blueprint groups these page routes so create_app() can register them.
web = Blueprint("web", __name__)


@web.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web.route("/login", methods=["GET", "POST"])
def login():
    # GET displays the form. POST processes the submitted form.
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    # Accept only short usernames containing these ASCII characters.
    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
    username_is_valid = True
    if len(username) < 1 or len(username) > 40:
        username_is_valid = False
    for character in username:
        if character not in allowed_characters:
            username_is_valid = False

    if not username_is_valid or len(password) < 1 or len(password) > 128:
        message = "Enter a valid username and password."
        return render_template("login.html", error=message), 400

    connection = get_db()
    # The ? keeps the submitted value separate from the SQL statement.
    result = connection.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = result.fetchone()

    user_id = None
    password_is_correct = False
    if user_row is not None:
        user_id = user_row["id"]
        password_is_correct = check_password_hash(user_row["password_hash"], password)

    if not password_is_correct:
        record_auth("LOGIN_FAILED", user_id)
        message = "Invalid username or password."
        return render_template("login.html", error=message), 401

    # Start a new login session only after checking the password.
    session.clear()
    user = User(user_row)
    login_user(user)
    session.permanent = True  # Use the 30-minute lifetime from create_app().
    record_auth("LOGIN_SUCCESS", user.id)
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
    connection = get_db()
    result = connection.execute("SELECT * FROM rooms ORDER BY id")
    rooms = result.fetchall()
    return render_template("dashboard.html", rooms=rooms)


@web.get("/admin")
@login_required
def admin():
    # Check the role here even when the navigation link is hidden.
    if current_user.role != "admin":
        abort(403)
    return render_template("admin.html")
