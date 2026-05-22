# -*- coding: utf-8 -*-
"""
Phase 5.7b — Bulk update contract tests.

DB integration tests cho:
  POST /api/members/bulk-update-branch
  POST /api/members/bulk-update-sll

Tập trung auth gates + DB state changes.
Không thay đổi production code.
"""
import csv
import io
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────


def _commit(cursor):
    conn = getattr(cursor, "_connection", None)
    if conn is None:
        raise AssertionError("cursor does not expose _connection")
    conn.commit()


def _patch_pw(monkeypatch, pw="testpw"):
    monkeypatch.setattr("services.members_service.get_members_password", lambda: pw)
    return pw


def _authed_client(db_client):
    with db_client.session_transaction() as sess:
        sess["members_gate_ok"] = True
        sess["members_gate_user"] = "pytest"
    return db_client


def _seed_person(cursor, person_id="P-1-1", full_name="Test Person"):
    _commit(cursor)
    cursor.execute(
        "INSERT INTO persons (person_id, full_name, generation_level, status) VALUES (%s, %s, %s, %s)",
        (person_id, full_name, 1, "Còn sống"),
    )
    _commit(cursor)


def _ensure_branch_name_col(cursor):
    """ALTER TABLE persons ADD COLUMN branch_name (idempotent, DDL auto-commits in MySQL)."""
    _commit(cursor)
    cursor.execute(
        """
        SELECT COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
          AND COLUMN_NAME = 'branch_name' LIMIT 1
        """
    )
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE persons ADD COLUMN branch_name VARCHAR(100) NULL")
    _commit(cursor)


def _ensure_sll_columns(cursor):
    """
    Thêm các cột mà apply_person_members_update_core hard-code trong SELECT
    nhưng không có trong reset_schema_tbqc.sql.
    """
    _commit(cursor)
    needed = {
        "biography": "TEXT NULL",
        "academic_rank": "TEXT NULL",
        "academic_degree": "TEXT NULL",
        "phone": "VARCHAR(50) NULL",
        "email": "VARCHAR(255) NULL",
    }
    cursor.execute(
        """
        SELECT COLUMN_NAME FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
          AND COLUMN_NAME IN ({})
        """.format(", ".join(f"'{c}'" for c in needed))
    )
    existing = {row[0] for row in cursor.fetchall()}
    for col, typedef in needed.items():
        if col not in existing:
            cursor.execute(f"ALTER TABLE persons ADD COLUMN {col} {typedef}")
    _commit(cursor)


def _get_field(cursor, person_id, field):
    _commit(cursor)
    cursor.execute(f"SELECT {field} FROM persons WHERE person_id = %s", (person_id,))
    row = cursor.fetchone()
    _commit(cursor)
    return row[0] if row else None


def _make_branch_csv(person_id, branch_name="Một"):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Nhánh"])
    writer.writerow([person_id, branch_name])
    return io.BytesIO(buf.getvalue().encode("utf-8-sig"))


def _make_sll_csv(person_id, full_name):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "Họ và tên"])
    writer.writerow([person_id, full_name])
    return io.BytesIO(buf.getvalue().encode("utf-8-sig"))


def _post_bulk_branch(client, file_bytes, filename="branch.csv", password="testpw"):
    return client.post(
        "/api/members/bulk-update-branch",
        data={"password": password, "file": (file_bytes, filename, "text/csv")},
        content_type="multipart/form-data",
    )


def _post_bulk_sll(client, file_bytes, filename="sll.csv", password="testpw"):
    return client.post(
        "/api/members/bulk-update-sll",
        data={"password": password, "file": (file_bytes, filename, "text/csv")},
        content_type="multipart/form-data",
    )


# ── bulk-update-branch: auth gates ────────────────────────────────────────────


@pytest.mark.db_integration
def test_branch_no_session_returns_401(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    resp = _post_bulk_branch(db_client, _make_branch_csv("P-1-1"))
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_branch_wrong_password_returns_403(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    _authed_client(db_client)
    resp = _post_bulk_branch(db_client, _make_branch_csv("P-1-1"), password="wrong")
    assert resp.status_code == 403
    assert resp.get_json()["success"] is False


# ── bulk-update-branch: file validation ───────────────────────────────────────


@pytest.mark.db_integration
def test_branch_no_file_returns_400(db_client, test_db_cursor, monkeypatch):
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    resp = db_client.post(
        "/api/members/bulk-update-branch",
        data={"password": pw},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_branch_wrong_extension_returns_400(db_client, test_db_cursor, monkeypatch):
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    resp = _post_bulk_branch(db_client, io.BytesIO(b"data"), filename="doc.txt", password=pw)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_branch_missing_columns_returns_400(db_client, test_db_cursor, monkeypatch):
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    bad_csv = io.BytesIO(b"Name,Value\nfoo,bar")
    resp = _post_bulk_branch(db_client, bad_csv, password=pw)
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── bulk-update-branch: happy path ────────────────────────────────────────────


@pytest.mark.db_integration
def test_branch_updates_branch_name_in_db(db_client, test_db_cursor, monkeypatch):
    """Upload CSV hợp lệ → branch_name được cập nhật trong DB."""
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    _ensure_branch_name_col(test_db_cursor)
    _seed_person(test_db_cursor, "P-7-1")

    resp = _post_bulk_branch(db_client, _make_branch_csv("P-7-1", "Một"), password=pw)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["updated_count"] == 1
    assert body["error_count"] == 0
    assert _get_field(test_db_cursor, "P-7-1", "branch_name") == "Một"


@pytest.mark.db_integration
def test_branch_skips_nonexistent_person(db_client, test_db_cursor, monkeypatch):
    """Person không tồn tại trong DB → updated_count=0, success=True (silent skip)."""
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    _ensure_branch_name_col(test_db_cursor)

    resp = _post_bulk_branch(db_client, _make_branch_csv("P-99-99"), password=pw)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["updated_count"] == 0


# ── bulk-update-sll: auth gates ───────────────────────────────────────────────


@pytest.mark.db_integration
def test_sll_no_session_returns_401(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    resp = _post_bulk_sll(db_client, _make_sll_csv("P-1-1", "Some Name"))
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


@pytest.mark.db_integration
def test_sll_wrong_password_returns_403(db_client, test_db_cursor, monkeypatch):
    _patch_pw(monkeypatch)
    _authed_client(db_client)
    resp = _post_bulk_sll(db_client, _make_sll_csv("P-1-1", "Some Name"), password="wrong")
    assert resp.status_code == 403
    assert resp.get_json()["success"] is False


# ── bulk-update-sll: feature flag ─────────────────────────────────────────────


@pytest.mark.db_integration
def test_sll_disabled_returns_503(db_client, test_db_cursor, monkeypatch):
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    import blueprints.members_portal as mp
    monkeypatch.setattr(mp, "BULK_UPDATE_SLL_ENABLED", False)
    resp = _post_bulk_sll(db_client, _make_sll_csv("P-1-1", "Some Name"), password=pw)
    assert resp.status_code == 503
    assert resp.get_json()["success"] is False


# ── bulk-update-sll: file validation ──────────────────────────────────────────


@pytest.mark.db_integration
def test_sll_no_file_returns_400(db_client, test_db_cursor, monkeypatch):
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    resp = db_client.post(
        "/api/members/bulk-update-sll",
        data={"password": pw},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False


# ── bulk-update-sll: happy path ───────────────────────────────────────────────


@pytest.mark.db_integration
def test_sll_updates_full_name_in_db(db_client, test_db_cursor, monkeypatch):
    """Upload CSV với full_name mới → DB được cập nhật."""
    pw = _patch_pw(monkeypatch)
    _authed_client(db_client)
    _ensure_sll_columns(test_db_cursor)
    _seed_person(test_db_cursor, "P-8-1", "Old Name")

    resp = _post_bulk_sll(db_client, _make_sll_csv("P-8-1", "New Name"), password=pw)

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["updated_count"] == 1
    assert body["error_count"] == 0
    assert _get_field(test_db_cursor, "P-8-1", "full_name") == "New Name"
