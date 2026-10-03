from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import func, select

from src.backend.models import AuditLog, GalleryEvent, db
from src.backend.services import current_state, record_event


@pytest.mark.parametrize("setup,event,room", [
    ([("ENTER_GALLERY", None)], "ENTER_GALLERY", None),
    ([], "LEAVE_GALLERY", None),
    ([], "ENTER_ROOM", 1),
    ([("ENTER_GALLERY", None), ("ENTER_ROOM", 1)], "ENTER_ROOM", 2),
    ([("ENTER_GALLERY", None), ("ENTER_ROOM", 1)], "LEAVE_ROOM", 2),
    ([("ENTER_GALLERY", None), ("ENTER_ROOM", 1)], "LEAVE_GALLERY", None),
    ([("ENTER_GALLERY", None), ("ENTER_ROOM", 1)], "ENTER_ROOM", 1),
    ([], "LEAVE_ROOM", 1),
    ([("ENTER_GALLERY", None)], "ENTER_ROOM", 999),
    ([], "ENTER_GALLERY", 1),
])
def test_invalid_transition_rejected(login, move, app, setup, event, room):
    login()
    for initial, initial_room in setup:
        assert move(initial, room_id=initial_room).status_code == 302
    with app.app_context():
        before = current_state(db.session)
    response = move(event, room_id=room)
    assert response.status_code == 409
    with app.app_context():
        assert current_state(db.session) == before
        assert db.session.scalar(select(func.count()).select_from(GalleryEvent)) == len(setup)
        assert db.session.scalar(select(AuditLog).order_by(AuditLog.id.desc())).action == "GALLERY_EVENT_REJECTED"


def test_capacity_rejected(login, move):
    login()
    move("ENTER_GALLERY")
    move("ENTER_ROOM", room_id=1)
    move("ENTER_GALLERY", person_id=2)
    assert move("ENTER_ROOM", person_id=2, room_id=1).status_code == 409


def test_stale_replay_after_complete_cycle(login, move, app):
    login()
    move("ENTER_GALLERY")
    move("LEAVE_GALLERY")
    assert move("ENTER_GALLERY", version=0).status_code == 409
    with app.app_context():
        assert current_state(db.session) == {}


def test_missing_person_rejected(login, move):
    login()
    assert move("ENTER_GALLERY", person_id=999).status_code == 409


def test_concurrent_entries_one_wins(app):
    barrier = Barrier(2)
    def attempt():
        with app.app_context():
            barrier.wait(timeout=10)
            return record_event(2, 1, "ENTER_GALLERY", None, 0)[0]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(attempt) for _ in range(2)]
        results = [future.result(timeout=15) for future in futures]
    assert sorted(results) == [False, True]
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(GalleryEvent)) == 1


def test_concurrent_room_capacity(app):
    with app.app_context():
        assert record_event(2, 1, "ENTER_GALLERY", None, 0)[0]
        assert record_event(2, 2, "ENTER_GALLERY", None, 1)[0]
    barrier = Barrier(2)
    def attempt(person_id):
        with app.app_context():
            barrier.wait(timeout=10)
            return record_event(2, person_id, "ENTER_ROOM", 1, 2)[0]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(attempt, (1, 2)))
    assert sorted(results) == [False, True]
    with app.app_context():
        assert sum(room == 1 for room in current_state(db.session).values()) == 1
