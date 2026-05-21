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


def find_person_by_name(cursor, name, generation_id=None):
    """Tìm person_id theo tên, có thể lọc theo generation_id."""
    if not name or not name.strip():
        return None
    name = name.strip()
    if generation_id:
        cursor.execute(
            """
            SELECT person_id FROM persons
            WHERE full_name = %s AND generation_id = %s
            LIMIT 1
        """,
            (name, generation_id),
        )
    else:
        cursor.execute(
            """
            SELECT person_id FROM persons
            WHERE full_name = %s
            LIMIT 1
        """,
            (name,),
        )
    result = cursor.fetchone()
    if not result:
        return None
    if isinstance(result, dict):
        return result.get("person_id")
    return result[0]
