import pytest
from unittest.mock import MagicMock

from services.person_helpers import (
    normalize_search_query,
    split_semicolon_values,
    find_person_by_name,
    load_relationship_data,
    get_or_create_location,
    get_or_create_generation,
    get_or_create_branch,
)
from services import person_service


@pytest.fixture
def mock_cursor():
    return MagicMock()


def test_normalize_search_query_empty_values():
    assert normalize_search_query(None) == ("", [])
    assert normalize_search_query("") == ("", [])


def test_normalize_search_query_keeps_trimmed_query_and_person_id_variants():
    normalized, patterns = normalize_search_query(" p-7-654 ")

    assert normalized == "p-7-654"
    assert patterns == [
        "%p-7-654%",
        "%P-7-654%",
        "%p-7-654%",
    ]


def test_normalize_search_query_generation_number_pair():
    normalized, patterns = normalize_search_query("7-654")

    assert normalized == "7-654"
    assert patterns == ["%P-7-654%", "%p-7-654%", "%7-654%"]


def test_normalize_search_query_numeric_suffix():
    normalized, patterns = normalize_search_query("654")

    assert normalized == "654"
    assert patterns == ["%-654%", "%654%"]


def test_split_semicolon_values_trims_and_drops_empty_parts():
    assert split_semicolon_values(" A ; ;B;  C  ") == ["A", "B", "C"]
    assert split_semicolon_values(None) == []


def test_person_service_keeps_legacy_helper_aliases():
    assert person_service.normalize_search_query is normalize_search_query
    assert person_service._split_semicolon_values is split_semicolon_values
    assert person_service.find_person_by_name is find_person_by_name
    assert person_service.get_or_create_branch is get_or_create_branch
    assert person_service.get_or_create_location is get_or_create_location
    assert person_service.get_or_create_generation is get_or_create_generation


# ---------------------------------------------------------------------------
# find_person_by_name
# ---------------------------------------------------------------------------


def test_find_person_by_name_blank_name_skips_db(mock_cursor):
    from services.person_helpers import find_person_by_name

    assert find_person_by_name(mock_cursor, "") is None
    assert find_person_by_name(mock_cursor, "  ") is None
    assert find_person_by_name(mock_cursor, None) is None
    mock_cursor.execute.assert_not_called()


def test_find_person_by_name_returns_id_from_dict_row(mock_cursor):
    from services.person_helpers import find_person_by_name

    mock_cursor.fetchone.return_value = {"person_id": 42}
    assert find_person_by_name(mock_cursor, "Nguyễn Văn A") == 42


def test_find_person_by_name_returns_id_from_tuple_row(mock_cursor):
    from services.person_helpers import find_person_by_name

    mock_cursor.fetchone.return_value = (99,)
    assert find_person_by_name(mock_cursor, "Trần Thị B") == 99


def test_find_person_by_name_returns_none_when_not_found(mock_cursor):
    from services.person_helpers import find_person_by_name

    mock_cursor.fetchone.return_value = None
    assert find_person_by_name(mock_cursor, "Unknown") is None


def test_find_person_by_name_includes_generation_filter_in_query(mock_cursor):
    from services.person_helpers import find_person_by_name

    mock_cursor.fetchone.return_value = {"person_id": 7}
    find_person_by_name(mock_cursor, "Lê Văn C", generation_id=3)
    sql = mock_cursor.execute.call_args[0][0]
    assert "generation_id" in sql


def test_find_person_by_name_no_generation_filter_omits_generation_clause(mock_cursor):
    from services.person_helpers import find_person_by_name

    mock_cursor.fetchone.return_value = {"person_id": 5}
    find_person_by_name(mock_cursor, "Phạm Thị D")
    sql = mock_cursor.execute.call_args[0][0]
    assert "generation_id" not in sql


def test_person_service_keeps_load_relationship_data_alias():
    assert person_service.load_relationship_data is load_relationship_data


# ---------------------------------------------------------------------------
# load_relationship_data
# ---------------------------------------------------------------------------


def test_load_relationship_data_returns_expected_keys(mock_cursor):
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    result = load_relationship_data(mock_cursor)
    expected = {
        'spouse_data_from_table', 'spouse_data_from_marriages', 'spouse_data_from_csv',
        'parent_data', 'parent_ids_map', 'children_map', 'siblings_map', 'person_name_map',
        'children_text_map', 'siblings_text_map', 'parent_text_map',
    }
    assert set(result.keys()) == expected


def test_load_relationship_data_empty_db_returns_empty_dicts(mock_cursor):
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    result = load_relationship_data(mock_cursor)
    assert result['spouse_data_from_table'] == {}
    assert result['spouse_data_from_marriages'] == {}
    assert result['children_map'] == {}
    assert result['siblings_map'] == {}


def test_load_relationship_data_populates_parent_data_from_relationships(mock_cursor):
    # fetchone=None: ssc absent; fetchall order: marriages, relationships, person_name_map
    fetch_seq = [
        [],
        [
            {'child_id': 'p-1-1', 'parent_id': 'p-0-1', 'relation_type': 'father',
             'parent_name': 'Nguyễn Văn A', 'child_name': 'Nguyễn Văn B'},
        ],
        [],
    ]
    fetch_iter = iter(fetch_seq)
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.side_effect = lambda: next(fetch_iter, [])
    result = load_relationship_data(mock_cursor)
    assert result['parent_data'].get('p-1-1', {}).get('father_name') == 'Nguyễn Văn A'


def test_load_relationship_data_builds_children_map_from_relationships(mock_cursor):
    # fetchall order: marriages, relationships, person_name_map
    fetch_seq = [
        [],
        [
            {'child_id': 'p-1-1', 'parent_id': 'p-0-1', 'relation_type': 'father',
             'parent_name': 'Cha A', 'child_name': 'Con B'},
        ],
        [],
    ]
    fetch_iter = iter(fetch_seq)
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.side_effect = lambda: next(fetch_iter, [])
    result = load_relationship_data(mock_cursor)
    assert 'Con B' in result['children_map'].get('p-0-1', [])


def test_load_relationship_data_deduplicates_spouse_from_marriages(mock_cursor):
    # fetchone=None means ssc table absent → no ssc fetchall calls
    # fetchall call order: marriages, relationships, person_name_map
    fetch_seq = [
        [
            {'person_id': 'p-1-1', 'spouse_person_id': 'p-1-2', 'spouse_name': 'Vợ A'},
            {'person_id': 'p-1-1', 'spouse_person_id': 'p-1-2', 'spouse_name': 'Vợ A'},
        ],
        [],
        [],
    ]
    fetch_iter = iter(fetch_seq)
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.side_effect = lambda: next(fetch_iter, [])
    result = load_relationship_data(mock_cursor)
    assert result['spouse_data_from_marriages'].get('p-1-1') == ['Vợ A']


# ---------------------------------------------------------------------------
# get_or_create_location / generation / branch
# ---------------------------------------------------------------------------


def test_get_or_create_location_blank_returns_none(mock_cursor):
    assert get_or_create_location(mock_cursor, "", "Nơi sinh") is None
    assert get_or_create_location(mock_cursor, None, "Nơi sinh") is None
    mock_cursor.execute.assert_not_called()


def test_get_or_create_location_returns_existing_id(mock_cursor):
    mock_cursor.fetchone.return_value = (7,)
    result = get_or_create_location(mock_cursor, "Hà Nội", "Nơi sinh")
    assert result == 7
    mock_cursor.execute.assert_called_once()


def test_get_or_create_location_inserts_when_absent(mock_cursor):
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 42
    result = get_or_create_location(mock_cursor, "Đà Nẵng", "Nguyên quán")
    assert result == 42
    assert mock_cursor.execute.call_count == 2


def test_get_or_create_generation_none_returns_none(mock_cursor):
    assert get_or_create_generation(mock_cursor, None) is None
    assert get_or_create_generation(mock_cursor, "") is None
    assert get_or_create_generation(mock_cursor, "abc") is None
    mock_cursor.execute.assert_not_called()


def test_get_or_create_generation_returns_existing_dict_row(mock_cursor):
    mock_cursor.fetchone.return_value = {"generation_id": 3}
    result = get_or_create_generation(mock_cursor, 3)
    assert result == 3


def test_get_or_create_generation_inserts_when_absent(mock_cursor):
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 10
    result = get_or_create_generation(mock_cursor, "5")
    assert result == 10
    assert mock_cursor.execute.call_count == 2


def test_get_or_create_branch_blank_returns_none(mock_cursor):
    assert get_or_create_branch(mock_cursor, "") is None
    assert get_or_create_branch(mock_cursor, None) is None
    mock_cursor.execute.assert_not_called()


def test_get_or_create_branch_returns_existing_dict_row(mock_cursor):
    mock_cursor.fetchone.return_value = {"branch_id": 2}
    result = get_or_create_branch(mock_cursor, "Hai")
    assert result == 2


def test_get_or_create_branch_inserts_when_absent(mock_cursor):
    mock_cursor.fetchone.return_value = None
    mock_cursor.lastrowid = 5
    result = get_or_create_branch(mock_cursor, "Ba")
    assert result == 5
    assert mock_cursor.execute.call_count == 2
