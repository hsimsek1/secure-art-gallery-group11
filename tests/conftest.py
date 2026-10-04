import re
import secrets

import pytest

from src.backend import create_app
from src.backend.models import db


@pytest.fixture
def app(tmp_path, monkeypatch):
    password = secrets.token_urlsafe(18)
    for role in ("guest", "employee", "admin"):
        monkeypatch.setenv(f"SEED_{role.upper()}_PASSWORD", password)
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(32),
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
    })
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    app.config["TEST_PASSWORD"] = password
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_token(client, path):
    response = client.get(path)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


@pytest.fixture
def login(app, client):
    def perform(role="employee", password=None):
        return client.post("/login", data={
            "username": role + "11",
            "password": app.config["TEST_PASSWORD"] if password is None else password,
            "csrf_token": csrf_token(client, "/login"),
        })
    return perform
