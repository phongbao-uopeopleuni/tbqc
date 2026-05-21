from services.person_helpers import normalize_search_query, split_semicolon_values
from services import person_service


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
