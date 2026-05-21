# -*- coding: utf-8 -*-
"""Pure helper functions for person service code."""


def normalize_search_query(q):
    """
    Normalize search query for broader person search support.

    Returns:
        tuple: (normalized_query, person_id_patterns)
    """
    if not q:
        return ("", [])

    q = str(q).strip()
    person_id_patterns = []

    if q.upper().startswith("P-") or q.lower().startswith("p-"):
        person_id_patterns.append(f"%{q}%")
        person_id_patterns.append(f"%{q.upper()}%")
        person_id_patterns.append(f"%{q.lower()}%")

    if q.replace("-", "").replace(" ", "").isdigit():
        if "-" in q:
            parts = q.split("-")
            if len(parts) == 2:
                gen, num = (parts[0].strip(), parts[1].strip())
                person_id_patterns.append(f"%P-{gen}-{num}%")
                person_id_patterns.append(f"%p-{gen}-{num}%")
                person_id_patterns.append(f"%{gen}-{num}%")
        else:
            person_id_patterns.append(f"%-{q}%")
            person_id_patterns.append(f"%{q}%")

    return (q, person_id_patterns)


def split_semicolon_values(raw_value):
    if not raw_value:
        return []
    return [s.strip() for s in str(raw_value).split(";") if s and str(s).strip()]
