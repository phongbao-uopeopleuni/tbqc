# -*- coding: utf-8 -*-
"""Pure helper functions for members portal code."""

import re
import unicodedata
from datetime import date, datetime

from services.person_helpers import get_preferred_spouse_names


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


def sll_base_payload(cursor, person_id, rel_data):
    """Tạo base payload cho một person từ DB + rel_data đã load sẵn."""
    cursor.execute("SELECT * FROM persons WHERE person_id = %s", (person_id,))
    p = cursor.fetchone()
    if not p:
        return None
    pid = person_id
    parent = rel_data["parent_data"].get(pid, {})
    spouse_names = get_preferred_spouse_names(rel_data, pid)
    children = rel_data["children_map"].get(pid, [])
    siblings = rel_data["siblings_map"].get(pid, [])

    def semi(xs):
        if not xs:
            return None
        if isinstance(xs, list):
            return "; ".join(xs)
        return str(xs)

    branch_name = p.get("branch_name")
    if not branch_name and p.get("branch_id"):
        cursor.execute(
            "SELECT branch_name FROM branches WHERE branch_id = %s", (p["branch_id"],)
        )
        br = cursor.fetchone()
        if br:
            branch_name = br.get("branch_name")

    def fmt_date(d):
        if d is None:
            return None
        if hasattr(d, "isoformat"):
            s = d.isoformat()
            return s[:10] if len(s) >= 10 else s
        return str(d)

    fm = p.get("father_mother_id")
    if fm is None:
        fm = p.get("fm_id")

    return {
        "full_name": p.get("full_name"),
        "alias": p.get("alias"),
        "fm_id": fm,
        "gender": p.get("gender"),
        "status": p.get("status"),
        "generation_number": p.get("generation_level"),
        "branch_name": branch_name,
        "birth_date_solar": fmt_date(p.get("birth_date_solar")),
        "birth_date_lunar": fmt_date(p.get("birth_date_lunar")),
        "death_date_solar": fmt_date(p.get("death_date_solar")),
        "death_date_lunar": fmt_date(p.get("death_date_lunar")),
        "grave_info": p.get("grave_info"),
        "place_of_death": p.get("place_of_death"),
        "father_name": parent.get("father_name"),
        "mother_name": parent.get("mother_name"),
        "spouse_info": semi(spouse_names),
        "children_info": semi(children),
        "siblings_info": semi(siblings),
        "occupation": p.get("occupation"),
        "academic_rank": p.get("academic_rank"),
        "academic_degree": p.get("academic_degree"),
        "phone": p.get("phone"),
        "email": p.get("email"),
        "biography": p.get("biography"),
        "personal_image_url": p.get("personal_image_url") or p.get("personal_image"),
    }
