"""Server-rendered pages. Every protected operation checks roles on the server."""
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import re

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select
from werkzeug.security import check_password_hash

from .models import AuditLog, EVENT_TYPES, GalleryEvent, Person, ROLES, Room, User, db, utcnow
from .services import audit, current_state, ledger_version, record_event, write_transaction

web = Blueprint("web", __name__)


def roles_required(*roles):
    def decorate(function):
        @wraps(function)
        @login_required
        def wrapped(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return function(*args, **kwargs)
        return wrapped
    return decorate


def fields(required, optional=()):
    supplied = set(request.form) - {"csrf_token"}
    if not set(required) <= supplied or supplied - set(required) - set(optional):
        abort(400)
    if any(len(request.form.getlist(key)) != 1 for key in request.form):
        abort(400)


def number(value, minimum=1):
    if not value or not re.fullmatch(r"[0-9]{1,9}", value) or int(value) < minimum:
        abort(400)
    return int(value)


def valid_name(value):
    value = value.strip()
    if not 1 <= len(value) <= 80 or any(ord(c) < 32 for c in value):
        abort(400)
    return value


@web.route("/")
def index():
    return redirect(url_for("web.dashboard" if current_user.is_authenticated else "web.login"))


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    fields(("username", "password"))
    username = request.form["username"].strip().lower()
    password = request.form["password"]
    if not 1 <= len(username) <= 40 or not 1 <= len(password) <= 128:
        abort(400)
    # IP-based throttling is deliberately local/demo scale; no forwarded header trust.
    source = "source:" + hashlib.sha256((request.remote_addr or "unknown").encode()).hexdigest()[:32]
    cutoff = utcnow() - timedelta(minutes=15)
    failures = db.session.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.action == "LOGIN_FAILED", AuditLog.details == source, AuditLog.timestamp >= cutoff))
    if failures >= 10:
        return render_template("error.html", code=429), 429
    user = db.session.scalar(select(User).where(User.username == username))
    candidate_hash = user.password_hash if user else current_app.config["DUMMY_PASSWORD_HASH"]
    matches = check_password_hash(candidate_hash, password)
    if not user or not matches or not user.active:
        audit(db.session, user.id if user else None, "LOGIN_FAILED", source, "REJECTED")
        db.session.commit()
        return render_template("login.html", error="Invalid username or password."), 401
    session.clear()
    login_user(user, remember=False)
    session["version"] = user.session_version
    session.permanent = True
    audit(db.session, user.id, "LOGIN_SUCCESS")
    db.session.commit()
    # Never redirect to a client-supplied next URL.
    return redirect(url_for("web.dashboard"))


@web.post("/logout")
@login_required
def logout():
    fields(())
    with write_transaction(current_user.id, ROLES) as transaction:
        user = transaction.get(User, current_user.id)
        user.session_version += 1
        audit(transaction, user.id, "LOGOUT")
    logout_user()
    session.clear()
    return redirect(url_for("web.login"))


@web.get("/dashboard")
@roles_required(*ROLES)
def dashboard():
    state = current_state(db.session)
    rooms = db.session.scalars(select(Room).order_by(Room.id)).all()
    occupants = []
    if current_user.role in ("employee", "admin"):
        occupants = db.session.scalars(select(Person).where(Person.id.in_(state)).order_by(Person.name)).all()
    return render_template("dashboard.html", state=state, rooms=rooms, occupants=occupants,
                           room_counts={room.id: sum(r == room.id for r in state.values()) for room in rooms},
                           room_names={room.id: room.name for room in rooms})


@web.route("/events", methods=["GET", "POST"])
@roles_required("employee", "admin")
def events():
    message, status = None, 200
    if request.method == "POST":
        fields(("person_id", "event_type", "expected_version"), ("room_id",))
        person_id = number(request.form["person_id"])
        room_id = number(request.form["room_id"]) if request.form.get("room_id") else None
        version = number(request.form["expected_version"], minimum=0)
        if request.form["event_type"] not in EVENT_TYPES:
            audit(db.session, current_user.id, "GALLERY_EVENT_REJECTED", "Invalid event type", "REJECTED")
            db.session.commit()
            abort(400)
        success, message = record_event(current_user.id, person_id, request.form["event_type"], room_id, version)
        if success:
            flash(message)
            return redirect(url_for("web.dashboard"))
        status = 409
    return render_template("events.html", people=db.session.scalars(select(Person).order_by(Person.name)).all(),
                           rooms=db.session.scalars(select(Room).order_by(Room.id)).all(),
                           types=EVENT_TYPES, version=ledger_version(db.session), error=message), status


@web.route("/persons", methods=["GET", "POST"])
@roles_required("employee", "admin")
def persons():
    if request.method == "POST":
        fields(("name", "kind"))
        name = valid_name(request.form["name"])
        kind = request.form["kind"]
        if kind not in ("guest", "employee"):
            abort(400)
        with write_transaction(current_user.id, ("employee", "admin")) as transaction:
            person = Person(name=name, kind=kind)
            transaction.add(person)
            transaction.flush()
            audit(transaction, current_user.id, "PERSON_CREATED", f"person:{person.id}")
        flash("Person added.")
        return redirect(url_for("web.persons"))
    page = number(request.args.get("page", "1"))
    people = db.paginate(select(Person).order_by(Person.id), page=page, per_page=25, error_out=False)
    return render_template("persons.html", people=people)


@web.get("/history")
@roles_required("employee", "admin")
def history():
    if set(request.args) - {"person_id", "room_id", "event_type", "start", "end", "page"}:
        abort(400)
    if any(len(request.args.getlist(key)) != 1 for key in request.args):
        abort(400)
    query = select(GalleryEvent)
    for key, column in (("person_id", GalleryEvent.person_id), ("room_id", GalleryEvent.room_id)):
        if request.args.get(key):
            query = query.where(column == number(request.args[key]))
    if request.args.get("event_type"):
        if request.args["event_type"] not in EVENT_TYPES:
            abort(400)
        query = query.where(GalleryEvent.event_type == request.args["event_type"])
    dates = {}
    for key in ("start", "end"):
        if request.args.get(key):
            try:
                dates[key] = datetime.strptime(request.args[key], "%Y-%m-%d")
            except ValueError:
                abort(400)
    if dates.get("start") and dates.get("end") and dates["start"] > dates["end"]:
        abort(400)
    if "start" in dates:
        query = query.where(GalleryEvent.timestamp >= dates["start"])
    if "end" in dates:
        try:
            end_exclusive = dates["end"] + timedelta(days=1)
        except OverflowError:
            abort(400)
        query = query.where(GalleryEvent.timestamp < end_exclusive)
    page = number(request.args.get("page", "1"))
    records = db.paginate(query.order_by(GalleryEvent.id.desc()), page=page, per_page=25, error_out=False)
    filters = request.args.to_dict()
    filters.pop("page", None)
    return render_template("history.html", records=records, types=EVENT_TYPES, filters=filters)


@web.route("/admin/users", methods=["GET", "POST"])
@roles_required("admin")
def admin_users():
    if request.method == "POST":
        fields(("username", "password", "role"))
        username = request.form["username"].strip().lower()
        password, role = request.form["password"], request.form["role"]
        if not re.fullmatch(r"[a-z0-9_]{3,40}", username) or not 12 <= len(password) <= 128 or role not in ROLES:
            abort(400)
        with write_transaction(current_user.id, ("admin",)) as transaction:
            if transaction.scalar(select(User).where(User.username == username)):
                abort(409)
            user = User(username=username, role=role)
            user.set_password(password)
            transaction.add(user)
            transaction.flush()
            audit(transaction, current_user.id, "USER_CREATED", f"user:{user.id} role:{role}")
        flash("User created.")
        return redirect(url_for("web.admin_users"))
    return render_template("admin.html", users=db.session.scalars(select(User).order_by(User.id)).all(), roles=ROLES)


@web.post("/admin/users/<int:user_id>")
@roles_required("admin")
def update_user(user_id):
    fields(("role", "active"))
    role, active = request.form["role"], request.form["active"]
    if role not in ROLES or active not in ("0", "1"):
        abort(400)
    if user_id == current_user.id:
        abort(409)
    with write_transaction(current_user.id, ("admin",)) as transaction:
        user = transaction.get(User, user_id)
        if user is None:
            abort(404)
        user.role, user.active = role, active == "1"
        user.session_version += 1
        audit(transaction, current_user.id, "USER_UPDATED", f"user:{user.id} role:{role} active:{active}")
    flash("User updated; their existing sessions have been invalidated.")
    return redirect(url_for("web.admin_users"))


@web.get("/admin/audit")
@roles_required("admin")
def audit_history():
    page = number(request.args.get("page", "1"))
    logs = db.paginate(select(AuditLog).order_by(AuditLog.id.desc()), page=page, per_page=25, error_out=False)
    return render_template("audit.html", logs=logs)
