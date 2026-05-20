import json
import os
import pathlib

import pytest


FIXTURE_DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "contract"
WRITE_FIXTURES = os.environ.get("TBQC_WRITE_FIXTURES", "").lower() in {"1", "true", "yes"}


def _assert_json_fixture(name, payload):
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / name
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if WRITE_FIXTURES:
        path.write_text(text, encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8")) == payload


def _commit(cursor):
    connection = getattr(cursor, "_connection", None)
    if connection is None:
        raise AssertionError("mysql.connector cursor does not expose _connection")
    connection.commit()


def _seed_contract_data(cursor):
    cursor.execute("DELETE FROM generations")
    cursor.execute("INSERT INTO generations (generation_number, description) VALUES (1, 'Doi 1'), (2, 'Doi 2')")
    cursor.execute(
        """
        INSERT INTO persons (
            person_id, full_name, alias, gender, status, generation_level,
            home_town, nationality, religion, place_of_death, grave_info,
            contact, social, occupation, education, events, titles,
            blood_type, genetic_disease, note, father_mother_id
        ) VALUES
            ('P-1-1', 'To Tien', 'Ong To', 'Nam', 'Con song', 1,
             'Hue', 'Viet Nam', 'Khong', NULL, 'Mo A',
             '0901', 'fb/to-tien', 'Truong toc', 'Nho hoc', 'Lap dong ho', 'Cuu pham',
             'A', NULL, 'Goc', 'FM-1'),
            ('P-1-2', 'Phoi Nguu', NULL, 'Nu', 'Con song', 1,
             'Hue', 'Viet Nam', 'Khong', NULL, 'Mo B',
             '0902', NULL, 'Noi tro', NULL, NULL, NULL,
             'B', NULL, NULL, 'FM-1'),
            ('P-2-1', 'Nguoi Mau', 'Con Truong', 'Nam', 'Da mat', 2,
             'Da Nang', 'Viet Nam', 'Khong', 'Da Nang', 'Mo C',
             '0903', NULL, 'Ky su', 'Dai hoc', 'Hoc hanh', NULL,
             'O', NULL, 'Nhan vat test', 'FM-1')
        """
    )
    cursor.execute(
        """
        INSERT INTO relationships (parent_id, child_id, relation_type) VALUES
            ('P-1-1', 'P-2-1', 'father'),
            ('P-1-2', 'P-2-1', 'mother')
        """
    )
    cursor.execute(
        """
        INSERT INTO marriages (person_id, spouse_person_id, status, note)
        VALUES ('P-1-1', 'P-1-2', 'Dang ket hon', 'Seed marriage')
        """
    )
    cursor.execute("DROP VIEW IF EXISTS v_family_tree")
    cursor.execute(
        """
        CREATE VIEW v_family_tree AS
        SELECT
            person_id,
            full_name,
            generation_level AS generation_number
        FROM persons
        """
    )
    _commit(cursor)


def _members_session(client):
    with client.session_transaction() as session:
        session["members_gate_ok"] = True
        session["members_gate_user"] = "pytest"


@pytest.mark.db_integration
def test_api_health_contract(db_client, test_db_cursor):
    _seed_contract_data(test_db_cursor)
    response = db_client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    payload = {
        "server": data["server"],
        "database": data["database"],
        "blueprints_registered": data["blueprints_registered"],
        "db_config": {
            "database_non_empty": bool(data["db_config"].get("database")),
            "host_non_empty": bool(data["db_config"].get("host")),
            "password_set": data["db_config"].get("password_set"),
            "port_present": data["db_config"].get("port") is not None,
            "user_non_empty": bool(data["db_config"].get("user")),
        },
        "stats": data["stats"],
    }
    _assert_json_fixture("api_health.json", payload)


@pytest.mark.db_integration
def test_api_persons_contract(db_client, test_db_cursor):
    _seed_contract_data(test_db_cursor)
    response = db_client.get("/api/persons?paginated=1&page=1&per_page=2")
    assert response.status_code == 200
    data = response.get_json()
    payload = {
        "page": data["page"],
        "per_page": data["per_page"],
        "total": data["total"],
        "pages": data["pages"],
        "items": [
            {
                "person_id": item["person_id"],
                "full_name": item["full_name"],
                "generation_level": item["generation_level"],
                "father_name": item["father_name"],
                "mother_name": item["mother_name"],
                "children": item["children"],
                "spouse": item["spouse"],
            }
            for item in data["items"]
        ],
    }
    _assert_json_fixture("api_persons.json", payload)


@pytest.mark.db_integration
def test_api_person_single_contract(db_client, test_db_cursor):
    _seed_contract_data(test_db_cursor)
    response = db_client.get("/api/person/P-1-1")
    assert response.status_code == 200
    data = response.get_json()
    payload = {
        "person_id": data["person_id"],
        "full_name": data["full_name"],
        "generation_number": data["generation_number"],
        "father_id": data["father_id"],
        "mother_id": data["mother_id"],
        "spouse": data["spouse"],
        "children": [
            {
                "person_id": child["person_id"],
                "full_name": child["full_name"],
                "generation_number": child["generation_number"],
            }
            for child in data["children"]
        ],
        "marriages": [
            {
                "marriage_id": row["marriage_id"],
                "spouse_id": row["spouse_id"],
                "spouse_name": row["spouse_name"],
                "marriage_status": row["marriage_status"],
            }
            for row in data["marriages"]
        ],
    }
    _assert_json_fixture("api_person_single.json", payload)


@pytest.mark.db_integration
def test_api_members_contract(db_client, test_db_cursor):
    _seed_contract_data(test_db_cursor)
    _members_session(db_client)
    response = db_client.get("/api/members")
    assert response.status_code == 200
    data = response.get_json()
    payload = {
        "success": data["success"],
        "count": len(data["data"]),
        "items": [
            {
                "person_id": item["person_id"],
                "full_name": item["full_name"],
                "generation_number": item["generation_number"],
                "father_name": item["father_name"],
                "mother_name": item["mother_name"],
                "spouses": item["spouses"],
                "children": item["children"],
            }
            for item in data["data"]
        ],
    }
    _assert_json_fixture("api_members.json", payload)


@pytest.mark.db_integration
def test_api_family_tree_contract(db_client, test_db_cursor):
    _seed_contract_data(test_db_cursor)
    response = db_client.get("/api/family-tree")
    assert response.status_code == 200
    data = response.get_json()
    payload = [
        {
            "person_id": row["person_id"],
            "full_name": row["full_name"],
            "generation_number": row["generation_number"],
        }
        for row in data
    ]
    _assert_json_fixture("api_family_tree.json", payload)
