# -*- coding: utf-8 -*-
"""Pure helper functions for person service code."""

import logging

logger = logging.getLogger(__name__)


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


def load_relationship_data(cursor):
    """
    Helper function để load tất cả relationship data (spouse, children, siblings, parents)
    theo cùng logic như /api/members - đây là source of truth.

    Returns:
        dict với các keys:
        - spouse_data_from_table: {person_id: [spouse_name1, spouse_name2, ...]}
        - spouse_data_from_marriages: {person_id: [spouse_name1, ...]}
        - spouse_data_from_csv: {person_id: [spouse_name1, ...]}
        - parent_data: {child_id: {'father_name': ..., 'mother_name': ...}}
        - parent_ids_map: {child_id: [parent_id1, parent_id2, ...]}
        - children_map: {parent_id: [child_name1, child_name2, ...]}
        - siblings_map: {person_id: [sibling_name1, sibling_name2, ...]}
        - person_name_map: {person_id: full_name}
    """
    result = {
        'spouse_data_from_table': {},
        'spouse_data_from_marriages': {},
        'spouse_data_from_csv': {},
        'parent_data': {},
        'parent_ids_map': {},
        'children_map': {},
        'siblings_map': {},
        'person_name_map': {},
        # Dữ liệu text fallback khi chưa map được sang person_id.
        'children_text_map': {},
        'siblings_text_map': {},
        'parent_text_map': {},
    }
    try:
        cursor.execute("\n            SELECT TABLE_NAME \n            FROM information_schema.TABLES \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'spouse_sibling_children'\n        ")
        spouse_table_exists = cursor.fetchone() is not None
        if spouse_table_exists:
            cursor.execute(
                """
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'spouse_sibling_children'
                """
            )
            ssc_columns = {str((r or {}).get('COLUMN_NAME') or '').strip() for r in (cursor.fetchall() or [])}

            if 'spouse_name' in ssc_columns:
                cursor.execute("\n                    SELECT person_id, spouse_name \n                    FROM spouse_sibling_children \n                    WHERE spouse_name IS NOT NULL AND spouse_name != ''\n                ")
                for row in cursor.fetchall():
                    person_id_key = row.get('person_id')
                    spouse_name_str = row.get('spouse_name', '').strip()
                    if person_id_key and spouse_name_str:
                        result['spouse_data_from_table'][person_id_key] = split_semicolon_values(spouse_name_str)

            siblings_col = 'siblings_infor' if 'siblings_infor' in ssc_columns else ('siblings_info' if 'siblings_info' in ssc_columns else None)
            if siblings_col:
                cursor.execute(
                    f"""
                    SELECT person_id, {siblings_col} AS siblings_text
                    FROM spouse_sibling_children
                    WHERE {siblings_col} IS NOT NULL AND {siblings_col} != ''
                    """
                )
                for row in cursor.fetchall():
                    person_id_key = row.get('person_id')
                    siblings_text = row.get('siblings_text')
                    if person_id_key and siblings_text:
                        result['siblings_text_map'][person_id_key] = split_semicolon_values(siblings_text)

            children_col = 'children_infor' if 'children_infor' in ssc_columns else ('children_info' if 'children_info' in ssc_columns else None)
            if children_col:
                cursor.execute(
                    f"""
                    SELECT person_id, {children_col} AS children_text
                    FROM spouse_sibling_children
                    WHERE {children_col} IS NOT NULL AND {children_col} != ''
                    """
                )
                for row in cursor.fetchall():
                    person_id_key = row.get('person_id')
                    children_text = row.get('children_text')
                    if person_id_key and children_text:
                        result['children_text_map'][person_id_key] = split_semicolon_values(children_text)

            if 'father_name' in ssc_columns or 'mother_name' in ssc_columns:
                select_parts = ['person_id']
                if 'father_name' in ssc_columns:
                    select_parts.append('father_name')
                else:
                    select_parts.append('NULL AS father_name')
                if 'mother_name' in ssc_columns:
                    select_parts.append('mother_name')
                else:
                    select_parts.append('NULL AS mother_name')
                cursor.execute(f"SELECT {', '.join(select_parts)} FROM spouse_sibling_children")
                for row in cursor.fetchall():
                    person_id_key = row.get('person_id')
                    if not person_id_key:
                        continue
                    father_name = (row.get('father_name') or '').strip() if row.get('father_name') is not None else ''
                    mother_name = (row.get('mother_name') or '').strip() if row.get('mother_name') is not None else ''
                    if father_name or mother_name:
                        result['parent_text_map'][person_id_key] = {
                            'father_name': father_name or None,
                            'mother_name': mother_name or None,
                        }
    except Exception as e:
        logger.debug(f'Could not load spouse data from table: {e}')
    try:
        cursor.execute('\n            SELECT \n                m.person_id,\n                m.spouse_person_id,\n                sp_spouse.full_name AS spouse_name\n            FROM marriages m\n            LEFT JOIN persons sp_spouse ON sp_spouse.person_id = m.spouse_person_id\n            WHERE sp_spouse.full_name IS NOT NULL\n            \n            UNION\n            \n            SELECT \n                m.spouse_person_id AS person_id,\n                m.person_id AS spouse_person_id,\n                sp_person.full_name AS spouse_name\n            FROM marriages m\n            LEFT JOIN persons sp_person ON sp_person.person_id = m.person_id\n            WHERE sp_person.full_name IS NOT NULL\n        ')
        for row in cursor.fetchall():
            person_id_key = row.get('person_id')
            spouse_name = row.get('spouse_name')
            if person_id_key and spouse_name:
                if person_id_key not in result['spouse_data_from_marriages']:
                    result['spouse_data_from_marriages'][person_id_key] = []
                if spouse_name not in result['spouse_data_from_marriages'][person_id_key]:
                    result['spouse_data_from_marriages'][person_id_key].append(spouse_name)
    except Exception as e:
        logger.debug(f'Could not load spouse data from marriages: {e}')
    try:
        import csv
        import os
        csv_file = 'spouse_sibling_children.csv'
        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    person_id_key = row.get('person_id', '').strip()
                    spouse_name_str = row.get('spouse_name', '').strip()
                    if person_id_key and spouse_name_str:
                        spouse_names = [s.strip() for s in spouse_name_str.split(';') if s.strip()]
                        result['spouse_data_from_csv'][person_id_key] = spouse_names
    except Exception as e:
        logger.debug(f'Could not load spouse data from CSV: {e}')
    try:
        cursor.execute('\n            SELECT \n                r.child_id,\n                r.parent_id,\n                r.relation_type,\n                parent.full_name AS parent_name,\n                child.full_name AS child_name\n            FROM relationships r\n            LEFT JOIN persons parent ON r.parent_id = parent.person_id\n            LEFT JOIN persons child ON r.child_id = child.person_id\n            WHERE parent.full_name IS NOT NULL AND child.full_name IS NOT NULL\n        ')
        relationships = cursor.fetchall()
        for rel in relationships:
            child_id = rel['child_id']
            parent_id = rel['parent_id']
            relation_type = rel['relation_type']
            parent_name = rel['parent_name']
            child_name = rel['child_name']
            if child_id not in result['parent_data']:
                result['parent_data'][child_id] = {'father_name': None, 'mother_name': None}
            if relation_type == 'father' and parent_name:
                if result['parent_data'][child_id]['father_name']:
                    result['parent_data'][child_id]['father_name'] += ', ' + parent_name
                else:
                    result['parent_data'][child_id]['father_name'] = parent_name
            elif relation_type == 'mother' and parent_name:
                if result['parent_data'][child_id]['mother_name']:
                    result['parent_data'][child_id]['mother_name'] += ', ' + parent_name
                else:
                    result['parent_data'][child_id]['mother_name'] = parent_name
            if child_id not in result['parent_ids_map']:
                result['parent_ids_map'][child_id] = []
            if parent_id and parent_id not in result['parent_ids_map'][child_id]:
                result['parent_ids_map'][child_id].append(parent_id)
            if parent_id not in result['children_map']:
                result['children_map'][parent_id] = []
            if child_name and child_name not in result['children_map'][parent_id]:
                result['children_map'][parent_id].append(child_name)
        logger.debug(f'Loaded {len(relationships)} relationships')
    except Exception as e:
        logger.warning(f'Error loading relationships: {e}')
    try:
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name IS NOT NULL')
        for row in cursor.fetchall():
            result['person_name_map'][row['person_id']] = row['full_name']
    except Exception as e:
        logger.debug(f'Could not load person_name_map: {e}')
    try:
        parent_to_children = {}
        for child_id, parent_ids in result['parent_ids_map'].items():
            for parent_id in parent_ids:
                if parent_id not in parent_to_children:
                    parent_to_children[parent_id] = []
                if child_id not in parent_to_children[parent_id]:
                    parent_to_children[parent_id].append(child_id)
        for person_id in result['person_name_map'].keys():
            person_parent_ids = result['parent_ids_map'].get(person_id, [])
            if not person_parent_ids:
                continue
            sibling_names = set()
            for parent_id in person_parent_ids:
                children_of_parent = parent_to_children.get(parent_id, [])
                for child_id in children_of_parent:
                    if child_id != person_id:
                        child_name = result['person_name_map'].get(child_id)
                        if child_name:
                            sibling_names.add(child_name)
            if sibling_names:
                result['siblings_map'][person_id] = sorted(list(sibling_names))
        logger.debug(f"Loaded siblings for {len(result['siblings_map'])} persons")
    except Exception as e:
        logger.warning(f'Error loading siblings: {e}')

    # Fallback text data cho các trường quan hệ nhập tay chưa map sang person_id.
    try:
        for person_id_key, names in result.get('children_text_map', {}).items():
            if person_id_key not in result['children_map'] or not result['children_map'].get(person_id_key):
                result['children_map'][person_id_key] = names
        for person_id_key, names in result.get('siblings_text_map', {}).items():
            if person_id_key not in result['siblings_map'] or not result['siblings_map'].get(person_id_key):
                result['siblings_map'][person_id_key] = names
        for person_id_key, parent_names in result.get('parent_text_map', {}).items():
            if person_id_key not in result['parent_data']:
                result['parent_data'][person_id_key] = {'father_name': None, 'mother_name': None}
            if not result['parent_data'][person_id_key].get('father_name') and parent_names.get('father_name'):
                result['parent_data'][person_id_key]['father_name'] = parent_names.get('father_name')
            if not result['parent_data'][person_id_key].get('mother_name') and parent_names.get('mother_name'):
                result['parent_data'][person_id_key]['mother_name'] = parent_names.get('mother_name')
    except Exception as e:
        logger.warning(f'Error applying fallback relationship text data: {e}')

    return result
