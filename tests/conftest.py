import re
import secrets

import pytest

from src.backend import create_app


@pytest.fixture
def app(tmp_path):
    # Each test gets its own database and never changes the demo database.
    password = secrets.token_urlsafe(18)
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": secrets.token_hex(32),
        "DATABASE": str(tmp_path / "test.db"),
        "SEED_GUEST_PASSWORD": password,
        "SEED_EMPLOYEE_PASSWORD": password,
        "SEED_ADMIN_PASSWORD": password,
    })
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    app.config["TEST_PASSWORD"] = password
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf_token(client, path):
    # Read the form's hidden token, just as a browser would send it back.
    response = client.get(path)
    match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
    assert match is not None
    return match.group(1).decode()


@pytest.fixture
def login(app, client):
    def perform(role="employee", password=None):
        if password is None:
            password = app.config["TEST_PASSWORD"]
        return client.post("/login", data={
            "username": role + "11",
            "password": password,
            "csrf_token": csrf_token(client, "/login"),
        })
    return perform
