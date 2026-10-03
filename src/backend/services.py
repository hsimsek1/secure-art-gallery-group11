"""State transitions and serialized database writes, independent of HTML forms."""
from contextlib import contextmanager
from datetime import timedelta

from flask import abort
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from .models import AuditLog, GalleryEvent, Person, Room, User, db, utcnow


def audit(session, actor_id, action, details="", result="SUCCESS"):
    session.add(AuditLog(user_id=actor_id, action=action, details=details, result=result))


@contextmanager
def write_transaction(actor_id=None, roles=()):
    # Acquire SQLite's write reservation BEFORE reading state. Concurrent requests
    # wait, then read the committed result of the previous request.
    with Session(db.engine) as transaction:
        transaction.execute(text("BEGIN IMMEDIATE"))
        if actor_id is not None:
            actor = transaction.get(User, actor_id)
            if actor is None or not actor.active or actor.role not in roles:
                abort(403)
        try:
            yield transaction
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise


def current_state(session):
    """Map person ID to room ID (None = gallery lobby); absent means outside."""
    state = {}
    for event in session.scalars(select(GalleryEvent).order_by(GalleryEvent.id)):
        if event.event_type == "ENTER_GALLERY":
            state[event.person_id] = None
        elif event.event_type == "LEAVE_GALLERY":
            state.pop(event.person_id, None)
        elif event.event_type == "ENTER_ROOM":
            state[event.person_id] = event.room_id
        elif event.event_type == "LEAVE_ROOM":
            state[event.person_id] = None
    return state


def ledger_version(session):
    return session.scalar(select(func.max(GalleryEvent.id))) or 0


def record_event(actor_id, person_id, event_type, room_id, expected_version):
    """Append an accepted event and audit row atomically; audit rejections too."""
    with write_transaction(actor_id, ("employee", "admin")) as transaction:
        version = ledger_version(transaction)
        state = current_state(transaction)
        room = transaction.get(Room, room_id) if room_id else None
        inside = person_id in state
        occupied_room = state.get(person_id)
        reason = None
        if expected_version != version:
            reason = "The gallery changed. Refresh the form before recording another event."
        elif transaction.get(Person, person_id) is None:
            reason = "Person does not exist."
        elif event_type not in ("ENTER_GALLERY", "LEAVE_GALLERY", "ENTER_ROOM", "LEAVE_ROOM"):
            reason = "Unknown event type."
        elif event_type.endswith("ROOM") and room is None:
            reason = "Choose an existing room."
        elif event_type.endswith("GALLERY") and room_id is not None:
            reason = "Gallery events must not specify a room."
        elif event_type == "ENTER_GALLERY" and inside:
            reason = "This person is already inside the gallery."
        elif event_type == "LEAVE_GALLERY" and not inside:
            reason = "This person is already outside the gallery."
        elif event_type == "LEAVE_GALLERY" and occupied_room is not None:
            reason = "Leave the room before leaving the gallery."
        elif event_type == "ENTER_ROOM" and not inside:
            reason = "Enter the gallery before entering a room."
        elif event_type == "ENTER_ROOM" and occupied_room is not None:
            reason = "Leave the current room before entering another room."
        elif event_type == "ENTER_ROOM" and sum(r == room_id for r in state.values()) >= room.capacity:
            reason = "This room is full."
        elif event_type == "LEAVE_ROOM" and (not inside or occupied_room != room_id):
            reason = "This person does not occupy that room."
        if reason:
            audit(transaction, actor_id, "GALLERY_EVENT_REJECTED", reason, "REJECTED")
            return False, reason
        last = transaction.get(GalleryEvent, version) if version else None
        timestamp = utcnow()
        if last:
            timestamp = max(timestamp, last.timestamp + timedelta(microseconds=1))
        event = GalleryEvent(person_id=person_id, room_id=room_id, event_type=event_type,
                             created_by=actor_id, timestamp=timestamp)
        transaction.add(event)
        transaction.flush()
        audit(transaction, actor_id, "GALLERY_EVENT", f"event:{event.id} person:{person_id} {event_type}")
        return True, "Event recorded."
