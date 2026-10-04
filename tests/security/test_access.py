import pytest
from sqlalchemy import select

from src.backend.models import User, db


def test_passwords_are_hashed(app):
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "employee11"))
        assert user.password_hash != app.config["TEST_PASSWORD"]
        assert user.password_hash.startswith("scrypt:")
        assert user.check_password(app.config["TEST_PASSWORD"])


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
