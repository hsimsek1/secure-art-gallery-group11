import sqlite3

import pytest

from src.backend import ROOT
from src.backend.db import get_db
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
        actions = [row["action"] for row in get_db().execute("SELECT action FROM audit_logs ORDER BY id")]
        assert actions == ["LOGIN_SUCCESS", "LOGOUT"]


def test_database_initialization_and_seed(app):
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    with app.app_context():
        connection = get_db()
        tables = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert tables == {"users", "persons", "rooms", "audit_logs"}
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 3
        assert connection.execute("SELECT COUNT(*) FROM persons").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 2


def test_schema_enforces_roles_and_foreign_keys():
    with sqlite3.connect(":memory:") as connection:
        connection.executescript((ROOT / "database/schema.sql").read_text())
        connection.executescript((ROOT / "database/seed.sql").read_text())
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("invalid", "not-a-real-password-hash", "superuser"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO audit_logs (user_id, action, timestamp) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (999, "LOGIN_SUCCESS"),
            )


def test_invalid_login_input(client):
    response = client.post("/login", data={
        "username": "!", "password": "example-password",
        "csrf_token": csrf_token(client, "/login"),
    })
    assert response.status_code == 400
