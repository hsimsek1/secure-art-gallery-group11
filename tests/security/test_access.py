import pytest
from werkzeug.security import check_password_hash

from src.backend.db import get_db


def test_passwords_are_hashed(app):
    with app.app_context():
        user = get_db().execute("SELECT * FROM users WHERE username = ?", ("employee11",)).fetchone()
        assert user["password_hash"] != app.config["TEST_PASSWORD"]
        assert user["password_hash"].startswith("scrypt:")
        assert check_password_hash(user["password_hash"], app.config["TEST_PASSWORD"])


@pytest.mark.parametrize("role", ["guest", "employee"])
def test_non_admin_cannot_access_admin_page(client, login, role):
    login(role)
    assert client.get("/admin").status_code == 403


def test_admin_can_access_admin_page(client, login):
    login("admin")
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Access granted" in response.data


def test_login_requires_csrf_token(client):
    assert client.post("/login", data={"username": "guest11", "password": "example"}).status_code == 400
