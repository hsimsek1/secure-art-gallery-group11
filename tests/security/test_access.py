import pytest
from sqlalchemy import select

from src.backend.models import AuditLog, User, db
from tests.conftest import csrf_token


@pytest.mark.parametrize("path", ["/events", "/persons", "/history", "/admin/users", "/admin/audit"])
def test_guest_cannot_access_staff_pages(login, client, path):
    login("guest")
    assert client.get(path).status_code == 403


def test_guest_only_sees_aggregate_counts(login, client):
    login("guest")
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Alex" not in response.data and b"Sam" not in response.data


def test_forged_admin_post_denied(login, client, credentials):
    login()
    response = client.post("/admin/users", data={"username": "intruder", "password": credentials[0], "role": "admin",
                                                "csrf_token": csrf_token(client, "/dashboard")})
    assert response.status_code == 403


def test_actor_timestamp_and_role_cannot_be_forged(login, move):
    login()
    assert move("ENTER_GALLERY", created_by="1").status_code == 400
    assert move("ENTER_GALLERY", timestamp="2000-01-01").status_code == 400
    assert move("ENTER_GALLERY", role="admin").status_code == 400


def test_disabled_account_cannot_login(login):
    assert login("disabled").status_code == 401


def test_disabling_account_invalidates_active_session(login, client, app):
    login()
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "employee"))
        user.active = False
        db.session.commit()
    assert client.get("/dashboard").status_code == 302


def test_role_loaded_from_database_each_request(login, client, app):
    login("admin")
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "admin"))
        user.role = "guest"
        db.session.commit()
    assert client.get("/admin/users").status_code == 403


def test_missing_or_invalid_csrf_rejected(client):
    assert client.post("/login", data={"username": "admin", "password": "anything"}).status_code == 400
    assert client.post("/login", data={"username": "admin", "password": "anything", "csrf_token": "forged"}).status_code == 400


def test_missing_csrf_on_event_rejected(login, client):
    login()
    assert client.post("/events", data={"person_id": "1", "event_type": "ENTER_GALLERY", "expected_version": "0"}).status_code == 400


def test_logout_revokes_copied_cookie(login, client, app):
    login()
    copied_cookie = client.get_cookie("session").value
    assert client.get("/logout").status_code == 405
    response = client.post("/logout", data={"csrf_token": csrf_token(client, "/dashboard")})
    assert response.status_code == 302
    attacker = app.test_client()
    attacker.set_cookie("session", copied_cookie)
    assert attacker.get("/dashboard").status_code == 302


def test_admin_cannot_disable_self(login, client):
    login("admin")
    assert client.post("/admin/users/1", data={"role": "guest", "active": "0", "csrf_token": csrf_token(client, "/admin/users")}).status_code == 409


def test_sql_injection_login_and_history(login, client):
    assert login("' OR 1=1 --").status_code == 401
    login()
    assert client.get("/history?person_id=1%20OR%201=1").status_code == 400


def test_stored_xss_is_encoded(login, client):
    login()
    response = client.post("/persons", data={"name": '<script>alert("x")</script>', "kind": "guest", "csrf_token": csrf_token(client, "/persons")})
    assert response.status_code == 302
    page = client.get("/persons")
    assert b"<script>" not in page.data
    assert b"&lt;script&gt;" in page.data
    assert "script-src 'none'" in page.headers["Content-Security-Policy"]


def test_cookie_flags(login):
    cookie = login().headers.get("Set-Cookie")
    assert "HttpOnly" in cookie and "SameSite=Strict" in cookie


def test_no_open_redirect(login, client, credentials):
    response = client.post("/login?next=https://example.org", data={"username": "employee", "password": credentials[0], "csrf_token": csrf_token(client, "/login")})
    assert response.headers["Location"] == "/dashboard"


def test_login_throttle(login):
    for _ in range(10):
        assert login(password="wrong").status_code == 401
    assert login().status_code == 429


def test_audit_actions_do_not_contain_passwords(login, client, app, credentials):
    login(password="wrong")
    login()
    client.get("/admin/users")
    client.post("/logout", data={"csrf_token": csrf_token(client, "/dashboard")})
    with app.app_context():
        entries = db.session.scalars(select(AuditLog)).all()
        assert {"LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT", "AUTHORIZATION_DENIED"} <= {entry.action for entry in entries}
        assert all(credentials[0] not in entry.details and "wrong" not in entry.details for entry in entries)


@pytest.mark.parametrize("query", ["page=-1", "start=bad", "start=2026-10-03&end=2026-01-01", "event_type=BAD", "sort=password_hash"])
def test_history_rejects_bad_filters(login, client, query):
    login()
    assert client.get("/history?" + query).status_code == 400


def test_large_request_and_safe_error_page(client):
    assert client.post("/login", data={"password": "x" * 20000}).status_code == 413
    response = client.get("/missing")
    assert response.status_code == 404
    assert b"Traceback" not in response.data and b"C:\\Users" not in response.data
