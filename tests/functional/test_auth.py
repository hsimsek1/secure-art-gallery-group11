import sqlite3

import pytest
from sqlalchemy import inspect, select

from src.backend import ROOT
from src.backend.models import AuditLog, Person, Room, User, db
from tests.conftest import csrf_token


@pytest.mark.parametrize("role", ["guest", "employee", "admin"])
def test_valid_login(client, login, role):
    response = login(role)
    assert response.status_code == 302
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert (role + "11").encode() in page.data
    assert b"Painting Room" in page.data


def test_invalid_password(client, login):
    assert login(password="incorrect-password").status_code == 401
    assert client.get("/dashboard").status_code == 302


def test_protected_page_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.location


def test_logout_clears_session_and_logs_authentication(app, client, login):
    login()
    response = client.post("/logout", data={"csrf_token": csrf_token(client, "/dashboard")})
    assert response.status_code == 302
    assert client.get("/dashboard").status_code == 302
    with app.app_context():
        actions = db.session.scalars(select(AuditLog.action).order_by(AuditLog.id)).all()
        assert actions == ["LOGIN_SUCCESS", "LOGOUT"]


def test_database_initialization_and_seed(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    with app.app_context():
        assert set(inspect(db.engine).get_table_names()) == {"users", "persons", "rooms", "audit_logs"}
        assert len(db.session.scalars(select(User)).all()) == 3
        assert len(db.session.scalars(select(Person)).all()) == 2
        assert len(db.session.scalars(select(Room)).all()) == 2


def test_sql_schema_and_seed_match_models(app):
    with sqlite3.connect(":memory:") as connection:
        connection.executescript((ROOT / "database/schema.sql").read_text())
        connection.executescript((ROOT / "database/seed.sql").read_text())
        assert connection.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 2
        with app.app_context():
            for table in db.metadata.sorted_tables:
                columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table.name})")}
                assert columns == set(table.columns.keys())


def test_invalid_login_input(client):
    response = client.post("/login", data={
        "username": "!", "password": "example-password",
        "csrf_token": csrf_token(client, "/login"),
    })
    assert response.status_code == 400
