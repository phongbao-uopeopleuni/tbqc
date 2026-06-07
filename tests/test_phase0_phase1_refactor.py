from unittest.mock import MagicMock

from flask import jsonify

from folder_py.genealogy_tree import build_tree
from services import person_service


def _patch_person_handler(monkeypatch, handler_name):
    def _handler(person_id):
        return jsonify({"handler": handler_name, "person_id": person_id})

    monkeypatch.setattr(person_service, handler_name, _handler)


def test_legacy_person_routes_accept_string_ids(flask_app, monkeypatch):
    _patch_person_handler(monkeypatch, "update_person")
    _patch_person_handler(monkeypatch, "sync_person")
    _patch_person_handler(monkeypatch, "delete_person")

    client = flask_app.test_client()

    update_resp = client.put("/api/person/P-7-654", json={"full_name": "Updated"})
    sync_resp = client.post("/api/person/P-7-654/sync", json={})
    delete_resp = client.delete("/api/person/P-7-654", json={})

    assert update_resp.status_code == 200
    assert update_resp.get_json() == {"handler": "update_person", "person_id": "P-7-654"}

    assert sync_resp.status_code == 200
    assert sync_resp.get_json() == {"handler": "sync_person", "person_id": "P-7-654"}

    assert delete_resp.status_code == 200
    assert delete_resp.get_json() == {"handler": "delete_person", "person_id": "P-7-654"}


def test_apply_parent_relationship_mutations_blank_parent_deletes_only_that_relation():
    cursor = MagicMock()

    person_service._apply_parent_relationship_mutations(
        cursor,
        "P-2-1",
        {"father_name": ""},
    )

    assert cursor.execute.call_count == 1
    sql, params = cursor.execute.call_args[0]
    assert "DELETE FROM relationships" in sql
    assert params == ("P-2-1", "father")


def test_apply_parent_relationship_mutations_rejects_unmappable_parent_without_deleting(monkeypatch):
    cursor = MagicMock()
    monkeypatch.setattr(person_service, "find_person_by_name", lambda *_args, **_kwargs: None)

    try:
        person_service._apply_parent_relationship_mutations(
            cursor,
            "P-2-1",
            {"father_name": "Missing Parent"},
        )
    except ValueError as exc:
        assert "father_name" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unmappable parent")

    cursor.execute.assert_not_called()


def test_apply_parent_relationship_mutations_replaces_existing_parent(monkeypatch):
    cursor = MagicMock()
    monkeypatch.setattr(person_service, "find_person_by_name", lambda *_args, **_kwargs: "P-1-9")

    person_service._apply_parent_relationship_mutations(
        cursor,
        "P-2-1",
        {"father_name": "Father New"},
    )

    assert cursor.execute.call_count == 2
    delete_sql, delete_params = cursor.execute.call_args_list[0][0]
    insert_sql, insert_params = cursor.execute.call_args_list[1][0]
    assert "DELETE FROM relationships" in delete_sql
    assert delete_params == ("P-2-1", "father")
    assert "INSERT INTO relationships" in insert_sql
    assert insert_params == ("P-2-1", "P-1-9", "father")


def test_apply_parent_relationship_mutations_uses_direct_father_id():
    """father_id (person_id trực tiếp) được dùng ưu tiên, không gọi find_person_by_name."""
    cursor = MagicMock()
    # SELECT validate person exists → trả về 1 row
    cursor.fetchone.return_value = {"person_id": "P-1-5"}

    person_service._apply_parent_relationship_mutations(
        cursor,
        "P-2-1",
        {"father_id": "P-1-5"},
    )

    # SELECT validate + DELETE + INSERT = 3
    assert cursor.execute.call_count == 3
    validate_sql = cursor.execute.call_args_list[0][0][0]
    assert "SELECT person_id FROM persons WHERE person_id" in validate_sql
    delete_sql = cursor.execute.call_args_list[1][0][0]
    assert "DELETE FROM relationships" in delete_sql
    insert_sql, insert_params = cursor.execute.call_args_list[2][0]
    assert "INSERT INTO relationships" in insert_sql
    assert insert_params == ("P-2-1", "P-1-5", "father")


def test_apply_parent_relationship_mutations_direct_father_id_not_found_raises():
    """father_id trực tiếp nhưng không tồn tại trong DB → raise ValueError, không ghi."""
    cursor = MagicMock()
    cursor.fetchone.return_value = None  # person không tồn tại

    try:
        person_service._apply_parent_relationship_mutations(
            cursor,
            "P-2-1",
            {"father_id": "P-9-999"},
        )
    except ValueError as exc:
        assert "father_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing direct person_id")

    # Chỉ có SELECT validate, không DELETE/INSERT
    assert cursor.execute.call_count == 1


def test_apply_parent_relationship_mutations_fm_id_passed_to_name_lookup(monkeypatch):
    """fm_id trong payload được truyền vào find_person_by_name để disambiguation."""
    cursor = MagicMock()
    captured = {}

    def fake_find(cur, name, generation_level=None, fm_id=None):
        captured['fm_id'] = fm_id
        return "P-3-10"

    monkeypatch.setattr(person_service, "find_person_by_name", fake_find)

    person_service._apply_parent_relationship_mutations(
        cursor,
        "P-4-1",
        {"father_name": "Nguyễn Văn Trùng", "fm_id": "fm_99"},
    )

    assert captured['fm_id'] == "fm_99"
    # DELETE + INSERT
    assert cursor.execute.call_count == 2


def test_apply_parent_relationship_mutations_blank_direct_id_deletes_relation():
    """father_id = '' (blank) → xóa relation, không raise."""
    cursor = MagicMock()

    person_service._apply_parent_relationship_mutations(
        cursor,
        "P-2-1",
        {"father_id": ""},
    )

    assert cursor.execute.call_count == 1
    sql, params = cursor.execute.call_args[0]
    assert "DELETE FROM relationships" in sql
    assert params == ("P-2-1", "father")


def test_build_tree_includes_parent_refs_and_family_group_key():
    payload = build_tree(
        "P-1-1",
        {
            "P-1-1": {
                "full_name": "Father",
                "generation_level": 1,
                "gender": "Nam",
            },
            "P-2-1": {
                "full_name": "Child",
                "generation_level": 2,
                "gender": "Nam",
                "father_id": "P-1-1",
                "mother_id": "P-1-2",
                "father_name": "Father",
                "mother_name": "Mother",
                "father_mother_id": "FM-LEGACY",
                "family_group_key": "P-1-1|P-1-2",
            },
        },
        {"P-1-1": ["P-2-1"]},
        1,
        3,
    )

    child = payload["children"][0]
    assert child["father_id"] == "P-1-1"
    assert child["mother_id"] == "P-1-2"
    assert child["family_group_key"] == "P-1-1|P-1-2"
