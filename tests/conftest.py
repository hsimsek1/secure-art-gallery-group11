import re
import secrets

import pytest
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from src.backend import create_app
from src.backend.models import Person, Room, User, db
from src.backend.services import ledger_version


@pytest.fixture(scope="session")
def credentials():
    password = secrets.token_urlsafe(18)
    return password, generate_password_hash(password, method="scrypt")


@pytest.fixture
def app(tmp_path, credentials):
    app = create_app({"TESTING": True, "SECRET_KEY": secrets.token_hex(32),
                      "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
                      "WTF_CSRF_ENABLED": True})
    with app.app_context():
        db.create_all()
        for role in ("admin", "employee", "guest"):
            db.session.add(User(username=role, role=role, password_hash=credentials[1]))
        db.session.add(User(username="disabled", role="employee", active=False, password_hash=credentials[1]))
        db.session.add_all([Person(name="Alex", kind="guest"), Person(name="Sam", kind="employee"),
                            Room(name="Paintings", capacity=1), Room(name="Sculptures", capacity=5)])
        db.session.commit()
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
    assert match, response.data.decode()
    return match.group(1).decode()


@pytest.fixture
def login(client, credentials):
    def perform(role="employee", password=None):
        return client.post("/login", data={"username": role, "password": password or credentials[0],
                                          "csrf_token": csrf_token(client, "/login")})
    return perform


@pytest.fixture
def move(app, client):
    def perform(event_type, person_id=1, room_id=None, version=None, **extras):
        with app.app_context():
            version = ledger_version(db.session) if version is None else version
        data = {"person_id": str(person_id), "event_type": event_type, "expected_version": str(version),
                "room_id": str(room_id) if room_id is not None else "", "csrf_token": csrf_token(client, "/events")}
        data.update(extras)
        return client.post("/events", data=data)
    return perform
