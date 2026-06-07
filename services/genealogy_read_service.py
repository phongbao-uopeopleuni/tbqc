import logging
import traceback

from flask import jsonify, request
from mysql.connector import Error

from db import get_db_connection
from services.person_helpers import get_preferred_spouse_names
from utils.validation import validate_person_id, validate_integer
from services.person_service import load_relationship_data
from services.genealogy_sync import (
    _collect_person_ids_from_tree_node,
    _fetch_marriage_pairs_in_scope,
)

logger = logging.getLogger(__name__)

NGUYEN_PHUOC_LINEAGE_KEYWORDS = (
    'Vua',
    'Miên',
    'Hồng',
    'Hường',
    'Ưng',
    'Bửu',
    'Vĩnh',
    'Bảo',
    'Quý',
    'Nguyễn Phước',
    'Nguyễn Phúc',
)

try:
    from folder_py.genealogy_tree import (
        build_tree,
        build_ancestors_chain,
        build_descendants,
        build_children_map,
        build_parent_map,
        load_persons_data,
    )
except ImportError as e:
    logger.warning(f'Cannot import genealogy_tree: {e}')
    build_tree = None
    build_ancestors_chain = None
    build_descendants = None
    build_children_map = None
    build_parent_map = None
    load_persons_data = None


def belongs_to_nguyen_phuoc_lineage(person_name):
    if not person_name:
        return False
    return any(keyword in person_name for keyword in NGUYEN_PHUOC_LINEAGE_KEYWORDS)


def get_tree():
    """
    Get genealogy tree from root_id up to max_gen (schema mới).
    Handler chạy trực tiếp trong app; blueprint family_tree gọi hàm này qua _call_app('get_tree').
    """
    if build_tree is None or load_persons_data is None or build_children_map is None:
        logger.error('genealogy_tree functions not available')
        return (
            jsonify(
                {
                    'error': 'Tree functions not available. Please check server logs.',
                    'hint': 'Kiem tra /api/health - module genealogy_tree chua load duoc.',
                }
            ),
            500,
        )

    connection = None
    cursor = None
    try:
        root_id = request.args.get('root_id', 'P-1-1')
        try:
            root_id = validate_person_id(root_id)
        except ValueError:
            root_id = 'P-1-1'

        max_gen_param = request.args.get('max_gen')
        max_generation_param = request.args.get('max_generation')
        if max_gen_param:
            max_gen = validate_integer(max_gen_param, min_val=1, max_val=20, default=5)
        elif max_generation_param:
            max_gen = validate_integer(max_generation_param, min_val=1, max_val=20, default=5)
        else:
            max_gen = 5
    except (ValueError, TypeError) as e:
        logger.error(f'Invalid max_gen or max_generation parameter: {e}')
        return (
            jsonify(
                {
                    'error': 'Invalid max_gen or max_generation parameter. Must be an integer.',
                }
            ),
            400,
        )

    try:
        connection = get_db_connection()
        if not connection:
            logger.error('Cannot connect to database')
            return (
                jsonify(
                    {
                        'error': 'Khong the ket noi database',
                        'hint': 'Kiem tra MySQL dang chay va cau hinh DB. Mo /api/health de xem trang thai.',
                    }
                ),
                503,
            )

        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (root_id,))
        if not cursor.fetchone():
            cursor.execute(
                'SELECT person_id FROM persons ORDER BY generation_level ASC, person_id ASC LIMIT 1'
            )
            first_row = cursor.fetchone()
            if first_row:
                root_id = first_row['person_id']
                logger.info(
                    f'Root {request.args.get("root_id")} not found, using first person: {root_id}'
                )
            else:
                return (
                    jsonify(
                        {
                            'persons': [],
                            'relationships': [],
                            'root_id': None,
                            'message': 'Chưa có dữ liệu người trong cơ sở dữ liệu',
                        }
                    ),
                    200,
                )

        persons_by_id = load_persons_data(cursor)
        logger.info(
            f'Loaded {len(persons_by_id)} persons from database (consistent with /api/members)'
        )
        children_map = build_children_map(cursor)
        logger.info(
            f'Built children map with {len(children_map)} parent-child relationships'
        )
        tree = build_tree(root_id, persons_by_id, children_map, 1, max_gen)
        if not tree:
            logger.error(f'Could not build tree for root_id={root_id}')
            return (
                jsonify(
                    {
                        'error': 'Khong the dung cay gia pha',
                        'hint': f'Root_id {root_id} co the khong co du lieu. Kiem tra bang persons va relationships.',
                    }
                ),
                500,
            )
        try:
            tree_ids = _collect_person_ids_from_tree_node(tree)
            tree["marriage_pairs"] = _fetch_marriage_pairs_in_scope(cursor, tree_ids)
        except Exception as e:
            logger.warning("Could not attach marriage_pairs to /api/tree: %s", e)
            tree["marriage_pairs"] = []
        logger.info(
            f'Built tree for root_id={root_id}, max_gen={max_gen}, nodes={len(persons_by_id)}'
        )
        return jsonify(tree)
    except Error as e:
        logger.error(f'Database error in /api/tree: {e}')
        import traceback

        logger.error(traceback.format_exc())
        return (
            jsonify(
                {
                    'error': f'Loi database: {str(e)}',
                    'hint': 'Kiem tra /api/health',
                }
            ),
            500,
        )
    except Exception as e:
        logger.error(f'Unexpected error in /api/tree: {e}')
        import traceback

        logger.error(traceback.format_exc())
        return (
            jsonify({'error': f'Loi: {str(e)}', 'hint': 'Kiem tra /api/health'}),
            500,
        )
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def get_ancestors(person_id):
    """Get ancestors chain for a person (schema mới - dùng stored procedure)"""
    if not person_id:
        return (jsonify({'error': 'person_id is required'}), 400)
    person_id = str(person_id).strip()
    if not person_id:
        return (jsonify({'error': 'person_id cannot be empty'}), 400)
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            logger.error(f'Cannot connect to database for /api/ancestors/{person_id}')
            return (jsonify({'error': 'Không thể kết nối database'}), 500)
        try:
            max_level = validate_integer(request.args.get('max_level', 10), min_val=1, max_val=20, default=10)
        except (ValueError, TypeError):
            max_level = 10
        cursor = connection.cursor(dictionary=True)
        father_to_add_to_chain = None
        original_person_id = person_id
        try:
            cursor.execute('\n                SELECT person_id, full_name, gender, generation_level, father_mother_id\n                FROM persons WHERE person_id = %s\n            ', (person_id,))
            person_info = cursor.fetchone()
            if not person_info:
                logger.warning(f'Person {person_id} not found in database')
                return (jsonify({'error': f'Person {person_id} not found'}), 404)
            target_person_id = person_id
            person_gender = person_info.get('gender', '').strip().upper() if person_info.get('gender') else ''
            logger.info(f'[API /api/ancestors/{person_id}] Finding father first (gender: {person_gender})')
            father_id = None
            cursor.execute("\n                SELECT r.parent_id\n                FROM relationships r\n                WHERE r.child_id = %s AND r.relation_type = 'father'\n                LIMIT 1\n            ", (person_id,))
            father_rel = cursor.fetchone()
            if father_rel and father_rel.get('parent_id'):
                father_id = father_rel.get('parent_id')
            if not father_id and person_info.get('father_mother_id'):
                cursor.execute("\n                    SELECT person_id\n                    FROM persons\n                    WHERE father_mother_id = %s\n                        AND generation_level < %s\n                        AND (gender = 'Nam' OR gender IS NULL)\n                    ORDER BY generation_level DESC\n                    LIMIT 1\n                ", (person_info.get('father_mother_id'), person_info.get('generation_level', 999)))
                father_fm = cursor.fetchone()
                if father_fm and father_fm.get('person_id'):
                    father_id = father_fm.get('person_id')
            if father_id:
                cursor.execute('\n                    SELECT full_name\n                    FROM persons\n                    WHERE person_id = %s\n                ', (father_id,))
                father_info = cursor.fetchone()
                father_name = father_info.get('full_name', '') if father_info else ''
                is_nguyen_phuoc_lineage = belongs_to_nguyen_phuoc_lineage(father_name)
                if is_nguyen_phuoc_lineage:
                    logger.info(f'[API /api/ancestors/{person_id}] Found father: {father_id} ({father_name}), belongs to Nguyen Phuoc lineage, using father for ancestors search')
                    target_person_id = father_id
                else:
                    logger.info(f"[API /api/ancestors/{person_id}] Father {father_id} ({father_name}) doesn't belong to Nguyen Phuoc lineage, switching to mother's line")
                    mother_id = None
                    cursor.execute("\n                        SELECT r.parent_id\n                        FROM relationships r\n                        WHERE r.child_id = %s AND r.relation_type = 'mother'\n                        LIMIT 1\n                    ", (person_id,))
                    mother_rel = cursor.fetchone()
                    if mother_rel and mother_rel.get('parent_id'):
                        mother_id = mother_rel.get('parent_id')
                    if mother_id:
                        cursor.execute("\n                            SELECT r.parent_id\n                            FROM relationships r\n                            WHERE r.child_id = %s AND r.relation_type = 'father'\n                            LIMIT 1\n                        ", (mother_id,))
                        grandfather_rel = cursor.fetchone()
                        if grandfather_rel and grandfather_rel.get('parent_id'):
                            target_person_id = grandfather_rel.get('parent_id')
                            logger.info(f'[API /api/ancestors/{person_id}] Found maternal grandfather: {target_person_id}, using for ancestors search')
                        else:
                            logger.warning(f'[API /api/ancestors/{person_id}] No maternal grandfather found, using person directly')
                    else:
                        logger.warning(f'[API /api/ancestors/{person_id}] No mother found, using person directly')
                    if father_id:
                        father_to_add_to_chain = father_id
                        logger.info(f'[API /api/ancestors/{person_id}] Storing father_id {father_id} to add to chain later')
            else:
                logger.info(f'[API /api/ancestors/{person_id}] No father found, trying to find maternal grandfather')
                mother_id = None
                cursor.execute("\n                    SELECT r.parent_id\n                    FROM relationships r\n                    WHERE r.child_id = %s AND r.relation_type = 'mother'\n                    LIMIT 1\n                ", (person_id,))
                mother_rel = cursor.fetchone()
                if mother_rel and mother_rel.get('parent_id'):
                    mother_id = mother_rel.get('parent_id')
                if mother_id:
                    cursor.execute("\n                        SELECT r.parent_id\n                        FROM relationships r\n                        WHERE r.child_id = %s AND r.relation_type = 'father'\n                        LIMIT 1\n                    ", (mother_id,))
                    grandfather_rel = cursor.fetchone()
                    if grandfather_rel and grandfather_rel.get('parent_id'):
                        target_person_id = grandfather_rel.get('parent_id')
                        logger.info(f'[API /api/ancestors/{person_id}] Found maternal grandfather: {target_person_id}, using for ancestors search')
                    else:
                        logger.warning(f'[API /api/ancestors/{person_id}] No father or maternal grandfather found, using person directly')
                else:
                    logger.warning(f'[API /api/ancestors/{person_id}] No father or mother found, using person directly')
        except Exception as e:
            logger.error(f'Error checking if person exists: {e}')
            import traceback
            logger.error(traceback.format_exc())
            return (jsonify({'error': f'Database error while checking person: {str(e)}'}), 500)
        ancestors_result = None
        try:
            # sp_get_ancestors còn fallback qua father_mother_id; xem D4 trong plan, không thay đổi cho tới khi có quyết định rõ ở Phase 6/7.
            cursor.callproc('sp_get_ancestors', [target_person_id, max_level])
            for result_set in cursor.stored_results():
                ancestors_result = result_set.fetchall()
                break
        except Exception as e:
            logger.warning(f'Error calling sp_get_ancestors for person_id={target_person_id}: {e}')
            ancestors_result = None
        use_direct_query = True
        if use_direct_query or not ancestors_result or len(ancestors_result) == 0:
            logger.info(f'[API /api/ancestors/{person_id}] Stored procedure returned empty, using direct query fallback (target_person_id={target_person_id})')
            try:
                cursor.execute("\n                    WITH RECURSIVE ancestors AS (\n                        -- Base case: người hiện tại (hoặc cha nếu là con gái)\n                        -- Base case: current person (or father if female)\n                        SELECT \n                            p.person_id,\n                            p.full_name,\n                            p.gender,\n                            p.generation_level,\n                            p.father_mother_id,\n                            0 AS level\n                        FROM persons p\n                        WHERE p.person_id = %s\n                        \n                        UNION ALL\n                        \n                        -- Recursive case: CHA (chỉ theo dòng cha)\n                        SELECT \n                            COALESCE(parent_by_rel.person_id, parent_by_fm.person_id, parent_by_gen.person_id) AS person_id,\n                            COALESCE(parent_by_rel.full_name, parent_by_fm.full_name, parent_by_gen.full_name) AS full_name,\n                            COALESCE(parent_by_rel.gender, parent_by_fm.gender, parent_by_gen.gender) AS gender,\n                            COALESCE(parent_by_rel.generation_level, parent_by_fm.generation_level, parent_by_gen.generation_level) AS generation_level,\n                            COALESCE(parent_by_rel.father_mother_id, parent_by_fm.father_mother_id, parent_by_gen.father_mother_id) AS father_mother_id,\n                            a.level + 1\n                        FROM ancestors a\n                        INNER JOIN persons child ON a.person_id = child.person_id\n                        -- Ưu tiên 1: Tìm cha theo relationships table\n                        LEFT JOIN relationships r ON (\n                            a.person_id = r.child_id\n                            AND r.relation_type = 'father'\n                        )\n                        LEFT JOIN persons parent_by_rel ON (\n                            r.parent_id = parent_by_rel.person_id\n                        )\n                        -- Ưu tiên 2: Tìm cha theo father_mother_id (fallback) - tìm cha gần nhất\n                        LEFT JOIN persons parent_by_fm ON (\n                            parent_by_rel.person_id IS NULL\n                            AND child.father_mother_id IS NOT NULL \n                            AND child.father_mother_id != ''\n                            AND parent_by_fm.father_mother_id = child.father_mother_id\n                            AND parent_by_fm.generation_level < child.generation_level\n                            AND (parent_by_fm.gender = 'Nam' OR parent_by_fm.gender IS NULL)\n                            -- Tìm cha gần nhất (generation_level cao nhất nhưng vẫn < child)\n                            AND parent_by_fm.generation_level = (\n                                SELECT MAX(p2.generation_level)\n                                FROM persons p2\n                                WHERE p2.father_mother_id = child.father_mother_id\n                                    AND p2.generation_level < child.generation_level\n                                    AND (p2.gender = 'Nam' OR p2.gender IS NULL)\n                            )\n                        )\n                        -- Ưu tiên 3: Tìm cha theo generation_level - 1 (suy luận nếu có nhiều người cùng father_mother_id)\n                        -- Đảm bảo tìm được đầy đủ các đời, kể cả khi thiếu thông tin relationships\n                        LEFT JOIN persons parent_by_gen ON (\n                            parent_by_rel.person_id IS NULL\n                            AND parent_by_fm.person_id IS NULL\n                            AND child.father_mother_id IS NOT NULL \n                            AND child.father_mother_id != ''\n                            AND parent_by_gen.father_mother_id = child.father_mother_id\n                            AND parent_by_gen.generation_level = child.generation_level - 1\n                            AND (parent_by_gen.gender = 'Nam' OR parent_by_gen.gender IS NULL)\n                        )\n                        WHERE a.level < %s\n                            AND (parent_by_rel.person_id IS NOT NULL \n                                 OR parent_by_fm.person_id IS NOT NULL \n                                 OR parent_by_gen.person_id IS NOT NULL)\n                    )\n                    SELECT * FROM ancestors \n                    WHERE level > 0 \n                        AND (gender = 'Nam' OR gender IS NULL)\n                    ORDER BY level, generation_level, full_name\n                ", (target_person_id, max_level))
                ancestors_result = cursor.fetchall()
                logger.info(f'[API /api/ancestors/{person_id}] Direct query returned {(len(ancestors_result) if ancestors_result else 0)} rows')
            except Exception as e2:
                logger.error(f'Error in direct query fallback for person_id={person_id}: {e2}')
                import traceback
                logger.error(traceback.format_exc())
                ancestors_result = []
        ancestors_chain = []
        seen_person_ids = set()
        duplicate_count = 0
        logger.info(f'[API /api/ancestors/{person_id}] Stored procedure returned {(len(ancestors_result) if ancestors_result else 0)} rows')
        if ancestors_result:
            generations_found = set()
            for row in ancestors_result:
                if isinstance(row, dict):
                    gen = row.get('generation_level') or row.get('generation_number')
                else:
                    gen = row[3] if len(row) > 3 else None
                if gen:
                    generations_found.add(gen)
            logger.info(f'[API /api/ancestors/{person_id}] Generations found: {sorted(generations_found)}')
        if ancestors_result:
            for row in ancestors_result:
                if isinstance(row, dict):
                    person_id_item = row.get('person_id')
                    gender = row.get('gender')
                    full_name = row.get('full_name', 'N/A')
                    generation_level = row.get('generation_level')
                else:
                    person_id_item = row[0] if len(row) > 0 else None
                    gender = row[2] if len(row) > 2 else None
                    full_name = row[1] if len(row) > 1 else 'N/A'
                    generation_level = row[3] if len(row) > 3 else None
                if person_id_item:
                    person_id_item = str(person_id_item).strip()
                logger.debug(f'[API /api/ancestors/{person_id}] Processing row: person_id={person_id_item}, name={full_name}, gender={gender}, generation={generation_level}')
                if gender:
                    gender_upper = str(gender).upper().strip()
                    if gender_upper not in ['NAM', 'MALE', 'M', '']:
                        logger.debug(f'[API /api/ancestors/{person_id}] Skipping non-father person_id={person_id_item}, gender={gender}, name={full_name}')
                        continue
                if not person_id_item or person_id_item in seen_person_ids:
                    if person_id_item:
                        duplicate_count += 1
                        full_name = row.get('full_name', 'N/A') if isinstance(row, dict) else row[1] if len(row) > 1 else 'N/A'
                        logger.warning(f'Duplicate person_id={person_id_item}, name={full_name} in ancestors chain, skipping')
                    continue
                seen_person_ids.add(person_id_item)
                if isinstance(row, dict):
                    ancestors_chain.append({'person_id': person_id_item, 'full_name': row.get('full_name', ''), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'generation_number': row.get('generation_level'), 'level': row.get('level', 0)})
                else:
                    ancestors_chain.append({'person_id': person_id_item, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'generation_number': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
        logger.debug(f'Loading relationship data for ancestors chain using shared helper...')
        relationship_data = load_relationship_data(cursor)
        parent_data = relationship_data['parent_data']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        enriched_chain = []
        for ancestor in ancestors_chain:
            ancestor_id = ancestor.get('person_id')
            if not ancestor_id:
                enriched_chain.append(ancestor)
                continue
            try:
                rel = parent_data.get(ancestor_id, {'father_name': None, 'mother_name': None})
                ancestor['father_name'] = rel.get('father_name')
                ancestor['mother_name'] = rel.get('mother_name')
                spouse_names = get_preferred_spouse_names(relationship_data, ancestor_id)
                ancestor['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                ancestor['spouse'] = '; '.join(spouse_names) if spouse_names else None
                children = children_map.get(ancestor_id, [])
                ancestor['children'] = '; '.join(children) if children else None
                ancestor['children_string'] = '; '.join(children) if children else None
                siblings = siblings_map.get(ancestor_id, [])
                ancestor['siblings'] = '; '.join(siblings) if siblings else None
                ancestor['siblings_infor'] = '; '.join(siblings) if siblings else None
                try:
                    cursor.execute("\n                        SELECT GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children_names\n                        FROM relationships r\n                        INNER JOIN persons child ON r.child_id = child.person_id\n                        WHERE r.parent_id = %s\n                            AND r.relation_type IN ('father', 'mother')\n                    ", (ancestor_id,))
                    children_info = cursor.fetchone()
                    ancestor['children_infor'] = children_info.get('children_names') if children_info and children_info.get('children_names') else None
                except Exception as e:
                    logger.warning(f'Error fetching children for {ancestor_id}: {e}')
                    ancestor['children_infor'] = None
            except Exception as e:
                logger.error(f'Unexpected error enriching ancestor {ancestor_id}: {e}')
                pass
            enriched_chain.append(ancestor)
        if father_to_add_to_chain:
            try:
                father_already_in_chain = any((a.get('person_id') == father_to_add_to_chain for a in enriched_chain))
                if not father_already_in_chain:
                    cursor.execute('\n                        SELECT person_id, full_name, gender, generation_level, status\n                        FROM persons\n                        WHERE person_id = %s\n                    ', (father_to_add_to_chain,))
                    father_info = cursor.fetchone()
                    if father_info:
                        rel = parent_data.get(father_to_add_to_chain, {'father_name': None, 'mother_name': None})
                        father_entry = {'person_id': father_info.get('person_id'), 'full_name': father_info.get('full_name', ''), 'gender': father_info.get('gender'), 'generation_level': father_info.get('generation_level'), 'generation_number': father_info.get('generation_level'), 'father_name': rel.get('father_name'), 'mother_name': rel.get('mother_name'), 'level': 999}
                        spouse_names = get_preferred_spouse_names(relationship_data, father_to_add_to_chain)
                        father_entry['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
                        children = children_map.get(father_to_add_to_chain, [])
                        father_entry['children'] = '; '.join(children) if children else None
                        siblings = siblings_map.get(father_to_add_to_chain, [])
                        father_entry['siblings'] = '; '.join(siblings) if siblings else None
                        enriched_chain.append(father_entry)
                        logger.info(f'[API /api/ancestors/{person_id}] Added father {father_to_add_to_chain} to ancestors_chain')
            except Exception as e:
                logger.error(f'Error adding father to chain: {e}')
                import traceback
                logger.error(traceback.format_exc())
        enriched_chain.sort(key=lambda x: (x.get('generation_level') or x.get('generation_number') or 999, x.get('level', 0), x.get('person_id') or ''))
        logger.info(f'[API /api/ancestors/{person_id}] Final ancestors_chain length: {len(enriched_chain)}')
        generations_in_chain = set()
        for i, ancestor in enumerate(enriched_chain, 1):
            gen = ancestor.get('generation_level') or ancestor.get('generation_number')
            generations_in_chain.add(gen)
            logger.info(f"  {i}. {ancestor.get('person_id')}: {ancestor.get('full_name')} (Đời {gen})")
        if enriched_chain:
            min_gen = min(generations_in_chain)
            max_gen = max(generations_in_chain)
            expected_gens = set(range(min_gen, max_gen + 1))
            missing_gens = expected_gens - generations_in_chain
            if missing_gens:
                logger.warning(f'[API /api/ancestors/{person_id}] MISSING GENERATIONS: {sorted(missing_gens)} (Present: {sorted(generations_in_chain)})')
            else:
                logger.info(f'[API /api/ancestors/{person_id}] All generations present from {min_gen} to {max_gen}')
        person_info = None
        try:
            cursor.execute('\n                SELECT person_id, full_name, alias, gender, generation_level, status\n                FROM persons\n                WHERE person_id = %s\n            ', (person_id,))
            person_info = cursor.fetchone()
        except Exception as e:
            logger.error(f'Error fetching person_info for {person_id}: {e}')
            import traceback
            logger.error(traceback.format_exc())
            person_info = None
        if person_info:
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            person_info['father_name'] = rel.get('father_name')
            person_info['mother_name'] = rel.get('mother_name')
            spouse_names = get_preferred_spouse_names(relationship_data, person_id)
            person_info['spouse_name'] = '; '.join(spouse_names) if spouse_names else None
            person_info['spouse'] = '; '.join(spouse_names) if spouse_names else None
            children = children_map.get(person_id, [])
            person_info['children'] = '; '.join(children) if children else None
            person_info['children_string'] = '; '.join(children) if children else None
            siblings = siblings_map.get(person_id, [])
            person_info['siblings'] = '; '.join(siblings) if siblings else None
            person_info['siblings_infor'] = '; '.join(siblings) if siblings else None
            person_info['generation_number'] = person_info.get('generation_level')
            person_in_chain = any((a.get('person_id') == person_id for a in enriched_chain))
            if person_in_chain:
                logger.warning(f'Person {person_id} already in ancestors_chain, will be filtered by frontend')
        logger.info(f'Built ancestors chain for person_id={person_id}, length={len(enriched_chain)} (after deduplication, removed {duplicate_count} duplicates)')
        return jsonify({'person': person_info, 'ancestors_chain': enriched_chain})
    except Error as e:
        logger.error(f'Database error in /api/ancestors/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Database error: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/ancestors/{person_id}: {e}')
        import traceback
        logger.error(f'Error traceback: {traceback.format_exc()}')
        return (jsonify({'error': f'Unexpected error: {str(e)}'}), 500)
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()


def get_descendants(person_id):
    """Get descendants of a person (schema mới - dùng stored procedure)"""
    connection = get_db_connection()
    if not connection:
        return (jsonify({'error': 'Không thể kết nối database'}), 500)
    try:
        max_level = validate_integer(request.args.get('max_level', 5), min_val=1, max_val=20, default=5)
    except (ValueError, TypeError):
        max_level = 5
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
        if not cursor.fetchone():
            return (jsonify({'error': f'Person {person_id} not found'}), 404)
        cursor.callproc('sp_get_descendants', [person_id, max_level])
        descendants_result = None
        for result_set in cursor.stored_results():
            descendants_result = result_set.fetchall()
            break
        descendants = []
        if descendants_result:
            for row in descendants_result:
                if isinstance(row, dict):
                    descendants.append({'person_id': row.get('person_id'), 'full_name': row.get('full_name', ''), 'gender': row.get('gender'), 'generation_level': row.get('generation_level'), 'level': row.get('level', 0)})
                else:
                    descendants.append({'person_id': row[0] if len(row) > 0 else None, 'full_name': row[1] if len(row) > 1 else '', 'gender': row[2] if len(row) > 2 else None, 'generation_level': row[3] if len(row) > 3 else None, 'level': row[4] if len(row) > 4 else 0})
        logger.info(f'Built descendants for person_id={person_id}, count={len(descendants)}')
        return jsonify({'person_id': person_id, 'descendants': descendants})
    except Error as e:
        logger.error(f'Error in /api/descendants/{person_id}: {e}')
        return (jsonify({'error': str(e)}), 500)
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
