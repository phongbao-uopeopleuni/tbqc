import logging
import os
from datetime import datetime

from flask import jsonify
from mysql.connector import Error

from audit_log import log_activity
from db import get_db_connection

logger = logging.getLogger(__name__)


def sync_genealogy_from_members():
    """
    API sync dữ liệu Family Tree từ database chuẩn (https://www.phongtuybienquancong.info/members)

    Chức năng:
    - Fetch dữ liệu từ API endpoint /api/members của database chuẩn
    - Sync dữ liệu vào database hiện tại
    - TUYỆT ĐỐI chỉ đọc từ API, KHÔNG sửa đổi database chuẩn

    Returns:
        JSON với thông tin sync: số lượng records, status, message
    """
    logger.info('🔄 API /api/genealogy/sync được gọi - Sync từ database chuẩn (www.phongtuybienquancong.info)')
    connection = None
    cursor = None
    try:
        import requests
        standard_db_url = 'https://www.phongtuybienquancong.info/api/members'
        logger.info(f'📡 Fetching data from: {standard_db_url}')

        # TLS verification: mặc định BẬT (verify=True) — chặn MitM/DNS poisoning
        # chèn dữ liệu giả rồi ghi thẳng vào persons/relationships/marriages.
        #
        # Override hợp pháp (opt-in):
        #   - GENEALOGY_SYNC_CA_BUNDLE=/path/to/ca.pem → dùng CA bundle tùy chỉnh
        #     (self-signed cert nội bộ, mirror, staging host). Vẫn VERIFY.
        #   - GENEALOGY_SYNC_INSECURE_TLS=1           → TẮT verify (dev only).
        #     BỊ CHẶN TRÊN PRODUCTION — dù set vẫn giữ verify=True để không ai
        #     (kể cả admin) vô tình mở lỗ hổng trên môi trường thật.
        ca_bundle = (os.environ.get('GENEALOGY_SYNC_CA_BUNDLE') or '').strip()
        insecure_env = (os.environ.get('GENEALOGY_SYNC_INSECURE_TLS') or '').strip().lower()
        allow_insecure = insecure_env in ('1', 'true', 'yes')
        try:
            from config import is_production_env as _is_prod
        except Exception:
            _is_prod = lambda: False
        if allow_insecure and _is_prod():
            logger.error(
                'GENEALOGY_SYNC_INSECURE_TLS được set trên production — BỎ QUA, '
                'vẫn verify TLS đầy đủ để bảo vệ tính toàn vẹn dữ liệu.'
            )
            allow_insecure = False

        if ca_bundle and os.path.exists(ca_bundle):
            verify_arg = ca_bundle
            logger.info('Sync TLS verify: dùng CA bundle tùy chỉnh %s', ca_bundle)
        elif allow_insecure:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            logger.warning(
                'GENEALOGY_SYNC_INSECURE_TLS=1 (dev only) — TLS verification TẮT '
                'cho /api/genealogy/sync. KHÔNG dùng trên production.'
            )
            verify_arg = False
        else:
            verify_arg = True

        try:
            response = requests.get(standard_db_url, timeout=60, verify=verify_arg)
            response.raise_for_status()
            response_data = response.json()
            if isinstance(response_data, list):
                members_data = response_data
            elif isinstance(response_data, dict) and response_data.get('success') and isinstance(response_data.get('data'), list):
                members_data = response_data['data']
            elif isinstance(response_data, dict) and isinstance(response_data.get('members'), list):
                members_data = response_data['members']
            else:
                logger.error(f'❌ Unexpected response format from {standard_db_url}: {type(response_data)}')
                return (jsonify({'success': False, 'error': f'Dữ liệu từ database chuẩn không đúng định dạng. Expected array or {{success, data}}, got {type(response_data)}'}), 500)
            logger.info(f'📊 Đã fetch {len(members_data)} members từ database chuẩn')
        except requests.exceptions.SSLError as e:
            # TLS verify fail → dữ liệu KHÔNG đáng tin; hủy sync trước khi đụng DB.
            logger.error(
                '❌ TLS verification failed khi sync từ %s: %s. '
                'Dữ liệu không được tin cậy, sync đã hủy.',
                standard_db_url, e,
            )
            return (jsonify({
                'success': False,
                'error': (
                    'Không thể xác minh chứng chỉ TLS của database chuẩn. '
                    'Sync đã hủy để bảo vệ tính toàn vẹn dữ liệu. '
                    'Nếu đang dùng CA nội bộ, cấu hình GENEALOGY_SYNC_CA_BUNDLE.'
                ),
            }), 502)
        except requests.exceptions.RequestException as e:
            logger.error(f'❌ Lỗi khi fetch dữ liệu từ database chuẩn: {e}')
            return (jsonify({'success': False, 'error': f'Không thể kết nối đến database chuẩn: {str(e)}'}), 500)
        connection = get_db_connection()
        if not connection:
            logger.error('❌ Không thể kết nối database')
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT COUNT(*) AS count FROM persons')
        before_persons_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM relationships')
        before_relationships_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM marriages')
        before_marriages_count = cursor.fetchone()['count']
        inserted_persons = 0
        updated_persons = 0
        inserted_relationships = 0
        inserted_marriages = 0
        for member in members_data:
            person_id = member.get('person_id') or member.get('id')
            if not person_id:
                continue
            full_name = member.get('full_name') or member.get('name') or ''
            alias = member.get('alias') or None
            gender = member.get('gender') or None
            generation_level = member.get('generation_level') or member.get('generation') or None
            birth_date_solar = member.get('birth_date_solar') or member.get('birth_date') or None
            death_date_solar = member.get('death_date_solar') or member.get('death_date') or None
            grave_info = member.get('grave_info') or None
            place_of_death = member.get('place_of_death') or None
            home_town = member.get('home_town') or None
            status = member.get('status') or 'Đang sống'
            cursor.execute('SELECT person_id FROM persons WHERE person_id = %s', (person_id,))
            exists = cursor.fetchone()
            if exists:
                cursor.execute('\n                    UPDATE persons SET\n                        full_name = %s,\n                        alias = %s,\n                        gender = %s,\n                        generation_level = %s,\n                        birth_date_solar = %s,\n                        death_date_solar = %s,\n                        grave_info = %s,\n                        place_of_death = %s,\n                        home_town = %s,\n                        status = %s\n                    WHERE person_id = %s\n                ', (full_name, alias, gender, generation_level, birth_date_solar, death_date_solar, grave_info, place_of_death, home_town, status, person_id))
                updated_persons += 1
            else:
                cursor.execute('\n                    INSERT INTO persons (\n                        person_id, full_name, alias, gender, generation_level,\n                        birth_date_solar, death_date_solar, grave_info,\n                        place_of_death, home_town, status\n                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n                ', (person_id, full_name, alias, gender, generation_level, birth_date_solar, death_date_solar, grave_info, place_of_death, home_town, status))
                inserted_persons += 1
            father_id = member.get('father_id')
            mother_id = member.get('mother_id')
            if father_id:
                cursor.execute("\n                    SELECT * FROM relationships \n                    WHERE child_id = %s AND parent_id = %s AND relation_type = 'father'\n                ", (person_id, father_id))
                if not cursor.fetchone():
                    try:
                        cursor.execute("\n                            INSERT INTO relationships (parent_id, child_id, relation_type)\n                            VALUES (%s, %s, 'father')\n                        ", (father_id, person_id))
                        inserted_relationships += 1
                    except Error:
                        pass
            if mother_id:
                cursor.execute("\n                    SELECT * FROM relationships \n                    WHERE child_id = %s AND parent_id = %s AND relation_type = 'mother'\n                ", (person_id, mother_id))
                if not cursor.fetchone():
                    try:
                        cursor.execute("\n                            INSERT INTO relationships (parent_id, child_id, relation_type)\n                            VALUES (%s, %s, 'mother')\n                        ", (mother_id, person_id))
                        inserted_relationships += 1
                    except Error:
                        pass
            spouses = member.get('spouses') or member.get('marriages') or []
            spouse_list = []
            if isinstance(spouses, str):
                spouse_names = [s.strip() for s in spouses.split(';') if s.strip() and s.strip().lower() != 'unknown']
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE (full_name = %s OR alias = %s) AND person_id != %s', (spouse_name, spouse_name, person_id))
                    spouse_row = cursor.fetchone()
                    if spouse_row:
                        spouse_id = spouse_row['person_id']
                        spouse_list.append({'spouse_id': spouse_id, 'spouse_name': spouse_name})
                    else:
                        spouse_list.append({'spouse_name': spouse_name})
            elif isinstance(spouses, list):
                spouse_list = spouses
                for spouse in spouse_list:
                    if isinstance(spouse, dict):
                        spouse_id = spouse.get('spouse_id') or spouse.get('person_id') or spouse.get('id')
                        if spouse_id and spouse_id != person_id:
                            cursor.execute('\n                                SELECT * FROM marriages \n                                WHERE (husband_id = %s AND wife_id = %s)\n                                OR (husband_id = %s AND wife_id = %s)\n                            ', (person_id, spouse_id, spouse_id, person_id))
                            if not cursor.fetchone():
                                try:
                                    cursor.execute('\n                                        INSERT INTO marriages (husband_id, wife_id)\n                                        VALUES (%s, %s)\n                                    ', (person_id, spouse_id))
                                    inserted_marriages += 1
                                except Error:
                                    pass
        for member in members_data:
            person_id = member.get('person_id') or member.get('id')
            if not person_id:
                continue
            spouses = member.get('spouses') or member.get('marriages') or []
            if isinstance(spouses, str):
                spouse_names = [s.strip() for s in spouses.split(';') if s.strip() and s.strip().lower() != 'unknown']
                for spouse_name in spouse_names:
                    cursor.execute('SELECT person_id FROM persons WHERE (full_name = %s OR alias = %s) AND person_id != %s', (spouse_name, spouse_name, person_id))
                    spouse_row = cursor.fetchone()
                    if spouse_row:
                        spouse_id = spouse_row['person_id']
                        cursor.execute('\n                            SELECT * FROM marriages \n                            WHERE (husband_id = %s AND wife_id = %s)\n                            OR (husband_id = %s AND wife_id = %s)\n                        ', (person_id, spouse_id, spouse_id, person_id))
                        if not cursor.fetchone():
                            try:
                                cursor.execute('\n                                    INSERT INTO marriages (husband_id, wife_id)\n                                    VALUES (%s, %s)\n                                ', (person_id, spouse_id))
                                inserted_marriages += 1
                            except Error:
                                pass
        try:
            connection.commit()
            logger.info('✅ Database changes committed successfully')
        except Error as commit_error:
            connection.rollback()
            logger.error(f'❌ Error committing changes, rolled back: {commit_error}')
            raise
        cursor.execute('SELECT COUNT(*) AS count FROM persons')
        after_persons_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM relationships')
        after_relationships_count = cursor.fetchone()['count']
        cursor.execute('SELECT COUNT(*) AS count FROM marriages')
        after_marriages_count = cursor.fetchone()['count']
        sync_timestamp = datetime.now().isoformat()
        sync_info = {'success': True, 'message': f'Đã sync {len(members_data)} members từ database chuẩn', 'timestamp': sync_timestamp, 'source_url': standard_db_url, 'stats': {'persons_before': before_persons_count, 'persons_after': after_persons_count, 'persons_inserted': inserted_persons, 'persons_updated': updated_persons, 'relationships_before': before_relationships_count, 'relationships_after': after_relationships_count, 'relationships_inserted': inserted_relationships, 'marriages_before': before_marriages_count, 'marriages_after': after_marriages_count, 'marriages_inserted': inserted_marriages}, 'note': f'Đã sync từ {standard_db_url}. Inserted {inserted_persons} persons, updated {updated_persons} persons, inserted {inserted_relationships} relationships, {inserted_marriages} marriages.'}
        logger.info(f'✅ Sync thành công: {inserted_persons} inserted, {updated_persons} updated persons, {inserted_relationships} relationships, {inserted_marriages} marriages')
        log_activity('SYNC_GENEALOGY', target_type='Persons', after_data={'inserted_persons': inserted_persons, 'updated_persons': updated_persons, 'inserted_relationships': inserted_relationships, 'inserted_marriages': inserted_marriages})
        return jsonify(sync_info)
    except Error as e:
        logger.error(f'❌ Lỗi database trong /api/genealogy/sync: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500)
    except Exception as e:
        logger.error(f'❌ Lỗi không mong đợi trong /api/genealogy/sync: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi không mong đợi: {str(e)}'}), 500)
    finally:
        try:
            if cursor:
                try:
                    cursor.fetchall()
                except:
                    pass
                cursor.close()
        except Exception as e:
            logger.debug(f'Error closing cursor: {e}')
        try:
            if connection:
                try:
                    connection.ping(reconnect=False, attempts=1, delay=0)
                    connection.close()
                except:
                    try:
                        connection.close()
                    except:
                        pass
        except Exception as e:
            logger.debug(f'Error closing connection: {e}')


def _collect_person_ids_from_tree_node(node):
    """Thu thập mọi person_id trong cây JSON do build_tree trả về."""
    if not node:
        return set()
    out = set()
    pid = node.get("person_id")
    if pid:
        out.add(str(pid))
    for ch in node.get("children") or []:
        out |= _collect_person_ids_from_tree_node(ch)
    return out


def _fetch_marriage_pairs_in_scope(cursor, id_set):
    """
    Các cặp trong bảng marriages mà cả person_id và spouse_person_id đều nằm trong id_set
    (đồng bộ với phạm vi cây đang tải). Trả về [[a,b], ...] với a <= b (sort chuỗi).
    """
    if not id_set:
        return []
    ids = tuple(id_set)
    placeholders = ",".join(["%s"] * len(ids))
    cursor.execute(
        f"""
        SELECT husband_id, wife_id FROM marriages
        WHERE husband_id IN ({placeholders}) AND wife_id IN ({placeholders})
        """,
        ids + ids,
    )
    rows = cursor.fetchall()
    pairs = []
    seen = set()
    for row in rows or []:
        if isinstance(row, dict):
            a = row.get("husband_id")
            b = row.get("wife_id")
        else:
            a, b = row[0], row[1]
        if not a or not b or a == b:
            continue
        a, b = str(a), str(b)
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        pairs.append([key[0], key[1]])
    return pairs
