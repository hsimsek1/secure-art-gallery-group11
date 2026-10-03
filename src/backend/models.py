"""Five small relational tables; movement state is derived from the event ledger."""
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()
ROLES = ("guest", "employee", "admin")
EVENT_TYPES = ("ENTER_GALLERY", "LEAVE_GALLERY", "ENTER_ROOM", "LEAVE_ROOM")


def utcnow():
    # SQLite stores naive datetimes; every timestamp in this project means UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(12), nullable=False, default="guest")
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    session_version = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (CheckConstraint("role IN ('guest','employee','admin')"),)

    @property
    def is_active(self):
        return self.active

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Person(db.Model):
    __tablename__ = "persons"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    kind = db.Column(db.String(12), nullable=False, default="guest")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    __table_args__ = (CheckConstraint("kind IN ('guest','employee')"),)


class Room(db.Model):
    __tablename__ = "rooms"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)
    __table_args__ = (CheckConstraint("capacity > 0"),)


class GalleryEvent(db.Model):
    __tablename__ = "gallery_events"
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey("persons.id"), nullable=False, index=True)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"))
    event_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    person = db.relationship(Person)
    room = db.relationship(Room)
    creator = db.relationship(User)
    __table_args__ = (
        CheckConstraint("event_type IN ('ENTER_GALLERY','LEAVE_GALLERY','ENTER_ROOM','LEAVE_ROOM')"),
        CheckConstraint("(event_type IN ('ENTER_ROOM','LEAVE_ROOM') AND room_id IS NOT NULL) OR "
                        "(event_type IN ('ENTER_GALLERY','LEAVE_GALLERY') AND room_id IS NULL)"),
    )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(40), nullable=False, index=True)
    details = db.Column(db.String(200), nullable=False, default="")
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    result = db.Column(db.String(12), nullable=False)
    __table_args__ = (CheckConstraint("result IN ('SUCCESS','REJECTED')"),)
