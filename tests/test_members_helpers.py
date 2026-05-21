from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from blueprints import members_portal
from services.members_helpers import (
    normalize_excel_header,
    normalize_sll_row_id,
    sll_branch_code_to_name,
    sll_canonical_branch,
    sll_cell_nonempty,
    sll_merge_excel_into_payload,
    sll_normalize_cell,
)


@pytest.fixture
def mock_cursor():
    return MagicMock()


def _empty_rel_data():
    return {
        "spouse_data_from_table": {},
        "spouse_data_from_marriages": {},
        "spouse_data_from_csv": {},
        "parent_data": {},
        "children_map": {},
        "siblings_map": {},
    }


def _person_row(**overrides):
    base = {
        "full_name": "Nguyễn Văn A",
        "alias": None,
        "father_mother_id": None,
        "fm_id": "1-1",
        "gender": "Nam",
        "status": "alive",
        "generation_level": 3,
        "branch_name": "Hai",
        "branch_id": None,
        "birth_date_solar": None,
        "birth_date_lunar": None,
        "death_date_solar": None,
        "death_date_lunar": None,
        "grave_info": None,
        "place_of_death": None,
        "occupation": None,
        "academic_rank": None,
        "academic_degree": None,
        "phone": None,
        "email": None,
        "biography": None,
        "personal_image_url": None,
        "personal_image": None,
    }
    base.update(overrides)
    return base


def test_sll_cell_nonempty_matches_blank_rules():
    assert sll_cell_nonempty("abc") is True
    assert sll_cell_nonempty(0) is True
    assert sll_cell_nonempty("") is False
    assert sll_cell_nonempty("  ") is False
    assert sll_cell_nonempty(None) is False


def test_sll_normalize_cell_preserves_existing_values_and_dates():
    assert sll_normalize_cell(datetime(2026, 5, 21, 9, 30)) == "2026-05-21"
    assert sll_normalize_cell(date(2026, 5, 21)) == "2026-05-21"
    assert sll_normalize_cell(7.0) == 7
    assert sll_normalize_cell(7.5) == 7.5
    assert sll_normalize_cell("x") == "x"


def test_normalize_sll_row_id_handles_excel_types():
    assert normalize_sll_row_id(None) == ""
    assert normalize_sll_row_id(7.0) == "7"
    assert normalize_sll_row_id(7.5) == "7.5"
    assert normalize_sll_row_id(" P-1-1 ") == "P-1-1"


def test_sll_canonical_branch_accepts_codes_and_names():
    mapping = sll_branch_code_to_name()

    assert sll_canonical_branch("1") == mapping["1"]
    assert sll_canonical_branch(mapping["2"]) == mapping["2"]
    assert sll_canonical_branch("Custom") == "Custom"
    assert sll_canonical_branch(" ") is None


def test_normalize_excel_header_removes_accents_and_separators():
    assert normalize_excel_header(" Họ và tên ") == "ho va ten"
    assert normalize_excel_header("FM-ID") == "fm id"
    assert normalize_excel_header(None) == ""


def test_sll_merge_excel_into_payload_maps_nonempty_excel_values():
    base = {
        "full_name": "Base Name",
        "spouse_info": "Old spouse",
        "children_info": "Old child",
        "branch_name": "Old branch",
    }
    merged = sll_merge_excel_into_payload(
        base,
        {
            "person_id": "P-1-1",
            "full_name": "New Name",
            "spouses": "New spouse",
            "children": "  ",
            "grave": "New grave",
            "branch_name": "1",
        },
    )

    assert merged["full_name"] == "New Name"
    assert merged["spouse_info"] == "New spouse"
    assert merged["children_info"] == "Old child"
    assert merged["grave_info"] == "New grave"
    assert merged["branch_name"] == sll_branch_code_to_name()["1"]
    assert "person_id" not in merged


def test_members_portal_keeps_legacy_helper_aliases():
    from services.members_helpers import sll_base_payload

    assert members_portal._sll_cell_nonempty is sll_cell_nonempty
    assert members_portal._sll_normalize_cell is sll_normalize_cell
    assert members_portal._normalize_sll_row_id is normalize_sll_row_id
    assert members_portal._sll_branch_code_to_name is sll_branch_code_to_name
    assert members_portal._sll_canonical_branch is sll_canonical_branch
    assert members_portal._sll_merge_excel_into_payload is sll_merge_excel_into_payload
    assert members_portal._normalize_excel_header is normalize_excel_header
    assert members_portal._sll_base_payload is sll_base_payload


# ---------------------------------------------------------------------------
# sll_base_payload
# ---------------------------------------------------------------------------


def test_sll_base_payload_returns_none_when_person_not_found(mock_cursor):
    from services.members_helpers import sll_base_payload

    mock_cursor.fetchone.return_value = None
    assert sll_base_payload(mock_cursor, 1, _empty_rel_data()) is None
    mock_cursor.execute.assert_called_once()


def test_sll_base_payload_basic_fields(mock_cursor):
    from services.members_helpers import sll_base_payload

    mock_cursor.fetchone.return_value = _person_row()
    rel = {**_empty_rel_data(), "parent_data": {1: {"father_name": "Cha", "mother_name": "Mẹ"}}}
    result = sll_base_payload(mock_cursor, 1, rel)

    assert result is not None
    assert result["full_name"] == "Nguyễn Văn A"
    assert result["fm_id"] == "1-1"
    assert result["father_name"] == "Cha"
    assert result["mother_name"] == "Mẹ"
    assert result["generation_number"] == 3


def test_sll_base_payload_uses_father_mother_id_fallback(mock_cursor):
    from services.members_helpers import sll_base_payload

    # father_mother_id absent → fall back to fm_id
    mock_cursor.fetchone.return_value = _person_row(father_mother_id=None, fm_id="2-3")
    result = sll_base_payload(mock_cursor, 1, _empty_rel_data())
    assert result["fm_id"] == "2-3"


def test_sll_base_payload_branch_lookup_when_branch_id_present(mock_cursor):
    from services.members_helpers import sll_base_payload

    call_count = 0

    def fetchone_side():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _person_row(branch_name=None, branch_id=5)
        return {"branch_name": "Ba"}

    mock_cursor.fetchone.side_effect = fetchone_side
    result = sll_base_payload(mock_cursor, 1, _empty_rel_data())

    assert result["branch_name"] == "Ba"
    assert mock_cursor.execute.call_count == 2


def test_sll_base_payload_no_branch_lookup_when_branch_name_present(mock_cursor):
    from services.members_helpers import sll_base_payload

    mock_cursor.fetchone.return_value = _person_row(branch_name="Một", branch_id=1)
    result = sll_base_payload(mock_cursor, 1, _empty_rel_data())

    assert result["branch_name"] == "Một"
    assert mock_cursor.execute.call_count == 1  # only persons query


def test_sll_base_payload_semi_joins_lists(mock_cursor):
    from services.members_helpers import sll_base_payload

    mock_cursor.fetchone.return_value = _person_row()
    rel = {
        **_empty_rel_data(),
        "children_map": {1: ["Con A", "Con B"]},
        "siblings_map": {1: ["Anh X"]},
        "spouse_data_from_table": {1: ["Vợ Y"]},
    }
    result = sll_base_payload(mock_cursor, 1, rel)

    assert result["children_info"] == "Con A; Con B"
    assert result["siblings_info"] == "Anh X"
    assert result["spouse_info"] == "Vợ Y"


def test_sll_base_payload_date_formatting(mock_cursor):
    from services.members_helpers import sll_base_payload

    mock_cursor.fetchone.return_value = _person_row(
        birth_date_solar=date(1990, 6, 15),
        death_date_solar=None,
    )
    result = sll_base_payload(mock_cursor, 1, _empty_rel_data())

    assert result["birth_date_solar"] == "1990-06-15"
    assert result["death_date_solar"] is None
