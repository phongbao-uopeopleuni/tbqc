# -*- coding: utf-8 -*-
"""Pure helper functions for members portal code."""

import re
import unicodedata
from datetime import date, datetime


def sll_cell_nonempty(val):
    if val is None:
        return False
    if isinstance(val, str) and not val.strip():
        return False
    return True


def sll_normalize_cell(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, float):
        if val == int(val):
            return int(val)
    return val


def normalize_sll_row_id(val):
    if val is None:
        return ""
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return str(val).strip()
    if isinstance(val, (datetime, date)):
        return str(val).strip()
    return str(val).strip()


def sll_branch_code_to_name():
    return {
        "0": "Tổ tiên",
        "1": "Một",
        "2": "Hai",
        "3": "Ba",
        "4": "Bốn",
        "5": "Năm",
        "6": "Sáu",
        "7": "Bảy",
        "-1": "Khác",
    }


def sll_canonical_branch(val):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    mapping = sll_branch_code_to_name()
    if s in mapping.values():
        return s
    if s in mapping:
        return mapping[s]
    return s


def normalize_excel_header(header):
    if header is None:
        return ""
    s = str(header).strip().lower()
    if not s:
        return ""
    s = "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def sll_merge_excel_into_payload(base, excel_by_internal_key):
    out = dict(base)
    key_map = {
        "spouses": "spouse_info",
        "children": "children_info",
        "siblings": "siblings_info",
        "grave": "grave_info",
    }
    for key, value in excel_by_internal_key.items():
        if key == "person_id":
            continue
        if not sll_cell_nonempty(value):
            continue
        normalized_value = sll_normalize_cell(value)
        payload_key = key_map.get(key, key)
        if payload_key == "branch_name":
            normalized_value = sll_canonical_branch(normalized_value)
        out[payload_key] = normalized_value
    return out
