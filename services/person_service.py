# -*- coding: utf-8 -*-
"""Person CRUD and related API handlers."""
import os
import re
import csv
import json
import logging
import math
from datetime import datetime, date
from flask import jsonify, request
from flask_login import login_required, current_user
from mysql.connector import Error
from werkzeug.utils import secure_filename

from audit_log import log_person_update, log_person_create, log_activity
from db import get_db_connection
from extensions import cache
from services.members_service import get_members_password
from services.activities_service import is_admin_user
from services.person_helpers import (
    normalize_search_query,
    split_semicolon_values,
    find_person_by_name,
    get_preferred_spouse_names,
    load_relationship_data,
    get_or_create_location,
    get_or_create_generation,
    get_or_create_branch,
)
from utils.validation import (
    validate_filename,
    validate_person_id,
    sanitize_string,
    validate_integer,
    secure_compare,
)

logger = logging.getLogger(__name__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_split_semicolon_values = split_semicolon_values


def _apply_parent_relationship_mutations(cursor, person_id, data):
    """Apply father/mother mutations.

    Ưu tiên mỗi loại quan hệ:
    1. father_id / mother_id (person_id trực tiếp) — chính xác nhất
    2. father_name / mother_name + fm_id hint — name lookup có disambiguation
    3. Key bị bỏ qua (omitted) → giữ nguyên relation

    Blank value (id hoặc name) → xóa relation.
    Không tìm được / trùng tên không giải được → raise ValueError (không ghi gì).
    """
    # fm_id dùng làm hint disambiguation khi tên bị trùng
    fm_id = (str(data.get('fm_id') or data.get('father_mother_id') or '')).strip() or None

    for relation_type, name_field, id_field in (
        ('father', 'father_name', 'father_id'),
        ('mother', 'mother_name', 'mother_id'),
    ):
        has_id_field = id_field in data
        has_name_field = name_field in data

        if not has_id_field and not has_name_field:
            continue  # Omitted → giữ nguyên

        if has_id_field:
            # Ưu tiên 1: person_id trực tiếp
            direct_id = str(data[id_field]).strip() if data.get(id_field) is not None else ''
            if not direct_id:
                cursor.execute(
                    "DELETE FROM relationships WHERE child_id = %s AND relation_type = %s",
                    (person_id, relation_type),
                )
                continue
            cursor.execute(
                "SELECT person_id FROM persons WHERE person_id = %s",
                (direct_id,),
            )
            if not cursor.fetchone():
                raise ValueError(f'Khong tim thay {id_field}: {direct_id}')
            parent_id = direct_id
        else:
            # Ưu tiên 2: name lookup với fm_id disambiguation
            raw_value = data.get(name_field)
            normalized_name = str(raw_value).strip() if raw_value is not None else ''
            if not normalized_name:
                cursor.execute(
                    "DELETE FROM relationships WHERE child_id = %s AND relation_type = %s",
                    (person_id, relation_type),
                )
                continue
            parent_id = find_person_by_name(cursor, normalized_name, fm_id=fm_id)
            if not parent_id:
                raise ValueError(
                    f'Khong tim thay hoac ten bi trung {name_field}: {normalized_name}'
                )

        cursor.execute(
            "DELETE FROM relationships WHERE child_id = %s AND relation_type = %s",
            (person_id, relation_type),
        )
        cursor.execute(
            "INSERT INTO relationships (child_id, parent_id, relation_type) VALUES (%s, %s, %s)",
            (person_id, parent_id, relation_type),
        )

def get_persons():
    """Lấy danh sách tất cả người từ schema mới (person_id VARCHAR, relationships mới)"""
    logger.debug('API /api/persons duoc goi')
    connection = get_db_connection()
    if not connection:
        print('ERROR: Khong the ket noi database trong get_persons()')
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email')\n        ")
        available_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        select_fields = ['p.person_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status', 'p.generation_level', 'p.home_town', 'p.nationality', 'p.religion', 'p.birth_date_solar', 'p.birth_date_lunar', 'p.death_date_solar', 'p.death_date_lunar', 'p.place_of_death', 'p.grave_info', 'p.contact', 'p.social', 'p.occupation', 'p.education', 'p.events', 'p.titles', 'p.blood_type', 'p.genetic_disease', 'p.note', 'p.father_mother_id', 'p.family_unit_id']
        if 'personal_image_url' in available_columns:
            select_fields.append('p.personal_image_url AS personal_image_url')
        elif 'personal_image' in available_columns:
            select_fields.append('p.personal_image AS personal_image_url')
        else:
            select_fields.append('NULL AS personal_image_url')
            
        if 'version' in available_columns:
            select_fields.append('p.version')
        else:
            select_fields.append('1 AS version')
        if 'biography' in available_columns:
            select_fields.append('p.biography')
        else:
            select_fields.append('NULL AS biography')
        if 'academic_rank' in available_columns:
            select_fields.append('p.academic_rank')
        else:
            select_fields.append('NULL AS academic_rank')
        if 'academic_degree' in available_columns:
            select_fields.append('p.academic_degree')
        else:
            select_fields.append('NULL AS academic_degree')
        if 'phone' in available_columns:
            select_fields.append('p.phone')
        else:
            select_fields.append('NULL AS phone')
        if 'email' in available_columns:
            select_fields.append('p.email')
        else:
            select_fields.append('NULL AS email')
        paginated = request.args.get('paginated', '').strip().lower() in ('1', 'true', 'yes')
        total = None
        page = 1
        per_page = 20
        if paginated:
            try:
                page = max(1, int(request.args.get('page', 1)))
            except (TypeError, ValueError):
                page = 1
            try:
                raw_pp = int(request.args.get('per_page', 20))
                per_page = min(50, max(1, raw_pp))
            except (TypeError, ValueError):
                per_page = 20
            cursor.execute('SELECT COUNT(*) AS c FROM persons')
            total = cursor.fetchone()['c']
            offset = (page - 1) * per_page

        main_sql = f"\n            SELECT \n                {', '.join(select_fields)},\n\n                -- Cha từ relationships\n                father.person_id AS father_id,\n                father.full_name AS father_name,\n\n                -- Mẹ từ relationships\n                mother.person_id AS mother_id,\n                mother.full_name AS mother_name,\n\n                -- Con cái\n                GROUP_CONCAT(\n                    DISTINCT child.full_name\n                    ORDER BY child.full_name\n                    SEPARATOR '; '\n                ) AS children\n            FROM persons p\n\n            -- Cha từ relationships (relation_type = 'father')\n            LEFT JOIN relationships rel_father\n                ON rel_father.child_id = p.person_id \n                AND rel_father.relation_type = 'father'\n            LEFT JOIN persons father\n                ON rel_father.parent_id = father.person_id\n\n            -- Mẹ từ relationships (relation_type = 'mother')\n            LEFT JOIN relationships rel_mother\n                ON rel_mother.child_id = p.person_id \n                AND rel_mother.relation_type = 'mother'\n            LEFT JOIN persons mother\n                ON rel_mother.parent_id = mother.person_id\n\n            -- Con cái: những người có parent_id = p.person_id\n            LEFT JOIN relationships rel_child\n                ON rel_child.parent_id = p.person_id\n                AND rel_child.relation_type IN ('father', 'mother')\n            LEFT JOIN persons child\n                ON child.person_id = rel_child.child_id\n\n            GROUP BY\n                p.person_id,\n                p.full_name,\n                p.alias,\n                p.gender,\n                p.status,\n                p.generation_level,\n                p.home_town,\n                p.nationality,\n                p.religion,\n                p.birth_date_solar,\n                p.birth_date_lunar,\n                p.death_date_solar,\n                p.death_date_lunar,\n                p.place_of_death,\n                p.grave_info,\n                p.contact,\n                p.social,\n                p.occupation,\n                p.education,\n                p.events,\n                p.titles,\n                p.blood_type,\n                p.genetic_disease,\n                p.note,\n                p.father_mother_id,\n                father.person_id,\n                father.full_name,\n                mother.person_id,\n                mother.full_name\n            ORDER BY\n                p.generation_level,\n                p.full_name\n        "
        if paginated:
            main_sql += '\n            LIMIT %s OFFSET %s\n        '
            cursor.execute(main_sql, (per_page, offset))
        else:
            cursor.execute(main_sql)
        persons = cursor.fetchall()
        for person in persons:
            person_id = person['person_id']
            cursor.execute("\n                SELECT parent_id, relation_type\n                FROM relationships\n                WHERE child_id = %s AND relation_type IN ('father', 'mother')\n            ", (person_id,))
            parent_rels = cursor.fetchall()
            father_id = None
            mother_id = None
            for rel in parent_rels:
                if rel['relation_type'] == 'father':
                    father_id = rel['parent_id']
                elif rel['relation_type'] == 'mother':
                    mother_id = rel['parent_id']
            if father_id or mother_id:
                conditions = []
                params = [person_id]
                if father_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'father')")
                    params.append(father_id)
                if mother_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'mother')")
                    params.append(mother_id)
                sibling_query = f"\n                    SELECT DISTINCT s.full_name\n                    FROM persons s\n                    JOIN relationships r ON s.person_id = r.child_id\n                    WHERE s.person_id <> %s\n                      AND ({' OR '.join(conditions)})\n                    ORDER BY s.full_name\n                "
                cursor.execute(sibling_query, params)
                siblings = cursor.fetchall()
                person['siblings'] = '; '.join([s['full_name'] for s in siblings]) if siblings else None
            else:
                person['siblings'] = None
            cursor.execute("\n                SELECT DISTINCT \n                    CASE \n                        WHEN m.husband_id = %s THEN m.wife_id\n                        ELSE m.husband_id\n                    END AS spouse_id,\n                    sp.full_name AS spouse_name\n                FROM marriages m\n                JOIN persons sp ON (\n                    CASE \n                        WHEN m.husband_id = %s THEN sp.person_id = m.wife_id\n                        ELSE sp.person_id = m.husband_id\n                    END\n                )\n                WHERE (m.husband_id = %s OR m.wife_id = %s)\n                AND m.status != 'Đã ly dị'\n            ", (person_id, person_id, person_id, person_id))
            spouses = cursor.fetchall()
            if spouses:
                spouse_names = [s['spouse_name'] for s in spouses if s.get('spouse_name')]
                person['spouse'] = '; '.join(spouse_names) if spouse_names else None
            else:
                person['spouse'] = None
        is_admin = current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
        for person in persons:
            if not is_admin:
                if 'phone' in person:
                    person['phone'] = None
                if 'email' in person:
                    person['email'] = None
                if 'contact' in person:  # Fix F2: contact chứa SĐT — PII, chỉ admin xem
                    person['contact'] = None

        if paginated and total is not None:
            pages = int(math.ceil(total / float(per_page))) if per_page else 0
            return jsonify({
                'items': persons,
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
            })
        return jsonify(persons)
    except Error as e:
        print(f'ERROR: Loi trong /api/persons: {e}')
        import traceback
        traceback.print_exc()
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
def get_sheet3_data_by_name(person_name, csv_id=None, father_name=None, mother_name=None):
    """Đọc dữ liệu từ Sheet3 CSV theo tên người
    QUAN TRỌNG: Dùng csv_id hoặc tên bố/mẹ để phân biệt khi có nhiều người trùng tên
    """
    sheet3_file = os.path.join(ROOT_DIR, 'Data_TBQC_Sheet3.csv')
    if not os.path.exists(sheet3_file):
        return None
    try:
        with open(sheet3_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            candidates = []
            for row in reader:
                sheet3_name = (row.get('Họ và tên', '') or '').strip()
                person_name_clean = (person_name or '').strip()
                if sheet3_name.lower() == person_name_clean.lower():
                    candidates.append(row)
            if len(candidates) == 1:
                row = candidates[0]
                return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
            if len(candidates) > 1:
                if csv_id:
                    for row in candidates:
                        sheet3_id = (row.get('ID', '') or '').strip()
                        if sheet3_id == csv_id:
                            return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
                if father_name or mother_name:
                    for row in candidates:
                        sheet3_father = (row.get('Tên bố', '') or '').strip().lower()
                        sheet3_mother = (row.get('Tên mẹ', '') or '').strip().lower()
                        father_match = True
                        mother_match = True
                        if father_name:
                            father_clean = father_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            father_match = father_clean in sheet3_father or sheet3_father in father_clean
                        if mother_name:
                            mother_clean = mother_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            mother_match = mother_clean in sheet3_mother or sheet3_mother in mother_clean
                        if father_match and mother_match:
                            return {'sheet3_id': row.get('ID', ''), 'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''), 'sheet3_death_place': row.get('Nơi mất', ''), 'sheet3_grave': row.get('Mộ phần', ''), 'sheet3_parents': row.get('Thông tin Bố Mẹ', ''), 'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''), 'sheet3_spouse': row.get('Thông tin Hôn Phối', ''), 'sheet3_children': row.get('Thông tin Con', '')}
                return None
    except Exception as e:
        print(f'Lỗi đọc Sheet3: {e}')
        return None
    return None

def get_person(person_id):
    """Lấy thông tin chi tiết một người từ schema mới"""
    person_id = str(person_id).strip() if person_id else None
    if not person_id:
        return (jsonify({'error': 'person_id không hợp lệ'}), 400)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email', 'branch_name')\n        ")
        available_columns = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        select_fields = ['p.person_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status', 'p.generation_level', 'p.birth_date_solar', 'p.birth_date_lunar', 'p.death_date_solar', 'p.death_date_lunar', 'p.home_town', 'p.nationality', 'p.religion', 'p.place_of_death', 'p.grave_info', 'p.contact', 'p.social', 'p.occupation', 'p.education', 'p.events', 'p.titles', 'p.blood_type', 'p.genetic_disease', 'p.note', 'p.father_mother_id', 'p.family_unit_id']
        if 'personal_image_url' in available_columns:
            select_fields.append('p.personal_image_url AS personal_image_url')
        elif 'personal_image' in available_columns:
            select_fields.append('p.personal_image AS personal_image_url')
        else:
            select_fields.append('NULL AS personal_image_url')
            
        if 'version' in available_columns:
            select_fields.append('p.version')
        else:
            select_fields.append('1 AS version')
        if 'biography' in available_columns:
            select_fields.append('p.biography')
        else:
            select_fields.append('NULL AS biography')
        if 'academic_rank' in available_columns:
            select_fields.append('p.academic_rank')
        else:
            select_fields.append('NULL AS academic_rank')
        if 'academic_degree' in available_columns:
            select_fields.append('p.academic_degree')
        else:
            select_fields.append('NULL AS academic_degree')
        if 'phone' in available_columns:
            select_fields.append('p.phone')
        else:
            select_fields.append('NULL AS phone')
        if 'email' in available_columns:
            select_fields.append('p.email')
        else:
            select_fields.append('NULL AS email')
        if 'branch_name' in available_columns:
            select_fields.append('p.branch_name')
        else:
            select_fields.append('NULL AS branch_name')
        cursor.execute(f"\n            SELECT \n                {', '.join(select_fields)}\n            FROM persons p\n            WHERE p.person_id = %s\n        ", (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy'}), 404)
        person['generation_number'] = person.get('generation_level')
        if 'origin_location' not in person:
            person['origin_location'] = person.get('home_town')
        if 'death_location' not in person:
            person['death_location'] = person.get('place_of_death')
        if 'birth_location' not in person:
            person['birth_location'] = None
        try:
            bn_col = person.get('branch_name')
            if bn_col and str(bn_col).strip():
                person['branch_name'] = str(bn_col).strip()
            else:
                cursor.execute("SHOW COLUMNS FROM persons LIKE 'branch_id'")
                has_branch_id = cursor.fetchone()
                if has_branch_id:
                    cursor.execute('SELECT branch_id FROM persons WHERE person_id = %s', (person_id,))
                    branch_row = cursor.fetchone()
                    if branch_row and branch_row.get('branch_id'):
                        cursor.execute('SELECT branch_name FROM branches WHERE branch_id = %s', (branch_row['branch_id'],))
                        branch = cursor.fetchone()
                        person['branch_name'] = branch['branch_name'] if branch else None
                    else:
                        person['branch_name'] = None
                else:
                    person['branch_name'] = None
        except Exception as e:
            logger.warning(f'Could not fetch branch_name: {e}')
            person['branch_name'] = None
        try:
            cursor.execute("\n                SELECT \n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN r.parent_id END) AS father_ids,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'father' THEN parent.full_name END SEPARATOR ', ') AS father_name,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN r.parent_id END) AS mother_ids,\n                    GROUP_CONCAT(DISTINCT CASE WHEN r.relation_type = 'mother' THEN parent.full_name END SEPARATOR ', ') AS mother_name\n                FROM relationships r\n                JOIN persons parent ON r.parent_id = parent.person_id\n                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')\n                GROUP BY r.child_id\n            ", (person_id,))
            parent_info = cursor.fetchone()
            if parent_info:
                father_ids_str = parent_info.get('father_ids')
                father_id = father_ids_str.split(',')[0].strip() if father_ids_str else None
                mother_ids_str = parent_info.get('mother_ids')
                mother_id = mother_ids_str.split(',')[0].strip() if mother_ids_str else None
                person['father_id'] = father_id
                person['father_name'] = parent_info.get('father_name')
                person['mother_id'] = mother_id
                person['mother_name'] = parent_info.get('mother_name')
            else:
                person['father_id'] = None
                person['father_name'] = None
                person['mother_id'] = None
                person['mother_name'] = None
        except Exception as e:
            logger.warning(f'Error fetching parents for {person_id}: {e}')
            import traceback
            logger.debug(traceback.format_exc())
            person['father_id'] = None
            person['father_name'] = None
            person['mother_id'] = None
            person['mother_name'] = None
        relationship_data = None
        try:
            relationship_data = load_relationship_data(cursor)
            siblings_map = relationship_data['siblings_map']
            siblings_list = siblings_map.get(person_id, [])
            person['siblings'] = '; '.join(siblings_list) if siblings_list else None
        except Exception as e:
            logger.warning(f'Error fetching siblings for {person_id}: {e}')
            person['siblings'] = None
        try:
            cursor.execute(
                """
                SELECT p.person_id, p.full_name, p.generation_level, p.gender
                FROM relationships r
                JOIN persons p ON r.child_id = p.person_id
                WHERE r.parent_id = %s
                ORDER BY p.generation_level, p.full_name
                """,
                (person_id,),
            )
            children_records = cursor.fetchall()
            if children_records:
                children_list = [
                    {
                        'person_id': c['person_id'],
                        'full_name': c['full_name'],
                        'name': c['full_name'],
                        'generation_level': c['generation_level'],
                        'generation_number': c['generation_level'],
                        'gender': c['gender'],
                    }
                    for c in children_records if c.get('full_name')
                ]
                person['children'] = children_list
                person['children_string'] = '; '.join(
                    c['full_name'] for c in children_records if c.get('full_name')
                ) or None
                logger.info(f'[API /api/person/{person_id}] Loaded {len(children_list)} children')
            else:
                person['children'] = []
                person['children_string'] = None
                logger.debug(f'[API /api/person/{person_id}] No children found')
        except Exception as e:
            logger.warning(f'Error fetching children for {person_id}: {e}')
            person['children'] = []
            person['children_string'] = None
        try:
            cursor.execute(
                """
                SELECT
                    m.id AS marriage_id,
                    CASE WHEN m.husband_id = %s THEN m.wife_id ELSE m.husband_id END AS spouse_id,
                    sp.full_name AS spouse_name,
                    sp.gender AS spouse_gender,
                    m.status AS marriage_status,
                    m.note AS marriage_note
                FROM marriages m
                LEFT JOIN persons sp
                    ON sp.person_id = CASE WHEN m.husband_id = %s THEN m.wife_id ELSE m.husband_id END
                WHERE m.husband_id = %s OR m.wife_id = %s
                ORDER BY m.created_at
                """,
                (person_id, person_id, person_id, person_id),
            )
            marriages = cursor.fetchall()
            if marriages:
                person['marriages'] = marriages
                spouse_names = [m['spouse_name'] for m in marriages if m.get('spouse_name')]
                spouse_string = '; '.join(spouse_names) if spouse_names else None
                person['spouse'] = spouse_string
                person['spouse_name'] = spouse_string
            else:
                person['marriages'] = []
                person['spouse'] = None
                person['spouse_name'] = None
        except Exception as e:
            logger.warning(f'Error fetching marriages for {person_id}: {e}')
            person['marriages'] = []
            person['spouse'] = None
            person['spouse_name'] = None
        if relationship_data:
            try:
                if not person.get('spouse') or person.get('spouse') == '':
                    spouse_names = get_preferred_spouse_names(relationship_data, person_id)
                    if spouse_names:
                        spouse_string = '; '.join(spouse_names)
                        person['spouse'] = spouse_string
                        person['spouse_name'] = spouse_string
                        logger.info(f'[API /api/person/{person_id}] Loaded spouse from prioritized relationship data: {spouse_string}')
                elif not person.get('spouse_name'):
                    person['spouse_name'] = person.get('spouse')
                    logger.info(f"[API /api/person/{person_id}] Set spouse_name from spouse: {person.get('spouse')}")
            except Exception as e:
                logger.debug(f'Could not load spouse from helper for {person_id}: {e}')
                import traceback
                logger.debug(traceback.format_exc())
        try:
            cursor.callproc('sp_get_ancestors', [person_id, 10])
            ancestors_result = None
            for result_set in cursor.stored_results():
                ancestors_result = result_set.fetchall()
                break
            if ancestors_result:
                ancestors = []
                for row in ancestors_result:
                    if isinstance(row, dict):
                        ancestors.append({'person_id': row.get('person_id'), 'full_name': row.get('full_name'), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'level': row.get('level', 0)})
                    else:
                        ancestors.append({'person_id': row[0] if len(row) > 0 else None, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
                person['ancestors'] = ancestors
                ancestors_chain = []
                for ancestor in ancestors:
                    level = ancestor.get('level', 0)
                    level_name = ''
                    if level == 1:
                        level_name = 'Cha/Mẹ'
                    elif level == 2:
                        level_name = 'Ông/Bà'
                    elif level == 3:
                        level_name = 'Cụ'
                    elif level == 4:
                        level_name = 'Kỵ'
                    elif level >= 5:
                        level_name = f'Tổ tiên cấp {level}'
                    else:
                        level_name = f'Cấp {level}'
                    ancestors_chain.append({'level': level, 'level_name': level_name, 'full_name': ancestor.get('full_name', ''), 'generation_level': ancestor.get('generation_level'), 'gender': ancestor.get('gender'), 'person_id': ancestor.get('person_id')})
                ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                person['ancestors_chain'] = ancestors_chain
                ancestors.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                person['ancestors'] = ancestors
                logger.info(f'[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via stored procedure')
            else:
                # SP succeeded but returned 0 rows — fall through to manual fallback below
                raise LookupError("sp_get_ancestors returned empty result set")
        except Exception as e:
            logger.warning(f'Error calling sp_get_ancestors for {person_id}: {e}')
            import traceback
            logger.debug(traceback.format_exc())
            try:
                ancestors_chain = []
                if not father_id and (not mother_id):
                    cursor.execute(
                        """
                        SELECT r.parent_id, r.relation_type,
                               parent.person_id, parent.full_name, parent.gender, parent.generation_level
                        FROM relationships r
                        JOIN persons parent ON r.parent_id = parent.person_id
                        WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                        """,
                        (person_id,),
                    )
                    parent_rels = cursor.fetchall()
                    for rel in parent_rels:
                        if rel.get('relation_type') == 'father':
                            father_id = rel.get('parent_id')
                        elif rel.get('relation_type') == 'mother':
                            mother_id = rel.get('parent_id')
                if father_id:
                    cursor.execute(
                        'SELECT p.person_id, p.full_name, p.gender, p.generation_level FROM persons p WHERE p.person_id = %s',
                        (father_id,),
                    )
                    father = cursor.fetchone()
                    if father:
                        ancestors_chain.append({'level': 1, 'level_name': 'Cha/Mẹ', 'full_name': father.get('full_name', ''), 'generation_level': father.get('generation_level'), 'gender': father.get('gender'), 'person_id': father.get('person_id')})
                if mother_id:
                    cursor.execute(
                        'SELECT p.person_id, p.full_name, p.gender, p.generation_level FROM persons p WHERE p.person_id = %s',
                        (mother_id,),
                    )
                    mother = cursor.fetchone()
                    if mother:
                        ancestors_chain.append({'level': 1, 'level_name': 'Cha/Mẹ', 'full_name': mother.get('full_name', ''), 'generation_level': mother.get('generation_level'), 'gender': mother.get('gender'), 'person_id': mother.get('person_id')})
                max_level = 10
                current_level = 1
                visited_ids = {person_id}
                while current_level < max_level:
                    current_level += 1
                    level_name = {2: 'Ông/Bà', 3: 'Cụ', 4: 'Kỵ'}.get(current_level, f'Tổ tiên cấp {current_level}')
                    ancestors_to_process = [a for a in ancestors_chain if a['level'] == current_level - 1 and a.get('person_id')]
                    if not ancestors_to_process:
                        break
                    for ancestor in ancestors_to_process:
                        ancestor_id = ancestor.get('person_id')
                        if not ancestor_id or ancestor_id in visited_ids:
                            continue
                        visited_ids.add(ancestor_id)
                        cursor.execute(
                            """
                            SELECT r.parent_id, r.relation_type,
                                   parent.person_id, parent.full_name, parent.gender, parent.generation_level
                            FROM relationships r
                            JOIN persons parent ON r.parent_id = parent.person_id
                            WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                            """,
                            (ancestor_id,),
                        )
                        parent_rels = cursor.fetchall()
                        for parent_rel in parent_rels:
                            p_id = parent_rel.get('person_id')
                            if p_id and p_id not in visited_ids:
                                ancestors_chain.append({'level': current_level, 'level_name': level_name, 'full_name': parent_rel.get('full_name', ''), 'generation_level': parent_rel.get('generation_level'), 'gender': parent_rel.get('gender'), 'person_id': p_id})
                                visited_ids.add(p_id)
                ancestors_chain.sort(key=lambda x: int(x.get('generation_level', 0) or 0))
                person['ancestors_chain'] = ancestors_chain
                person['ancestors'] = ancestors_chain
                logger.info(f'[API /api/person/{person_id}] Found {len(ancestors_chain)} ancestors via manual query')
            except Exception as e2:
                logger.warning(f'Error fetching ancestors manually for {person_id}: {e2}')
                person['ancestors_chain'] = []
                person['ancestors'] = []
        if 'ancestors_chain' not in person:
            person['ancestors_chain'] = []
            person['ancestors'] = []
        if person:
            from datetime import date, datetime
            try:
                birth_date_solar = person.get('birth_date_solar')
                if birth_date_solar:
                    if isinstance(birth_date_solar, (date, datetime)):
                        person['birth_date_solar'] = birth_date_solar.strftime('%Y-%m-%d')
                    elif isinstance(birth_date_solar, str):
                        if not (birth_date_solar.startswith('19') or birth_date_solar.startswith('20')):
                            pass
            except Exception as e:
                logger.warning(f'Error formatting birth_date_solar for {person_id}: {e}')
                if 'birth_date_solar' in person:
                    person['birth_date_solar'] = str(person['birth_date_solar']) if person['birth_date_solar'] else None
            try:
                birth_date_lunar = person.get('birth_date_lunar')
                if birth_date_lunar and isinstance(birth_date_lunar, (date, datetime)):
                    person['birth_date_lunar'] = birth_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting birth_date_lunar for {person_id}: {e}')
                if 'birth_date_lunar' in person:
                    person['birth_date_lunar'] = str(person.get('birth_date_lunar')) if person.get('birth_date_lunar') else None
            try:
                death_date_solar = person.get('death_date_solar')
                if death_date_solar and isinstance(death_date_solar, (date, datetime)):
                    person['death_date_solar'] = death_date_solar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting death_date_solar for {person_id}: {e}')
                if 'death_date_solar' in person:
                    person['death_date_solar'] = str(person.get('death_date_solar')) if person.get('death_date_solar') else None
            try:
                death_date_lunar = person.get('death_date_lunar')
                if death_date_lunar and isinstance(death_date_lunar, (date, datetime)):
                    person['death_date_lunar'] = death_date_lunar.strftime('%Y-%m-%d')
            except Exception as e:
                logger.warning(f'Error formatting death_date_lunar for {person_id}: {e}')
                if 'death_date_lunar' in person:
                    person['death_date_lunar'] = str(person.get('death_date_lunar')) if person.get('death_date_lunar') else None
            logger.info(f'[API /api/person/{person_id}] Returning complete person data:')
            logger.info(f"  - person_id: {person.get('person_id')}")
            logger.info(f"  - full_name: {person.get('full_name')}")
            logger.info(f"  - alias: {person.get('alias')}")
            logger.info(f"  - gender: {person.get('gender')}")
            logger.info(f"  - status: {person.get('status')}")
            logger.info(f"  - generation_level: {person.get('generation_level')}")
            logger.info(f"  - generation_number: {person.get('generation_number')}")
            logger.info(f"  - branch_name: {person.get('branch_name')}")
            logger.info(f"  - father_id: {person.get('father_id')}")
            logger.info(f"  - father_name: {person.get('father_name')}")
            logger.info(f"  - mother_id: {person.get('mother_id')}")
            logger.info(f"  - mother_name: {person.get('mother_name')}")
            logger.info(f"  - siblings: {person.get('siblings')}")
            logger.info(f"  - children: {person.get('children')}")
            logger.info(f"  - spouse: {person.get('spouse')}")
            logger.info(f"  - marriages: {len(person.get('marriages', []))} records")
            logger.info(f"  - birth_date_solar: {person.get('birth_date_solar')}")
            logger.info(f"  - birth_date_lunar: {person.get('birth_date_lunar')}")
            logger.info(f"  - birth_location: {person.get('birth_location')}")
            logger.info(f"  - death_date_solar: {person.get('death_date_solar')}")
            logger.info(f"  - death_date_lunar: {person.get('death_date_lunar')}")
            logger.info(f"  - death_location: {person.get('death_location')}")
            logger.info(f"  - place_of_death: {person.get('place_of_death')}")
            logger.info(f"  - home_town: {person.get('home_town')}")
            logger.info(f"  - origin_location: {person.get('origin_location')}")
            logger.info(f"  - nationality: {person.get('nationality')}")
            logger.info(f"  - religion: {person.get('religion')}")
            logger.info(f"  - occupation: {person.get('occupation')}")
            logger.info(f"  - education: {person.get('education')}")
            logger.info(f"  - events: {person.get('events')}")
            logger.info(f"  - titles: {person.get('titles')}")
            logger.info(f"  - blood_type: {person.get('blood_type')}")
            logger.info(f"  - genetic_disease: {person.get('genetic_disease')}")
            logger.info(f"  - grave_info: {person.get('grave_info')}")
            logger.info(f"  - contact: {person.get('contact')}")
            logger.info(f"  - social: {person.get('social')}")
            logger.info(f"  - note: {person.get('note')}")
            ancestors_chain_len = len(person.get('ancestors_chain', []))
            logger.info(f'  - ancestors_chain: {ancestors_chain_len} records')
            if ancestors_chain_len > 0:
                logger.info(f"  - ancestors_chain details: {[a.get('full_name', 'N/A') for a in person.get('ancestors_chain', [])[:5]]}")
            else:
                has_parents = person.get('father_id') or person.get('mother_id') or person.get('father_name') or person.get('mother_name')
                if has_parents:
                    logger.warning(f"  - ancestors_chain is EMPTY for {person_id} but person has parent information (father_id={person.get('father_id')}, mother_id={person.get('mother_id')})")
                else:
                    logger.debug(f'  - ancestors_chain is EMPTY for {person_id} (no parent relationships in database - this is normal)')

            def clean_value(v):
                """Helper function để clean nested values"""
                if v is None:
                    return None
                elif isinstance(v, (str, int, float, bool)):
                    return v
                elif isinstance(v, (date, datetime)):
                    return v.strftime('%Y-%m-%d')
                else:
                    return str(v)
            try:
                clean_person = {}
                for key, value in person.items():
                    if value is None:
                        clean_person[key] = None
                    elif isinstance(value, (str, int, float, bool)):
                        clean_person[key] = value
                    elif isinstance(value, (date, datetime)):
                        clean_person[key] = value.strftime('%Y-%m-%d')
                    elif isinstance(value, list):
                        if key == 'ancestors_chain' or key == 'ancestors':
                            clean_person[key] = []
                            for item in value:
                                if isinstance(item, dict):
                                    clean_item = {}
                                    for k, v in item.items():
                                        clean_item[k] = clean_value(v)
                                    clean_person[key].append(clean_item)
                                else:
                                    clean_person[key].append(clean_value(item))
                        elif key == 'marriages' or key == 'children':
                            clean_person[key] = []
                            for item in value:
                                if isinstance(item, dict):
                                    clean_item = {}
                                    for k, v in item.items():
                                        clean_item[k] = clean_value(v)
                                    clean_person[key].append(clean_item)
                                else:
                                    clean_person[key].append(clean_value(item))
                        else:
                            clean_person[key] = [clean_value(v) for v in value]
                    elif isinstance(value, dict):
                        clean_person[key] = {k: clean_value(v) for k, v in value.items()}
                    else:
                        clean_person[key] = clean_value(value)

                is_admin = current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
                if not is_admin:
                    if 'phone' in clean_person:
                        clean_person['phone'] = None
                    if 'email' in clean_person:
                        clean_person['email'] = None
                    if 'contact' in clean_person:  # Fix F2: contact chứa SĐT — PII, chỉ admin xem
                        clean_person['contact'] = None

                return jsonify(clean_person)
            except Exception as e:
                logger.error(f'Error serializing person data for {person_id}: {e}')
                import traceback
                logger.error(traceback.format_exc())
                basic_person = {'person_id': person.get('person_id'), 'full_name': person.get('full_name'), 'generation_level': person.get('generation_level'), 'error': 'Có lỗi khi xử lý dữ liệu'}
                return (jsonify(basic_person), 500)
        return (jsonify({'error': 'Không tìm thấy'}), 404)
    except Error as e:
        logger.error(f'Database error in /api/person/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Database error: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/person/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Unexpected error: {str(e)}'}), 500)
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()
def search_persons():
    """
    Search persons by name, alias, generation_level, or person_id (schema mới)
    
    Hỗ trợ:
    - Case-insensitive search (MySQL COLLATE utf8mb4_unicode_ci)
    - Person_ID variants: P-7-654, p-7-654, 7-654, 654
    - Trim khoảng trắng tự động
    - Đồng bộ với /api/members (dùng cùng helper load_relationship_data)
    """
    q = request.args.get('q', '').strip() or request.args.get('query', '').strip()
    if not q:
        return jsonify([])
    try:
        generation_param = request.args.get('generation')
        if generation_param:
            generation_level = validate_integer(generation_param, min_val=0, max_val=50, default=None)
        else:
            generation_level = None
    except (ValueError, TypeError):
        generation_level = None
    try:
        limit = validate_integer(request.args.get('limit', 50), min_val=1, max_val=50, default=50)
    except ValueError:
        limit = 50
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        normalized_query, person_id_patterns = normalize_search_query(q)
        search_pattern = f'%{normalized_query}%'
        where_conditions = ['p.full_name LIKE %s COLLATE utf8mb4_unicode_ci', 'p.alias LIKE %s COLLATE utf8mb4_unicode_ci']
        where_params = [search_pattern, search_pattern]
        if person_id_patterns:
            person_id_conditions = ' OR '.join(['p.person_id LIKE %s COLLATE utf8mb4_unicode_ci'] * len(person_id_patterns))
            where_conditions.append(f'({person_id_conditions})')
            where_params.extend(person_id_patterns)
        else:
            where_conditions.append('p.person_id LIKE %s COLLATE utf8mb4_unicode_ci')
            where_params.append(search_pattern)
        where_clause = '(' + ' OR '.join(where_conditions) + ')'
        if generation_level:
            where_clause += ' AND p.generation_level = %s'
            where_params.append(generation_level)
        query_sql = f"\n                SELECT\n                    p.person_id,\n                    p.full_name,\n                    p.alias,\n                    p.status,\n                    p.generation_level,\n                    p.home_town,\n                    p.gender,\n                p.father_mother_id AS fm_id,\n                p.birth_date_solar,\n                p.death_date_solar,\n                    -- Cha từ relationships (GROUP_CONCAT để đồng nhất với /api/members)\n                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')\n                     FROM relationships r \n                     JOIN persons parent ON r.parent_id = parent.person_id \n                     WHERE r.child_id = p.person_id AND r.relation_type = 'father') AS father_name,\n                    -- Mẹ từ relationships (GROUP_CONCAT để đồng nhất với /api/members)\n                    (SELECT GROUP_CONCAT(DISTINCT parent.full_name SEPARATOR ', ')\n                     FROM relationships r \n                     JOIN persons parent ON r.parent_id = parent.person_id \n                     WHERE r.child_id = p.person_id AND r.relation_type = 'mother') AS mother_name\n                FROM persons p\n            WHERE {where_clause}\n                ORDER BY p.generation_level, p.full_name\n                LIMIT %s\n        "
        where_params.append(limit)
        cursor.execute(query_sql, tuple(where_params))
        results = cursor.fetchall()
        logger.debug('Loading all relationship data using shared helper for /api/search...')
        relationship_data = load_relationship_data(cursor)
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        seen_ids = set()
        unique_results = []
        for row in results:
            person_id = row.get('person_id')
            if person_id and person_id not in seen_ids:
                seen_ids.add(person_id)
                spouse_names = get_preferred_spouse_names(relationship_data, person_id)
                children = children_map.get(person_id, [])
                siblings = siblings_map.get(person_id, [])
                row['generation_number'] = row.get('generation_level')
                row['spouses'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                row['spouse'] = '; '.join(spouse_names) if spouse_names else None
                row['children'] = '; '.join(children) if children else None
                row['children_string'] = '; '.join(children) if children else None
                row['siblings'] = '; '.join(siblings) if siblings else None
                row['fm_id'] = row.get('father_mother_id')
                unique_results.append(row)
            elif person_id in seen_ids:
                logger.debug(f"Duplicate person_id={person_id} in search results for query='{q}'")
        logger.info(f"Search query='{q}', generation_level={generation_level}, found={len(results)} rows, {len(unique_results)} unique persons")
        return jsonify(unique_results)
    except Error as e:
        logger.error(f'Error in /api/search: {e}')
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_edit_request():
    """API tạo yêu cầu chỉnh sửa (không cần đăng nhập)"""
    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            personal_image_file = request.files.get('personal_image')
        else:
            data = request.get_json() or {}
            personal_image_file = None
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation')
        content = data.get('content', '').strip()
        if not content:
            return (jsonify({'error': 'Nội dung yêu cầu không được để trống'}), 400)
        connection = get_db_connection()
        if not connection:
            return (jsonify({'error': 'Không thể kết nối database'}), 500)
        try:
            cursor = connection.cursor()
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
            cursor.execute("\n                INSERT INTO edit_requests (person_id, person_name, person_generation, user_id, content, status)\n                VALUES (%s, %s, %s, %s, %s, 'pending')\n            ", (person_id, person_name, person_generation, user_id, content))
            connection.commit()
            return jsonify({'success': True, 'message': 'Yêu cầu đã được gửi thành công'})
        except Error as e:
            return (jsonify({'error': f'Lỗi database: {str(e)}'}), 500)
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        return (jsonify({'error': str(e)}), 500)

def delete_person(person_id):
    """
    Xóa một người (yêu cầu mật khẩu admin)
    Delete a person (requires admin password)
    """
    if not isinstance(person_id, (int, str)):
        return (jsonify({'error': 'Invalid person_id type'}), 400)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        try:
            person_id = validate_person_id(str(person_id))
        except ValueError as e:
            return (jsonify({'error': f'Invalid person_id format: {str(e)}'}), 400)
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        correct_password = os.environ.get('BACKUP_PASSWORD', os.environ.get('ADMIN_PASSWORD', ''))
        if not correct_password:
            logger.error('BACKUP_PASSWORD hoặc ADMIN_PASSWORD chưa được cấu hình')
            return (jsonify({'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
        if not secure_compare(password, correct_password):
            return (jsonify({'error': 'Mật khẩu không đúng'}), 403)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT full_name, generation_level FROM persons WHERE person_id = %s', (person_id,))
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Không tìm thấy người với ID này'}), 404)
        cursor.execute('\n            SELECT full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id = %s\n        ', (person_id,))
        before_data = cursor.fetchone()
        cursor.execute('DELETE FROM persons WHERE person_id = %s', (person_id,))
        connection.commit()
        try:
            if before_data:
                log_activity('DELETE_PERSON', target_type='Person', target_id=person_id, before_data=dict(before_data), after_data=None)
        except Exception as log_error:
            logger.warning(f'Failed to log person delete for {person_id}: {log_error}')
        if cache:
            try:
                cache.delete('api_members_data')
                logger.debug('Cache invalidated after delete_person')
            except Exception as e:
                logger.warning(f'Cache invalidation error (continuing): {e}')
        return jsonify({'success': True, 'message': f"Đã xóa người: {person['full_name']} (Đời {person['generation_level']})", 'person_id': person_id})
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Lỗi khi xóa: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@login_required
def update_person(person_id):
    """
    Update person information and persist relationship changes through the
    normalized members core path.
    """
    if not is_admin_user() and getattr(current_user, 'role', '') != 'editor':
        return (jsonify({'error': 'Khong co quyen cap nhat du lieu'}), 403)
    if not isinstance(person_id, (int, str)):
        return (jsonify({'error': 'Invalid person_id type'}), 400)

    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Khong the ket noi database'}), 500)

    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict()
            personal_image_file = request.files.get('personal_image')
        else:
            data = request.get_json() or {}
            personal_image_file = None

        if not data and not (personal_image_file and getattr(personal_image_file, 'filename', None)):
            return (jsonify({'error': 'Khong co du lieu de cap nhat'}), 400)

        cursor = connection.cursor(dictionary=True)
        try:
            person_id = validate_person_id(str(person_id))
        except ValueError as e:
            return (jsonify({'error': f'Invalid person_id format: {str(e)}'}), 400)

        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        if not cursor.fetchone():
            return (jsonify({'error': 'Khong tim thay nguoi nay'}), 404)

        cursor.execute(
            """
            SELECT full_name, gender, status, generation_level, birth_date_solar,
                   death_date_solar, place_of_death, biography, academic_rank,
                   academic_degree, phone, email, occupation
            FROM persons
            WHERE person_id = %s
            """,
            (person_id,),
        )
        before_data = cursor.fetchone()

        cursor.execute('SHOW COLUMNS FROM persons LIKE "version"')
        has_version = cursor.fetchone() is not None
        if has_version and 'version' in data:
            cursor.execute('SELECT version FROM persons WHERE person_id = %s', (person_id,))
            person = cursor.fetchone() or {}
            try:
                client_version = int(data['version'])
                db_version = person.get('version', 1) or 1
                if client_version != db_version:
                    return (
                        jsonify(
                            {
                                'error': (
                                    f'Xung dot phien ban du lieu (Conflict). '
                                    f'Du lieu da bi thay doi boi nguoi khac '
                                    f'(version hien tai: {db_version}, cua ban: {client_version}). '
                                    'Vui long tai lai trang.'
                                )
                            }
                        ),
                        409,
                    )
            except (ValueError, TypeError):
                pass

        ok, err, code = apply_person_members_update_core(
            connection, cursor, person_id, data, personal_image_file, before_data
        )
        if not ok:
            connection.rollback()
            return (jsonify({'error': err}), code or 400)

        return jsonify({'success': True, 'message': 'Da cap nhat va dong bo du lieu thanh cong!'})
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Loi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        import traceback
        traceback.print_exc()
        return (jsonify({'error': f'Loi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@login_required
def sync_person(person_id):
    """Read back normalized relationships for a person after update."""
    if not is_admin_user() and getattr(current_user, 'role', '') != 'editor':
        return (jsonify({'success': False, 'error': 'Khong co quyen sync du lieu'}), 403)

    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Khong the ket noi database'}), 500)

    try:
        cursor = connection.cursor(dictionary=True)
        try:
            person_id = validate_person_id(str(person_id))
        except ValueError as e:
            return (jsonify({'error': f'Invalid person_id format: {str(e)}'}), 400)

        sync_messages = []
        cursor.execute(
            """
            SELECT person_id, full_name, gender, generation_level
            FROM persons
            WHERE person_id = %s
            """,
            (person_id,),
        )
        person = cursor.fetchone()
        if not person:
            return (jsonify({'error': 'Khong tim thay nguoi nay'}), 404)

        cursor.execute(
            """
            SELECT
                r.relation_type,
                r.parent_id,
                parent.full_name AS parent_name
            FROM relationships r
            LEFT JOIN persons parent ON parent.person_id = r.parent_id
            WHERE r.child_id = %s
              AND r.relation_type IN ('father', 'mother')
            ORDER BY r.relation_type
            """,
            (person_id,),
        )
        parent_rows = cursor.fetchall()
        parent_ids = [row['parent_id'] for row in parent_rows if row.get('parent_id')]

        cursor.execute(
            """
            SELECT child.person_id, child.full_name
            FROM relationships r
            JOIN persons child ON child.person_id = r.child_id
            WHERE r.parent_id = %s
              AND r.relation_type IN ('father', 'mother')
            GROUP BY child.person_id, child.full_name
            ORDER BY child.full_name
            """,
            (person_id,),
        )
        current_children = cursor.fetchall()
        current_children_names = [c['full_name'] for c in current_children]

        cursor.execute(
            """
            SELECT DISTINCT
                CASE
                    WHEN m.husband_id = %s THEN m.wife_id
                    ELSE m.husband_id
                END AS spouse_id,
                spouse.full_name AS spouse_name
            FROM marriages m
            JOIN persons spouse ON spouse.person_id = CASE
                WHEN m.husband_id = %s THEN m.wife_id
                ELSE m.husband_id
            END
            WHERE (m.husband_id = %s OR m.wife_id = %s)
              AND COALESCE(m.status, '') != 'Da ly di'
            ORDER BY spouse.full_name
            """,
            (person_id, person_id, person_id, person_id),
        )
        active_spouses = [row['spouse_name'] for row in cursor.fetchall() if row.get('spouse_name')]

        siblings = []
        if parent_ids:
            placeholders = ','.join(['%s'] * len(parent_ids))
            cursor.execute(
                f"""
                SELECT DISTINCT sibling.person_id, sibling.full_name
                FROM relationships r
                JOIN persons sibling ON sibling.person_id = r.child_id
                WHERE r.parent_id IN ({placeholders})
                  AND r.relation_type IN ('father', 'mother')
                  AND sibling.person_id != %s
                ORDER BY sibling.full_name
                """,
                parent_ids + [person_id],
            )
            siblings = cursor.fetchall()

        sync_messages.append('Da kiem tra du lieu hien tai:')
        sync_messages.append(
            f"- Vo/Chong: {len(active_spouses)} nguoi ({(', '.join(active_spouses) if active_spouses else 'Khong co')})"
        )
        sync_messages.append(
            f"- Con cai: {len(current_children)} nguoi ({(', '.join(current_children_names) if current_children_names else 'Khong co')})"
        )
        if parent_rows:
            parent_names = [row['parent_name'] for row in parent_rows if row.get('parent_name')]
            sync_messages.append(
                f"- Cha/Me: {len(parent_names)} nguoi ({(', '.join(parent_names) if parent_names else 'Khong co')})"
            )
        if siblings:
            siblings_names = [row['full_name'] for row in siblings if row.get('full_name')]
            sync_messages.append(
                f"- Anh/Chi/Em: {len(siblings)} nguoi ({(', '.join(siblings_names) if siblings_names else 'Khong co')})"
            )

        connection.commit()
        message = '\n'.join(sync_messages)
        return jsonify(
            {
                'success': True,
                'message': message,
                'data': {
                    'spouses_count': len(active_spouses),
                    'children_count': len(current_children),
                    'siblings_count': len(siblings),
                    'parents_count': len(parent_rows),
                },
            }
        )
    except Error as e:
        connection.rollback()
        return (jsonify({'error': f'Loi khi dong bo: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def _process_children_spouse_siblings(cursor, person_id, data):
    """
    Helper function để xử lý children, spouse, siblings từ form data
    Parse tên từ textarea (phân cách bằng ;) và tạo relationships/marriages
    """
    try:
        # Chuẩn hóa các chuỗi nhập tay để lưu fallback text (khi không map được person_id).
        children_names = _split_semicolon_values(data.get('children_info')) if 'children_info' in data else None
        spouse_names = _split_semicolon_values(data.get('spouse_info')) if 'spouse_info' in data else None
        siblings_names = _split_semicolon_values(data.get('siblings_info')) if 'siblings_info' in data else None
        father_name_text = (data.get('father_name') or '').strip() if 'father_name' in data else ''
        mother_name_text = (data.get('mother_name') or '').strip() if 'mother_name' in data else ''

        cursor.execute('SELECT gender FROM persons WHERE person_id = %s', (person_id,))
        person_gender = cursor.fetchone()
        person_gender = person_gender['gender'] if person_gender else None
        if 'children_info' in data:
            cursor.execute("\n                SELECT child_id FROM relationships \n                WHERE parent_id = %s AND relation_type IN ('father', 'mother')\n            ", (person_id,))
            old_children = [row['child_id'] for row in cursor.fetchall()]
            if old_children:
                placeholders = ','.join(['%s'] * len(old_children))
                cursor.execute(f'\n                    DELETE FROM relationships \n                    WHERE parent_id = %s AND child_id IN ({placeholders})\n                ', [person_id] + old_children)
            if children_names:
                for child_name in children_names:
                    cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (child_name,))
                    child = cursor.fetchone()
                    if child:
                        child_id = child['person_id']
                        relation_type = 'father' if person_gender == 'Nam' else 'mother'
                        cursor.execute('\n                            INSERT INTO relationships (child_id, parent_id, relation_type)\n                            VALUES (%s, %s, %s)\n                            ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id), relation_type = VALUES(relation_type)\n                        ', (child_id, person_id, relation_type))
        if 'spouse_info' in data:
            cursor.execute('\n                DELETE FROM marriages \n                WHERE husband_id = %s OR wife_id = %s\n            ', (person_id, person_id))
            if spouse_names:
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (spouse_name,))
                    spouse = cursor.fetchone()
                    if spouse:
                        spouse_id = spouse['person_id']
                        cursor.execute("\n                            INSERT INTO marriages (husband_id, wife_id, status)\n                            VALUES (%s, %s, 'active')\n                        ", (person_id, spouse_id))
        # Lưu text fallback cho các trường quan hệ để không mất dữ liệu nhập tay.
        try:
            cursor.execute(
                """
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'spouse_sibling_children'
                """
            )
            table_exists = bool(cursor.fetchone())
            if table_exists:
                cursor.execute(
                    """
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'spouse_sibling_children'
                    """
                )
                ssc_columns = {str((r or {}).get('COLUMN_NAME') or '').strip() for r in (cursor.fetchall() or [])}
                # Tự mở rộng schema nhẹ để lưu text cha/mẹ khi chưa map được quan hệ theo person_id.
                if 'father_name' in data and 'father_name' not in ssc_columns:
                    try:
                        cursor.execute("ALTER TABLE spouse_sibling_children ADD COLUMN father_name VARCHAR(255) NULL")
                        ssc_columns.add('father_name')
                    except Exception as e:
                        logger.debug(f'Could not add father_name column to spouse_sibling_children: {e}')
                if 'mother_name' in data and 'mother_name' not in ssc_columns:
                    try:
                        cursor.execute("ALTER TABLE spouse_sibling_children ADD COLUMN mother_name VARCHAR(255) NULL")
                        ssc_columns.add('mother_name')
                    except Exception as e:
                        logger.debug(f'Could not add mother_name column to spouse_sibling_children: {e}')
                row_payload = {}
                if 'spouse_name' in ssc_columns and spouse_names is not None:
                    row_payload['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                if 'siblings_infor' in ssc_columns and siblings_names is not None:
                    row_payload['siblings_infor'] = '; '.join(siblings_names) if siblings_names else None
                elif 'siblings_info' in ssc_columns and siblings_names is not None:
                    row_payload['siblings_info'] = '; '.join(siblings_names) if siblings_names else None
                if 'children_infor' in ssc_columns and children_names is not None:
                    row_payload['children_infor'] = '; '.join(children_names) if children_names else None
                elif 'children_info' in ssc_columns and children_names is not None:
                    row_payload['children_info'] = '; '.join(children_names) if children_names else None
                if 'father_name' in ssc_columns and 'father_name' in data:
                    row_payload['father_name'] = father_name_text if father_name_text else None
                if 'mother_name' in ssc_columns and 'mother_name' in data:
                    row_payload['mother_name'] = mother_name_text if mother_name_text else None

                if row_payload:
                    cols = ['person_id'] + list(row_payload.keys())
                    vals = [person_id] + [row_payload[k] for k in row_payload.keys()]
                    placeholders = ', '.join(['%s'] * len(cols))
                    update_clause = ', '.join([f"{c} = VALUES({c})" for c in row_payload.keys()])
                    cursor.execute(
                        f"INSERT INTO spouse_sibling_children ({', '.join(cols)}) VALUES ({placeholders}) "
                        f"ON DUPLICATE KEY UPDATE {update_clause}",
                        vals,
                    )
        except Exception as relation_text_error:
            err_code = relation_text_error.errno if hasattr(relation_text_error, 'errno') else None
            logger.warning(f'Error saving relation text fallback for {person_id}: [{err_code}] {relation_text_error}')
    except Exception as e:
        error_code = e.errno if hasattr(e, 'errno') else None
        error_msg = str(e)
        logger.warning(f'Error processing children/spouse/siblings for {person_id}: [{error_code}] {error_msg}')

def create_person():
    """API thêm thành viên mới - Yêu cầu mật khẩu"""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        password = data.get('password', '').strip()
        personal_image_file = request.files.get('personal_image')
    else:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        personal_image_file = None
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    if 'password' in data:
        del data['password']
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    cursor = None
    try:
        if not data:
            return (jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400)
        cursor = connection.cursor(dictionary=True)
        person_id = data.get('person_id') or data.get('csv_id')
        if person_id:
            person_id = str(person_id).strip()
            cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
            if cursor.fetchone():
                return (jsonify({'success': False, 'error': f'person_id {person_id} đã tồn tại'}), 400)
        else:
            generation_num = data.get('generation_number')
            if generation_num is not None and str(generation_num).strip() != '':
                cursor.execute("\n                    SELECT MAX(CAST(SUBSTRING_INDEX(person_id, '-', -1) AS UNSIGNED)) as max_num\n                    FROM persons \n                    WHERE person_id LIKE %s\n                ", (f'P-{generation_num}-%',))
                result = cursor.fetchone()
                next_num = (result['max_num'] or 0) + 1
                person_id = f'P-{generation_num}-{next_num}'
            else:
                return (jsonify({'success': False, 'error': 'Cần có person_id hoặc generation_number để tạo ID'}), 400)
        cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n        ")
        columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
        insert_fields = ['person_id']
        insert_values = [person_id]
        if 'full_name' in columns:
            full_name = data.get('full_name')
            if full_name:
                full_name = sanitize_string(str(full_name), max_length=255, allow_empty=False)
            insert_fields.append('full_name')
            insert_values.append(full_name)
        if 'gender' in columns:
            gender = data.get('gender')
            if gender and gender not in ['M', 'F', 'Male', 'Female', 'Nam', 'Nữ']:
                return (jsonify({'success': False, 'error': 'Invalid gender value'}), 400)
            insert_fields.append('gender')
            insert_values.append(gender)
        if 'status' in columns:
            status = data.get('status', 'Không rõ')
            if status and len(str(status)) > 50:
                status = str(status)[:50]
            insert_fields.append('status')
            insert_values.append(status)
        if 'generation_level' in columns and 'generation_number' in data:
            gn = data['generation_number']
            if gn is not None and (not isinstance(gn, str) or gn.strip() != ''):
                insert_fields.append('generation_level')
                insert_values.append(gn)
        if 'father_mother_id' in columns:
            insert_fields.append('father_mother_id')
            insert_values.append(data.get('fm_id'))
        elif 'fm_id' in columns:
            insert_fields.append('fm_id')
            insert_values.append(data.get('fm_id'))
        # Nhánh: nếu persons có cột branch_name thì lưu thẳng, không phụ thuộc bảng branches
        if 'branch_name' in columns and data.get('branch_name'):
            insert_fields.append('branch_name')
            insert_values.append(str(data.get('branch_name')).strip())
        # Nhánh: map branch_name -> branch_id (tự tạo branch nếu chưa có)
        if 'branch_id' in columns and data.get('branch_name'):
            try:
                # Ensure branches table exists before writing
                cursor.execute("\n                    SELECT TABLE_NAME FROM information_schema.TABLES\n                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'branches'\n                    LIMIT 1\n                ")
                if cursor.fetchone():
                    branch_id = get_or_create_branch(cursor, data.get('branch_name'))
                    insert_fields.append('branch_id')
                    insert_values.append(branch_id)
            except Exception as e:
                logger.warning(f'Could not set branch_id on create_person: {e}')
        if 'birth_date_solar' in columns and data.get('birth_date_solar'):
            insert_fields.append('birth_date_solar')
            birth_date = data.get('birth_date_solar').strip()
            if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                birth_date = f'{birth_date}-01-01'
            insert_values.append(birth_date if birth_date else None)
        if 'death_date_solar' in columns and data.get('death_date_solar'):
            insert_fields.append('death_date_solar')
            death_date = data.get('death_date_solar').strip()
            if death_date and len(death_date) == 4 and death_date.isdigit():
                death_date = f'{death_date}-01-01'
            insert_values.append(death_date if death_date else None)
        if 'place_of_death' in columns:
            insert_fields.append('place_of_death')
            insert_values.append(data.get('place_of_death'))
        if 'biography' in columns:
            insert_fields.append('biography')
            biography = data.get('biography', '').strip() if data.get('biography') else None
            insert_values.append(biography if biography else None)
        if 'academic_rank' in columns:
            insert_fields.append('academic_rank')
            academic_rank = data.get('academic_rank', '').strip() if data.get('academic_rank') else None
            insert_values.append(academic_rank if academic_rank else None)
        if 'academic_degree' in columns:
            insert_fields.append('academic_degree')
            academic_degree = data.get('academic_degree', '').strip() if data.get('academic_degree') else None
            insert_values.append(academic_degree if academic_degree else None)
        if 'phone' in columns:
            insert_fields.append('phone')
            phone = data.get('phone', '').strip() if data.get('phone') else None
            insert_values.append(phone if phone else None)
        if 'email' in columns:
            insert_fields.append('email')
            email = data.get('email', '').strip() if data.get('email') else None
            if email and '@' not in email:
                return (jsonify({'success': False, 'error': 'Email không hợp lệ'}), 400)
            insert_values.append(email if email else None)
        if 'occupation' in columns:
            insert_fields.append('occupation')
            occupation = data.get('occupation', '').strip() if data.get('occupation') else None
            insert_values.append(occupation if occupation else None)
        if personal_image_file and personal_image_file.filename:
            personal_image_file.seek(0, os.SEEK_END)
            file_size = personal_image_file.tell()
            personal_image_file.seek(0)
            if file_size > 2 * 1024 * 1024:
                return (jsonify({'success': False, 'error': 'Kích thước file ảnh vượt quá 2MB'}), 400)
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
            if '.' not in personal_image_file.filename or personal_image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return (jsonify({'success': False, 'error': 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'}), 400)
            from datetime import datetime
            import hashlib
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_hash = hashlib.md5(f'{person_id}_{personal_image_file.filename}'.encode()).hexdigest()[:8]
            extension = personal_image_file.filename.rsplit('.', 1)[1].lower()
            safe_filename = secure_filename(f'personal_{person_id}_{timestamp}_{filename_hash}.{extension}')
            volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            if volume_mount_path and os.path.exists(volume_mount_path):
                base_images_dir = volume_mount_path
            else:
                base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
            personal_dir = os.path.join(base_images_dir, 'personal')
            os.makedirs(personal_dir, exist_ok=True)
            file_path = os.path.join(personal_dir, safe_filename)
            personal_image_file.save(file_path)
            image_url = f'/static/images/personal/{safe_filename}'
            if 'personal_image_url' in columns:
                insert_fields.append('personal_image_url')
                insert_values.append(image_url)
            elif 'personal_image' in columns:
                insert_fields.append('personal_image')
                insert_values.append(image_url)
        placeholders = ','.join(['%s'] * len(insert_values))
        insert_query = f"INSERT INTO persons ({', '.join(insert_fields)}) VALUES ({placeholders})"
        cursor.execute(insert_query, insert_values)
        if data.get('father_name') or data.get('mother_name'):
            father_id = None
            mother_id = None
            if data.get('father_name'):
                cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['father_name'],))
                father = cursor.fetchone()
                if father:
                    father_id = father['person_id']
            if data.get('mother_name'):
                cursor.execute('SELECT person_id FROM persons WHERE full_name = %s LIMIT 1', (data['mother_name'],))
                mother = cursor.fetchone()
                if mother:
                    mother_id = mother['person_id']
            if father_id:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'father')\n                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n                ", (person_id, father_id))
            if mother_id:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'mother')\n                    ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)\n                ", (person_id, mother_id))
        _process_children_spouse_siblings(cursor, person_id, data)
        connection.commit()
        try:
            cursor.execute('\n                SELECT full_name, gender, status, generation_level, birth_date_solar,\n                       death_date_solar, place_of_death, biography, academic_rank,\n                       academic_degree, phone, email, occupation\n                FROM persons \n                WHERE person_id = %s\n            ', (person_id,))
            person_data = cursor.fetchone()
            if person_data:
                log_person_create(person_id, dict(person_data))
        except Exception as log_error:
            logger.warning(f'Failed to log person create for {person_id}: {log_error}')
        if cache:
            try:
                cache.delete('api_members_data')
                logger.debug('Cache invalidated after create_person')
            except Exception as e:
                logger.warning(f'Cache invalidation error (continuing): {e}')
        return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def apply_person_members_update_core(connection, cursor, person_id, data, personal_image_file=None, before_data=None):
    """
    Logic cập nhật một thành viên (members portal). Dùng cho PUT /api/persons/<id> và bulk Update SLL.
    Thành công: commit, ghi log, xóa cache; trả về (True, None, None).
    Lỗi validate: trả (False, message, http_code), không commit.
    """
    if before_data is None:
        cursor.execute(
            """
            SELECT full_name, gender, status, generation_level, birth_date_solar,
                   death_date_solar, place_of_death, biography, academic_rank,
                   academic_degree, phone, email, occupation
            FROM persons
            WHERE person_id = %s
            """,
            (person_id,),
        )
        before_data = cursor.fetchone()

    has_csv_id = False
    if data.get('csv_id'):
        cursor.execute("\n                SELECT COLUMN_NAME \n                FROM information_schema.COLUMNS \n                WHERE TABLE_SCHEMA = DATABASE() \n                AND TABLE_NAME = 'persons'\n                AND COLUMN_NAME = 'csv_id'\n            ")
        has_csv_id = bool(cursor.fetchone())
        if has_csv_id:
            cursor.execute('SELECT person_id FROM persons WHERE csv_id = %s AND person_id != %s', (data['csv_id'], person_id))
            if cursor.fetchone():
                return (False, f"ID {data['csv_id']} đã tồn tại", 400)
        else:
            pass
    cursor.execute("\n            SELECT COLUMN_NAME \n            FROM information_schema.COLUMNS \n            WHERE TABLE_SCHEMA = DATABASE() \n            AND TABLE_NAME = 'persons'\n        ")
    columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
    update_fields = []
    update_values = []
    if 'full_name' in columns and 'full_name' in data:
        full_name = data.get('full_name')
        if full_name:
            full_name = sanitize_string(str(full_name), max_length=255, allow_empty=False)
        update_fields.append('full_name = %s')
        update_values.append(full_name)
    if 'gender' in columns and 'gender' in data:
        gender = data.get('gender')
        if gender and gender not in ['M', 'F', 'Male', 'Female', 'Nam', 'Nữ']:
            return (False, 'Invalid gender value', 400)
        update_fields.append('gender = %s')
        update_values.append(gender)
    if 'status' in columns and 'status' in data:
        update_fields.append('status = %s')
        update_values.append(data.get('status'))
    # Chỉ cập nhật csv_id khi schema hỗ trợ để tương thích DB cũ.
    if has_csv_id and 'csv_id' in columns and 'csv_id' in data:
        csv_id = str(data.get('csv_id') or '').strip()
        update_fields.append('csv_id = %s')
        update_values.append(csv_id if csv_id else None)
    if 'generation_level' in columns and 'generation_number' in data:
        gn = data['generation_number']
        if gn is not None and (not isinstance(gn, str) or gn.strip() != ''):
            update_fields.append('generation_level = %s')
            update_values.append(gn)
    # Nhánh: nếu persons có cột branch_name thì lưu thẳng, không phụ thuộc bảng branches
    branch_code_to_name = {
        '0': 'Tổ tiên',
        '1': 'Một',
        '2': 'Hai',
        '3': 'Ba',
        '4': 'Bốn',
        '5': 'Năm',
        '6': 'Sáu',
        '7': 'Bảy',
        '-1': 'Khác',
    }

    if 'branch_name' in columns and 'branch_name' in data:
        update_fields.append('branch_name = %s')
        v = data.get('branch_name')
        v = str(v).strip() if v is not None else None
        if v in branch_code_to_name:
            v = branch_code_to_name[v]
        update_values.append(v if v else None)
    # Nhánh: map branch_name -> branch_id (tự tạo branch nếu chưa có)
    if 'branch_id' in columns and 'branch_name' in data:
        try:
            cursor.execute("\n                    SELECT TABLE_NAME FROM information_schema.TABLES\n                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'branches'\n                    LIMIT 1\n                ")
            if cursor.fetchone():
                bn = data.get('branch_name')
                bn = str(bn).strip() if bn is not None else bn
                if bn in branch_code_to_name:
                    bn = branch_code_to_name[bn]
                branch_id = get_or_create_branch(cursor, bn) if bn else None
                update_fields.append('branch_id = %s')
                update_values.append(branch_id)
        except Exception as e:
            logger.warning(f'Could not set branch_id on update_person_members: {e}')
    if 'birth_date_solar' in columns and 'birth_date_solar' in data:
        update_fields.append('birth_date_solar = %s')
        birth_date = data.get('birth_date_solar', '').strip() if data.get('birth_date_solar') else ''
        if birth_date and len(birth_date) == 4 and birth_date.isdigit():
            birth_date = f'{birth_date}-01-01'
        update_values.append(birth_date if birth_date else None)
    if 'death_date_solar' in columns and 'death_date_solar' in data:
        update_fields.append('death_date_solar = %s')
        death_date = data.get('death_date_solar', '').strip() if data.get('death_date_solar') else ''
        if death_date and len(death_date) == 4 and death_date.isdigit():
            death_date = f'{death_date}-01-01'
        update_values.append(death_date if death_date else None)
    if 'place_of_death' in columns and 'place_of_death' in data:
        update_fields.append('place_of_death = %s')
        update_values.append(data.get('place_of_death'))
    if 'biography' in columns and 'biography' in data:
        update_fields.append('biography = %s')
        biography = data.get('biography', '').strip() if data.get('biography') else None
        update_values.append(biography if biography else None)
    if 'academic_rank' in columns and 'academic_rank' in data:
        update_fields.append('academic_rank = %s')
        academic_rank = data.get('academic_rank', '').strip() if data.get('academic_rank') else None
        update_values.append(academic_rank if academic_rank else None)
    if 'academic_degree' in columns and 'academic_degree' in data:
        update_fields.append('academic_degree = %s')
        academic_degree = data.get('academic_degree', '').strip() if data.get('academic_degree') else None
        update_values.append(academic_degree if academic_degree else None)
    if 'phone' in columns and 'phone' in data:
        update_fields.append('phone = %s')
        phone = data.get('phone', '').strip() if data.get('phone') else None
        update_values.append(phone if phone else None)
    if 'email' in columns and 'email' in data:
        update_fields.append('email = %s')
        email = data.get('email', '').strip() if data.get('email') else None
        if email and '@' not in email:
            return (False, 'Email không hợp lệ', 400)
        update_values.append(email if email else None)
    if 'occupation' in columns and 'occupation' in data:
        update_fields.append('occupation = %s')
        occupation = data.get('occupation', '').strip() if data.get('occupation') else None
        update_values.append(occupation if occupation else None)
    if 'alias' in columns and 'alias' in data:
        update_fields.append('alias = %s')
        av = data.get('alias')
        if av:
            av = sanitize_string(str(av), max_length=255, allow_empty=True)
        update_values.append(av if av else None)
    if 'birth_date_lunar' in columns and 'birth_date_lunar' in data:
        update_fields.append('birth_date_lunar = %s')
        bd = data.get('birth_date_lunar')
        if bd is not None and not isinstance(bd, str):
            bd = str(bd).strip()
        else:
            bd = (bd or '').strip() if bd else ''
        if bd and len(bd) == 4 and bd.isdigit():
            bd = f'{bd}-01-01'
        update_values.append(bd if bd else None)
    if 'death_date_lunar' in columns and 'death_date_lunar' in data:
        update_fields.append('death_date_lunar = %s')
        dd = data.get('death_date_lunar')
        if dd is not None and not isinstance(dd, str):
            dd = str(dd).strip()
        else:
            dd = (dd or '').strip() if dd else ''
        if dd and len(dd) == 4 and dd.isdigit():
            dd = f'{dd}-01-01'
        update_values.append(dd if dd else None)
    if 'grave_info' in columns and ('grave_info' in data or 'grave' in data):
        update_fields.append('grave_info = %s')
        gv = data.get('grave_info') if 'grave_info' in data else data.get('grave')
        if gv is not None:
            gv = str(gv).strip() if str(gv).strip() else None
        update_values.append(gv)
    if (
        'personal_image_url' in columns
        and 'personal_image_url' in data
        and data.get('personal_image_url')
        and not (personal_image_file and getattr(personal_image_file, 'filename', None))
    ):
        update_fields.append('personal_image_url = %s')
        update_values.append(str(data['personal_image_url']).strip())
    elif (
        'personal_image' in columns
        and 'personal_image_url' in data
        and data.get('personal_image_url')
        and not (personal_image_file and getattr(personal_image_file, 'filename', None))
    ):
        update_fields.append('personal_image = %s')
        update_values.append(str(data['personal_image_url']).strip())
    if personal_image_file and personal_image_file.filename:
        personal_image_file.seek(0, os.SEEK_END)
        file_size = personal_image_file.tell()
        personal_image_file.seek(0)
        if file_size > 2 * 1024 * 1024:
            return (False, 'Kích thước file ảnh vượt quá 2MB', 400)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if '.' not in personal_image_file.filename or personal_image_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return (False, 'Định dạng file không hợp lệ. Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP', 400)
        from datetime import datetime
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename_hash = hashlib.md5(f'{person_id}_{personal_image_file.filename}'.encode()).hexdigest()[:8]
        extension = personal_image_file.filename.rsplit('.', 1)[1].lower()
        safe_filename = secure_filename(f'personal_{person_id}_{timestamp}_{filename_hash}.{extension}')
        volume_mount_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
        if volume_mount_path and os.path.exists(volume_mount_path):
            base_images_dir = volume_mount_path
        else:
            base_images_dir = os.path.join(BASE_DIR, 'static', 'images')
        personal_dir = os.path.join(base_images_dir, 'personal')
        os.makedirs(personal_dir, exist_ok=True)
        file_path = os.path.join(personal_dir, safe_filename)
        personal_image_file.save(file_path)
        image_url = f'/static/images/personal/{safe_filename}'
        if 'personal_image_url' in columns:
            update_fields.append('personal_image_url = %s')
            update_values.append(image_url)
        elif 'personal_image' in columns:
            update_fields.append('personal_image = %s')
            update_values.append(image_url)
    if 'generation_id' in columns and 'generation_number' in data:
        gn = data['generation_number']
        if gn is not None and (not isinstance(gn, str) or gn.strip() != ''):
            cursor.execute('SELECT generation_id FROM generations WHERE generation_number = %s', (gn,))
            gen = cursor.fetchone()
            if gen:
                generation_id = gen['generation_id']
            else:
                cursor.execute('INSERT INTO generations (generation_number) VALUES (%s)', (gn,))
                generation_id = cursor.lastrowid
            update_fields.append('generation_id = %s')
            update_values.append(generation_id)
    if 'father_mother_id' in columns and 'fm_id' in data:
        update_fields.append('father_mother_id = %s')
        update_values.append(data.get('fm_id'))
    elif 'fm_id' in columns and 'fm_id' in data:
        update_fields.append('fm_id = %s')
        update_values.append(data.get('fm_id'))
    if 'family_unit_id' in columns and 'family_unit_id' in data:
        update_fields.append('family_unit_id = %s')
        update_values.append(data.get('family_unit_id') or None)
    if update_fields:
        update_values.append(person_id)
        update_query = f"UPDATE persons SET {', '.join(update_fields)} WHERE person_id = %s"
        cursor.execute(update_query, update_values)
    try:
        _apply_parent_relationship_mutations(cursor, person_id, data)
    except ValueError as e:
        return (False, str(e), 400)
    _process_children_spouse_siblings(cursor, person_id, data)
    connection.commit()
    try:
        cursor.execute('\n                SELECT full_name, gender, status, generation_level, birth_date_solar,\n                       death_date_solar, place_of_death, biography, academic_rank,\n                       academic_degree, phone, email, occupation\n                FROM persons \n                WHERE person_id = %s\n            ', (person_id,))
        after_data = cursor.fetchone()
        if before_data and after_data:
            log_person_update(person_id, dict(before_data), dict(after_data))
    except Exception as log_error:
        logger.warning(f'Failed to log person update for {person_id}: {log_error}')
    if cache:
        try:
            cache.delete('api_members_data')
            logger.debug('Cache invalidated after update_person_members')
        except Exception as e:
            logger.warning(f'Cache invalidation error (continuing): {e}')
    return (True, None, None)


def update_person_members(person_id):
    """API cập nhật thành viên từ trang members - Yêu cầu mật khẩu"""
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        password = data.get('password', '').strip()
        personal_image_file = request.files.get('personal_image')
    else:
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        personal_image_file = None
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    if 'password' in data:
        del data['password']
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        try:
            person_id = validate_person_id(person_id)
        except ValueError as e:
            return (jsonify({'success': False, 'error': f'Invalid person_id format: {str(e)}'}), 400)
        person_id = str(person_id).strip() if person_id else None
        if not person_id:
            return (jsonify({'success': False, 'error': 'person_id không hợp lệ'}), 400)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        existing_person = cursor.fetchone()
        if not existing_person:
            return (jsonify({'success': False, 'error': f'Không tìm thấy person_id: {person_id}'}), 404)
        cursor.execute('\n            SELECT full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id = %s\n        ', (person_id,))
        before_data = cursor.fetchone()
        ok, err, code = apply_person_members_update_core(
            connection, cursor, person_id, data, personal_image_file, before_data
        )
        if not ok:
            connection.rollback()
            return (jsonify({'success': False, 'error': err}), code or 400)
        return jsonify({'success': True, 'message': 'Cập nhật thành viên thành công'})
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def fix_p1_1_parents():
    """Fix relationships cho P-1-1 (Vua Minh Mạng) với Vua Gia Long và Thuận Thiên Cao Hoàng Hậu"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Vua Gia Long%',))
        vua_gia_long = cursor.fetchone()
        if not vua_gia_long:
            cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s OR full_name LIKE %s LIMIT 1', ('%Gia Long%', '%Nguyễn Phúc Ánh%'))
            vua_gia_long = cursor.fetchone()
        cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên%',))
        thuan_thien = cursor.fetchone()
        if not thuan_thien:
            cursor.execute('SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Cao Hoàng Hậu%',))
            thuan_thien = cursor.fetchone()
        cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = 'P-1-1'")
        p1_1 = cursor.fetchone()
        if not p1_1:
            return (jsonify({'success': False, 'error': 'Không tìm thấy P-1-1'}), 404)
        results = {'p1_1': p1_1['full_name'], 'father_found': False, 'mother_found': False, 'father_id': None, 'mother_id': None, 'relationships_created': []}
        cursor.execute("\n            DELETE FROM relationships \n            WHERE child_id = 'P-1-1' AND relation_type IN ('father', 'mother')\n        ")
        if vua_gia_long:
            father_id = vua_gia_long['person_id']
            results['father_found'] = True
            results['father_id'] = father_id
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'father'\n            ", (father_id,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES ('P-1-1', %s, 'father')\n                ", (father_id,))
                results['relationships_created'].append(f"Father: {vua_gia_long.get('full_name', father_id)}")
        if thuan_thien:
            mother_id = thuan_thien['person_id']
            results['mother_found'] = True
            results['mother_id'] = mother_id
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = 'P-1-1' AND parent_id = %s AND relation_type = 'mother'\n            ", (mother_id,))
            existing = cursor.fetchone()
            if not existing:
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES ('P-1-1', %s, 'mother')\n                ", (mother_id,))
                results['relationships_created'].append(f"Mother: {thuan_thien.get('full_name', mother_id)}")
        connection.commit()
        if not results['father_found']:
            results['error'] = 'Không tìm thấy Vua Gia Long trong database'
        if not results['mother_found']:
            results['error'] = (results.get('error', '') + '; ' if results.get('error') else '') + 'Không tìm thấy Thuận Thiên Cao Hoàng Hậu trong database'
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        connection.rollback()
        import traceback
        print(f'ERROR fixing P-1-1 parents: {e}')
        print(traceback.format_exc())
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def update_genealogy_info():
    """
    API để bổ sung thông tin hôn phối và tổ tiên:
    - Vua Minh Mạng: hôn phối với Tiệp dư Nguyễn Thị Viên, bố là Vua Gia Long, mẹ là Thuận Thiên Cao Hoàng Hậu
    - Kỳ Ngoại Hầu Hường Phiêu: (cần thông tin hôn phối)
    - Hường Chiêm: (cần thông tin hôn phối)
    """
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        cursor = connection.cursor(dictionary=True)
        results = {'marriages_added': [], 'relationships_added': [], 'errors': []}
        cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = 'P-1-1'")
        vua_minh_mang = cursor.fetchone()
        if not vua_minh_mang:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Minh Mạng%',))
            vua_minh_mang = cursor.fetchone()
        if not vua_minh_mang:
            return (jsonify({'success': False, 'error': 'Không tìm thấy Vua Minh Mạng'}), 404)
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Tiệp dư Nguyễn Thị Viên%',))
        tep_du = cursor.fetchone()
        if not tep_du:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Nguyễn Thị Viên%',))
            tep_du = cursor.fetchone()
        if tep_du:
            cursor.execute('\n                SELECT * FROM marriages \n                WHERE (husband_id = %s AND wife_id = %s)\n                   OR (husband_id = %s AND wife_id = %s)\n            ', (vua_minh_mang['person_id'], tep_du['person_id'], tep_du['person_id'], vua_minh_mang['person_id']))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO marriages (husband_id, wife_id) VALUES (%s, %s)', (vua_minh_mang['person_id'], tep_du['person_id']))
                results['marriages_added'].append(f"{vua_minh_mang['full_name']} <-> {tep_du['full_name']}")
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Vua Gia Long%',))
        vua_gia_long = cursor.fetchone()
        if not vua_gia_long:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Gia Long%',))
            vua_gia_long = cursor.fetchone()
        if vua_gia_long:
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = %s AND parent_id = %s AND relation_type = 'father'\n            ", (vua_minh_mang['person_id'], vua_gia_long['person_id']))
            if not cursor.fetchone():
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'father')\n                ", (vua_minh_mang['person_id'], vua_gia_long['person_id']))
                results['relationships_added'].append(f"Father: {vua_gia_long['full_name']}")
        cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên Cao Hoàng Hậu%',))
        thuan_thien = cursor.fetchone()
        if not thuan_thien:
            cursor.execute('SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1', ('%Thuận Thiên%',))
            thuan_thien = cursor.fetchone()
        if thuan_thien:
            cursor.execute("\n                SELECT * FROM relationships \n                WHERE child_id = %s AND parent_id = %s AND relation_type = 'mother'\n            ", (vua_minh_mang['person_id'], thuan_thien['person_id']))
            if not cursor.fetchone():
                cursor.execute("\n                    INSERT INTO relationships (child_id, parent_id, relation_type)\n                    VALUES (%s, %s, 'mother')\n                ", (vua_minh_mang['person_id'], thuan_thien['person_id']))
                results['relationships_added'].append(f"Mother: {thuan_thien['full_name']}")
        connection.commit()
        return jsonify({'success': True, 'message': 'Đã bổ sung thông tin thành công', 'results': results})
    except Exception as e:
        connection.rollback()
        logger.error(f'Error updating genealogy info: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def delete_persons_batch():
    """API xóa nhiều thành viên - Yêu cầu mật khẩu - Tự động backup trước khi xóa"""
    data = request.get_json() or {}
    password = data.get('password', '').strip()
    correct_password = get_members_password()
    if not correct_password:
        logger.error('MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình')
        return (jsonify({'success': False, 'error': 'Cấu hình bảo mật chưa được thiết lập'}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)
    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
    try:
        person_ids = data.get('person_ids', [])
        skip_backup = data.get('skip_backup', False)
        if not person_ids:
            return (jsonify({'success': False, 'error': 'Không có ID nào được chọn'}), 400)
        if not isinstance(person_ids, list):
            return (jsonify({'success': False, 'error': 'person_ids phải là một mảng'}), 400)
        if len(person_ids) > 100:
            return (jsonify({'success': False, 'error': 'Chỉ có thể xóa tối đa 100 thành viên mỗi lần'}), 400)
        validated_ids = []
        for pid in person_ids:
            try:
                if isinstance(pid, str):
                    pid = pid.strip()
                    if not pid:
                        continue
                    if not re.match('^P-\\d+-\\d+$', pid):
                        logger.warning(f'Invalid person_id format: {pid}')
                        continue
                elif isinstance(pid, int):
                    pass
                else:
                    logger.warning(f'Invalid person_id type: {type(pid)}')
                    continue
                validated_ids.append(pid)
            except Exception as e:
                logger.warning(f'Error validating person_id {pid}: {e}')
                continue
        if not validated_ids:
            return (jsonify({'success': False, 'error': 'Không có person_id hợp lệ'}), 400)
        person_ids = validated_ids
        backup_result = None
        if not skip_backup and len(person_ids) > 0:
            try:
                # Backup module lives in scripts/backup_database.py
                from scripts.backup_database import create_backup
                logger.info(f'Tạo backup tự động trước khi xóa {len(person_ids)} thành viên...')
                backup_dir = os.environ.get('BACKUP_DIR', '').strip() or 'backups'
                backup_result = create_backup(backup_dir=backup_dir)
                if backup_result['success']:
                    logger.info(f"✅ Backup thành công: {backup_result['backup_filename']}")
                else:
                    logger.warning(f"⚠️ Backup thất bại: {backup_result.get('error')}")
            except Exception as backup_error:
                logger.warning(f'⚠️ Không thể tạo backup: {backup_error}')
        cursor = connection.cursor(dictionary=True)
        placeholders = ','.join(['%s'] * len(person_ids))
        cursor.execute(f'\n            SELECT person_id, full_name, gender, status, generation_level, birth_date_solar,\n                   death_date_solar, place_of_death, biography, academic_rank,\n                   academic_degree, phone, email, occupation\n            FROM persons \n            WHERE person_id IN ({placeholders})\n        ', tuple(person_ids))
        before_data_list = cursor.fetchall()
        cursor.execute(f'DELETE FROM persons WHERE person_id IN ({placeholders})', tuple(person_ids))
        deleted_count = cursor.rowcount
        connection.commit()
        try:
            for before_data in before_data_list:
                person_id = before_data['person_id']
                log_activity('DELETE_PERSON', target_type='Person', target_id=person_id, before_data=dict(before_data), after_data=None)
        except Exception as log_error:
            logger.warning(f'Failed to log batch delete: {log_error}')
        response = {'success': True, 'message': f'Đã xóa {deleted_count} thành viên'}
        if backup_result and backup_result['success']:
            response['backup_created'] = True
            response['backup_file'] = backup_result['backup_filename']
        elif backup_result:
            response['backup_warning'] = f"Backup thất bại: {backup_result.get('error')}"
        return jsonify(response)
    except Error as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        connection.rollback()
        return (jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
