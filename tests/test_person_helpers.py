import pytest
from unittest.mock import MagicMock

from services.person_helpers import normalize_search_query, split_semicolon_values, find_person_by_name
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
