from datetime import date, datetime

from blueprints import members_portal
from services.members_helpers import (
    normalize_excel_header,
    normalize_sll_row_id,
    sll_branch_code_to_name,
    sll_canonical_branch,
    sll_cell_nonempty,
    sll_normalize_cell,
)


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


def test_members_portal_keeps_legacy_helper_aliases():
    assert members_portal._sll_cell_nonempty is sll_cell_nonempty
    assert members_portal._sll_normalize_cell is sll_normalize_cell
    assert members_portal._normalize_sll_row_id is normalize_sll_row_id
    assert members_portal._sll_branch_code_to_name is sll_branch_code_to_name
    assert members_portal._sll_canonical_branch is sll_canonical_branch
    assert members_portal._normalize_excel_header is normalize_excel_header
