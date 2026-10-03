from datetime import datetime
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError

from src.backend.models import AuditLog, GalleryEvent, db
from tests.conftest import csrf_token


def test_malformed_event_is_audited(login, client, app):
    login()
    assert client.post("/events", data={"person_id": "invalid", "event_type": "ENTER_GALLERY", "expected_version": "0",
                                       "csrf_token": csrf_token(client, "/events")}).status_code == 400
    with app.app_context():
        log = db.session.scalar(select(AuditLog).order_by(AuditLog.id.desc()))
        assert log.action == "GALLERY_EVENT_REJECTED" and log.result == "REJECTED"


def test_date_overflow_and_duplicate_filters(login, client):
    login()
    assert client.get("/history?end=9999-12-31").status_code == 400
    assert client.get("/history?person_id=1&person_id=2").status_code == 400


def test_database_failure_is_generic(login, client, app, monkeypatch):
    login()
    def fail(*args, **kwargs):
        raise OperationalError("PRIVATE SQL", {"password": "DO_NOT_DISCLOSE"}, Exception("private file path"))
    with app.app_context():
        monkeypatch.setattr(db.session, "get", fail)
        response = client.get("/dashboard")
    assert response.status_code == 503
    assert b"DO_NOT_DISCLOSE" not in response.data and b"PRIVATE SQL" not in response.data


def test_unexpected_error_is_generic(login, client, app, monkeypatch):
    login()
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE INTERNAL DETAILS")
    monkeypatch.setattr("src.backend.routes.current_state", fail)
    response = client.get("/dashboard")
    assert response.status_code == 500
    assert b"PRIVATE INTERNAL DETAILS" not in response.data


def test_audit_failure_rolls_back_event(app, monkeypatch):
    from src.backend.services import record_event
    def fail(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")
    monkeypatch.setattr("src.backend.services.audit", fail)
    with app.app_context():
        with pytest.raises(RuntimeError):
            record_event(2, 1, "ENTER_GALLERY", None, 0)
        assert db.session.scalars(select(GalleryEvent)).all() == []


def test_server_clock_reversal_preserves_order(login, move, app, monkeypatch):
    login()
    move("ENTER_GALLERY")
    monkeypatch.setattr("src.backend.services.utcnow", lambda: datetime(2000, 1, 1))
    assert move("LEAVE_GALLERY").status_code == 302
    with app.app_context():
        rows = db.session.scalars(select(GalleryEvent).order_by(GalleryEvent.id)).all()
        assert rows[1].timestamp > rows[0].timestamp


def test_production_cookie_secure(login, app):
    app.config["SESSION_COOKIE_SECURE"] = True
    response = login()
    assert "Secure" in response.headers["Set-Cookie"]
    assert "max-age=" in response.headers["Strict-Transport-Security"]


def test_exported_schema_and_seed_match_models(tmp_path):
    root = Path(__file__).resolve().parents[2]
    connection = sqlite3.connect(tmp_path / "schema.db")
    connection.executescript((root / "database" / "schema.sql").read_text())
    connection.executescript((root / "database" / "seed.sql").read_text())
    connection.executescript((root / "database" / "seed.sql").read_text())
    for table in db.metadata.sorted_tables:
        columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table.name}")')}
        assert columns == set(table.columns.keys())
    assert connection.execute("SELECT count(*) FROM persons").fetchone()[0] == 2
    assert connection.execute("SELECT count(*) FROM rooms").fetchone()[0] == 2
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute("INSERT INTO rooms (name, capacity) VALUES (?, ?)", ("Invalid", 0))
    connection.close()
