from sqlalchemy import func, select

from src.backend.models import AuditLog, GalleryEvent, User, db
from src.backend.services import current_state
from tests.conftest import csrf_token


def test_successful_login_and_dashboard(login, client):
    assert login().status_code == 302
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"employee" in response.data


def test_incorrect_password(login):
    response = login(password="deliberately-incorrect")
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_protected_page_without_login(client):
    assert client.get("/dashboard").status_code == 302
    assert "/login" in client.get("/dashboard").headers["Location"]


def test_employee_denied_admin(login, client):
    login()
    assert client.get("/admin/users").status_code == 403


def test_admin_allowed_admin(login, client):
    login("admin")
    assert client.get("/admin/users").status_code == 200


def test_password_is_hashed(app, credentials):
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == "admin"))
        assert user.password_hash != credentials[0]
        assert user.password_hash.startswith("scrypt:")
        assert user.check_password(credentials[0])


def test_complete_movement_cycle(login, move, app, client):
    login()
    for event, room in [("ENTER_GALLERY", None), ("ENTER_ROOM", 1), ("LEAVE_ROOM", 1),
                        ("ENTER_ROOM", 2), ("LEAVE_ROOM", 2), ("LEAVE_GALLERY", None)]:
        assert move(event, room_id=room).status_code == 302
    with app.app_context():
        assert current_state(db.session) == {}
        assert db.session.scalar(select(func.count()).select_from(GalleryEvent)) == 6
        assert db.session.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == "GALLERY_EVENT")) == 6
    assert b"ENTER_GALLERY" in client.get("/history").data


def test_occupancy_counts_room_and_lobby(login, move, client, app):
    login()
    move("ENTER_GALLERY")
    move("ENTER_GALLERY", person_id=2)
    move("ENTER_ROOM", room_id=1)
    assert b"2 people in the gallery" in client.get("/dashboard").data
    with app.app_context():
        assert current_state(db.session) == {1: 1, 2: None}


def test_history_filters_and_empty_results(login, move, client):
    login()
    move("ENTER_GALLERY")
    move("ENTER_ROOM", room_id=1)
    response = client.get("/history?room_id=1&person_id=1&event_type=ENTER_ROOM&start=2000-01-01&end=2099-01-01")
    assert response.status_code == 200
    assert b"Paintings" in response.data
    assert b"No matching events" in client.get("/history?person_id=2").data


def test_add_person(login, client):
    login()
    response = client.post("/persons", data={"name": "New Visitor", "kind": "guest", "csrf_token": csrf_token(client, "/persons")})
    assert response.status_code == 302
    assert b"New Visitor" in client.get("/persons").data


def test_admin_creates_and_disables_user(login, client, app, credentials):
    login("admin")
    response = client.post("/admin/users", data={"username": "new_employee", "password": credentials[0],
                                                "role": "employee", "csrf_token": csrf_token(client, "/admin/users")})
    assert response.status_code == 302
    with app.app_context():
        user_id = db.session.scalar(select(User.id).where(User.username == "new_employee"))
    response = client.post(f"/admin/users/{user_id}", data={"role": "guest", "active": "0", "csrf_token": csrf_token(client, "/admin/users")})
    assert response.status_code == 302
    with app.app_context():
        user = db.session.get(User, user_id)
        assert user.role == "guest" and not user.active
    assert b"USER_UPDATED" in client.get("/admin/audit").data


def test_cli_init_and_seed_preserve_data(app, monkeypatch, credentials):
    for role in ("ADMIN", "EMPLOYEE", "GUEST"):
        monkeypatch.setenv(f"SEED_{role}_PASSWORD", credentials[0])
    runner = app.test_cli_runner()
    assert runner.invoke(args=["init-db"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    assert runner.invoke(args=["seed"]).exit_code == 0
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(User)) == 7
