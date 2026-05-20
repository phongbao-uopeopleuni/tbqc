import json
import pathlib

import pytest

from auth import hash_password


FIXTURE_PATH = pathlib.Path(__file__).resolve().parent / "fixtures" / "audit" / "expected_actions.json"
EXPECTED_ACTIONS = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _commit(cursor):
    connection = getattr(cursor, "_connection", None)
    if connection is None:
        raise AssertionError("mysql.connector cursor does not expose _connection")
    connection.commit()


def _insert_admin_user(cursor, user_id=1, username="admin.seed", password="Secret123!"):
    cursor.execute(
        """
        INSERT INTO users (user_id, username, password_hash, full_name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, 'admin', TRUE)
        """,
        (user_id, username, hash_password(password), "Admin Seed", "admin@example.test"),
    )
    _commit(cursor)
    return {"user_id": user_id, "username": username, "password": password}


def _insert_regular_user(cursor, user_id=2, username="user.seed"):
    cursor.execute(
        """
        INSERT INTO users (user_id, username, password_hash, full_name, email, role, is_active)
        VALUES (%s, %s, %s, %s, %s, 'user', TRUE)
        """,
        (user_id, username, hash_password("UserPass123!"), "User Seed", "user@example.test"),
    )
    _commit(cursor)
    return user_id


def _insert_people(cursor):
    cursor.execute(
        """
        INSERT INTO persons (
            person_id, full_name, alias, gender, status, generation_level, home_town,
            nationality, religion, place_of_death, grave_info, contact, social,
            occupation, education, events, titles, blood_type, genetic_disease, note, father_mother_id
        ) VALUES
            ('P-1-1', 'To Tien', NULL, 'Nam', 'Con song', 1, 'Hue', 'Viet Nam', 'Khong', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'FM-1'),
            ('P-1-2', 'Phoi Nguu', NULL, 'Nu', 'Con song', 1, 'Hue', 'Viet Nam', 'Khong', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'FM-1')
        """
    )
    _commit(cursor)


def _set_admin_session(client, user_id=1):
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
        session["_id"] = "step6-audit-session"


def _count_action(cursor, action):
    _commit(cursor)
    cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE action = %s", (action,))
    return cursor.fetchone()[0]


def _find_action(cursor, action):
    _commit(cursor)
    cursor.execute(
        """
        SELECT action, target_type, target_id
        FROM activity_logs
        WHERE action = %s
        ORDER BY log_id DESC
        LIMIT 1
        """,
        (action,),
    )
    return cursor.fetchone()


@pytest.mark.db_integration
def test_login_success_and_failure_emit_audit(db_client, test_db_cursor):
    admin = _insert_admin_user(test_db_cursor)

    response_fail = db_client.post("/api/login", data={"username": admin["username"], "password": "wrong-password"})
    assert response_fail.status_code == 401
    assert _count_action(test_db_cursor, "LOGIN_FAILED") == 1

    response_ok = db_client.post("/api/login", data={"username": admin["username"], "password": admin["password"]})
    assert response_ok.status_code == 200
    assert _count_action(test_db_cursor, "LOGIN") == 1


@pytest.mark.db_integration
def test_update_and_delete_user_emit_audit(db_client, test_db_cursor):
    _insert_admin_user(test_db_cursor)
    target_user_id = _insert_regular_user(test_db_cursor, user_id=2, username="editor.seed")
    _set_admin_session(db_client)

    response_update = db_client.put(
        f"/admin/api/users/{target_user_id}",
        json={"full_name": "Editor Updated", "email": "updated@example.test", "role": "user"},
    )
    assert response_update.status_code == 200
    assert _count_action(test_db_cursor, "UPDATE_USER_ROLE") == 1

    response_delete = db_client.delete(f"/admin/api/users/{target_user_id}")
    assert response_delete.status_code == 200
    delete_row = _find_action(test_db_cursor, "DELETE_USER")
    assert delete_row is not None
    assert str(delete_row[2]) == str(target_user_id)


@pytest.mark.db_integration
def test_marriage_create_and_delete_emit_audit(db_client, test_db_cursor):
    _insert_admin_user(test_db_cursor)
    _insert_people(test_db_cursor)
    _set_admin_session(db_client)

    response_create = db_client.post(
        "/api/person/P-1-1/spouses",
        json={"spouse_person_id": "P-1-2", "status": "Dang ket hon", "note": "Seed marriage"},
    )
    assert response_create.status_code == 201
    marriage_id = response_create.get_json()["marriage_id"]
    create_row = _find_action(test_db_cursor, "CREATE_SPOUSE")
    assert create_row is not None
    assert str(create_row[2]) == str(marriage_id)

    response_delete = db_client.delete(f"/api/marriages/{marriage_id}")
    assert response_delete.status_code == 200
    delete_row = _find_action(test_db_cursor, "DELETE_SPOUSE")
    assert delete_row is not None
    assert str(delete_row[2]) == str(marriage_id)


@pytest.mark.db_integration
def test_marriage_update_emits_audit(db_client, test_db_cursor):
    _insert_admin_user(test_db_cursor)
    _insert_people(test_db_cursor)
    _set_admin_session(db_client)

    response_create = db_client.post(
        "/api/person/P-1-1/spouses",
        json={"spouse_person_id": "P-1-2", "status": "Dang ket hon", "note": "Seed marriage"},
    )
    assert response_create.status_code == 201
    marriage_id = response_create.get_json()["marriage_id"]

    response_update = db_client.put(f"/api/marriages/{marriage_id}", json={"status": "Da ly di", "note": "Updated"})
    assert response_update.status_code == 200
    update_row = _find_action(test_db_cursor, "UPDATE_SPOUSE")
    assert update_row is not None
    assert str(update_row[2]) == str(marriage_id)


@pytest.mark.db_integration
def test_create_user_emits_audit(db_client, test_db_cursor):
    _insert_admin_user(test_db_cursor)
    _set_admin_session(db_client)

    response = db_client.post(
        "/admin/api/users",
        json={
            "username": "new.user",
            "password": "Secret123!",
            "password_confirm": "Secret123!",
            "full_name": "New User",
            "email": "new.user@example.test",
            "role": "user",
        },
    )
    assert response.status_code == 200
    assert _count_action(test_db_cursor, "CREATE_USER") == 1


def test_expected_actions_fixture_tracks_step6_scope():
    assert EXPECTED_ACTIONS["implemented"] == [
        "LOGIN",
        "LOGIN_FAILED",
        "CREATE_USER",
        "UPDATE_USER_ROLE",
        "DELETE_USER",
        "CREATE_SPOUSE",
        "UPDATE_SPOUSE",
        "DELETE_SPOUSE",
    ]
    assert "CREATE_USER" not in EXPECTED_ACTIONS["known_gaps"]
    assert "UPDATE_SPOUSE" not in EXPECTED_ACTIONS["known_gaps"]
