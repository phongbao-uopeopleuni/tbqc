import logging

from flask import request, jsonify
from auth import permission_required
from audit_log import log_person_create, log_person_update, log_activity
from folder_py.db_config import get_db_connection
from mysql.connector import Error

logger = logging.getLogger(__name__)


def register_admin_members_routes(app):

    @app.route('/admin/api/members', methods=['GET'])
    @permission_required('canViewDashboard')
    def get_members_admin():
        """API: Lấy danh sách thành viên (tối ưu, không tính siblings/spouses)"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            search = request.args.get('search', '', type=str)

            cursor = connection.cursor(dictionary=True)

            base_query = """
                SELECT
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.gender,
                    p.status,
                    p.generation_level,
                    p.birth_date_solar,
                    p.birth_date_lunar,
                    p.death_date_solar,
                    p.death_date_lunar,
                    p.home_town,
                    p.place_of_death,
                    p.grave_info,
                    p.father_mother_id,
                    father.person_id AS father_id,
                    father.full_name AS father_name,
                    mother.person_id AS mother_id,
                    mother.full_name AS mother_name
                FROM persons p
                LEFT JOIN relationships rel_father
                    ON rel_father.child_id = p.person_id
                    AND rel_father.relation_type = 'father'
                LEFT JOIN persons father
                    ON rel_father.parent_id = father.person_id
                LEFT JOIN relationships rel_mother
                    ON rel_mother.child_id = p.person_id
                    AND rel_mother.relation_type = 'mother'
                LEFT JOIN persons mother
                    ON rel_mother.parent_id = mother.person_id
            """

            where_clause = ""
            params = []

            if search:
                where_clause = "WHERE p.person_id LIKE %s OR p.full_name LIKE %s OR father.full_name LIKE %s OR mother.full_name LIKE %s"
                search_pattern = f"%{search}%"
                params = [search_pattern, search_pattern, search_pattern, search_pattern]

            if where_clause:
                cursor.execute("SELECT COUNT(*) as total FROM persons p WHERE p.person_id LIKE %s OR p.full_name LIKE %s",
                               (f"%{search}%", f"%{search}%"))
            else:
                cursor.execute("SELECT COUNT(*) as total FROM persons")
            total = cursor.fetchone()['total']

            offset = (page - 1) * per_page
            order_by = "ORDER BY p.generation_level ASC, p.full_name ASC"
            limit_clause = f"LIMIT {per_page} OFFSET {offset}"

            if where_clause:
                query = f"{base_query} {where_clause} {order_by} {limit_clause}"
                cursor.execute(query, params)
            else:
                query = f"{base_query} {order_by} {limit_clause}"
                cursor.execute(query)

            persons = cursor.fetchall()

            for person in persons:
                person_id = person['person_id']

                cursor.execute("""
                    SELECT DISTINCT
                        CASE
                            WHEN m.person_id = %s THEN spouse.full_name
                            ELSE p.full_name
                        END AS spouse_name
                    FROM marriages m
                    LEFT JOIN persons p ON m.person_id = p.person_id
                    LEFT JOIN persons spouse ON m.spouse_person_id = spouse.person_id
                    WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                    AND (m.status IS NULL OR m.status != 'Đã ly dị')
                """, (person_id, person_id, person_id))
                spouses = cursor.fetchall()
                person['spouses'] = [s['spouse_name'] for s in spouses if s['spouse_name']]

                cursor.execute("""
                    SELECT DISTINCT child.full_name
                    FROM relationships r
                    JOIN persons child ON r.child_id = child.person_id
                    WHERE (r.parent_id = %s AND r.relation_type IN ('father', 'mother'))
                    ORDER BY child.full_name
                """, (person_id,))
                children = cursor.fetchall()
                person['children'] = [c['full_name'] for c in children if c['full_name']]

                fm_id = person.get('father_mother_id')
                if fm_id:
                    cursor.execute("""
                        SELECT DISTINCT s.full_name
                        FROM persons s
                        WHERE s.father_mother_id = %s
                        AND s.person_id != %s
                        ORDER BY s.full_name
                    """, (fm_id, person_id))
                    siblings = cursor.fetchall()
                    person['siblings'] = [s['full_name'] for s in siblings if s['full_name']]
                else:
                    person['siblings'] = []

            return jsonify({
                'success': True,
                'data': persons,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
        except Error as e:
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/members', methods=['POST'])
    @permission_required('canViewDashboard')
    def create_member_admin():
        """API: Thêm thành viên mới (admin không cần password)"""
        from services.person_service import _process_children_spouse_siblings
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

        cursor = None
        try:
            data = request.get_json() or {}
            if not data:
                return jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400

            cursor = connection.cursor(dictionary=True)

            person_id = data.get('person_id') or data.get('csv_id')
            if person_id:
                person_id = str(person_id).strip()
                cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'error': f'person_id {person_id} đã tồn tại'}), 400
            else:
                generation_num = data.get('generation_number')
                if generation_num:
                    cursor.execute("""
                        SELECT MAX(CAST(SUBSTRING_INDEX(person_id, '-', -1) AS UNSIGNED)) as max_num
                        FROM persons
                        WHERE person_id LIKE %s
                    """, (f'P-{generation_num}-%',))
                    result = cursor.fetchone()
                    next_num = (result['max_num'] or 0) + 1
                    person_id = f'P-{generation_num}-{next_num}'
                else:
                    return jsonify({'success': False, 'error': 'Cần có person_id hoặc generation_number để tạo ID'}), 400

            cursor.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'persons'
            """)
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

            insert_fields = ['person_id']
            insert_values = [person_id]

            if 'full_name' in columns:
                insert_fields.append('full_name')
                insert_values.append(data.get('full_name'))

            if 'gender' in columns:
                insert_fields.append('gender')
                insert_values.append(data.get('gender'))

            if 'status' in columns:
                insert_fields.append('status')
                insert_values.append(data.get('status', 'Không rõ'))

            if 'generation_level' in columns and data.get('generation_number'):
                insert_fields.append('generation_level')
                insert_values.append(data.get('generation_number'))

            if 'father_mother_id' in columns:
                insert_fields.append('father_mother_id')
                insert_values.append(data.get('fm_id'))
            elif 'fm_id' in columns:
                insert_fields.append('fm_id')
                insert_values.append(data.get('fm_id'))

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

            placeholders = ','.join(['%s'] * len(insert_values))
            insert_query = f"INSERT INTO persons ({', '.join(insert_fields)}) VALUES ({placeholders})"
            cursor.execute(insert_query, insert_values)

            if data.get('father_name') or data.get('mother_name'):
                father_id = None
                mother_id = None

                if data.get('father_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
                    father = cursor.fetchone()
                    if father:
                        father_id = father['person_id']

                if data.get('mother_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
                    mother = cursor.fetchone()
                    if mother:
                        mother_id = mother['person_id']

                if father_id:
                    cursor.execute("""
                        INSERT INTO relationships (child_id, parent_id, relation_type)
                        VALUES (%s, %s, 'father')
                        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                    """, (person_id, father_id))

                if mother_id:
                    cursor.execute("""
                        INSERT INTO relationships (child_id, parent_id, relation_type)
                        VALUES (%s, %s, 'mother')
                        ON DUPLICATE KEY UPDATE parent_id = VALUES(parent_id)
                    """, (person_id, mother_id))

            _process_children_spouse_siblings(cursor, person_id, data)

            connection.commit()

            try:
                cursor.execute("""
                    SELECT full_name, gender, status, generation_level, birth_date_solar,
                           death_date_solar, place_of_death
                    FROM persons
                    WHERE person_id = %s
                """, (person_id,))
                person_data = cursor.fetchone()

                if person_data:
                    log_person_create(person_id, dict(person_data))
            except Exception as log_error:
                logger.warning(f"Failed to log person create for {person_id}: {log_error}")

            return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})

        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
        except Exception as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                if cursor is not None:
                    cursor.close()
                connection.close()

    @app.route('/admin/api/members/<person_id>', methods=['PUT'])
    @permission_required('canViewDashboard')
    def update_member_admin(person_id):
        """API: Cập nhật thành viên (admin không cần password)"""
        from services.person_service import _process_children_spouse_siblings
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

        try:
            data = request.get_json() or {}
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': f'Không tìm thấy person_id: {person_id}'}), 404

            cursor.execute("""
                SELECT full_name, gender, status, generation_level, birth_date_solar,
                       death_date_solar, place_of_death
                FROM persons
                WHERE person_id = %s
            """, (person_id,))
            before_data = cursor.fetchone()

            cursor.execute("""
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'persons'
            """)
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

            update_fields = []
            update_values = []

            if 'full_name' in columns:
                update_fields.append('full_name = %s')
                update_values.append(data.get('full_name'))

            if 'gender' in columns:
                update_fields.append('gender = %s')
                update_values.append(data.get('gender'))

            if 'status' in columns:
                update_fields.append('status = %s')
                update_values.append(data.get('status'))

            if 'generation_level' in columns and data.get('generation_number'):
                update_fields.append('generation_level = %s')
                update_values.append(data.get('generation_number'))

            if 'father_mother_id' in columns:
                update_fields.append('father_mother_id = %s')
                update_values.append(data.get('fm_id'))
            elif 'fm_id' in columns:
                update_fields.append('fm_id = %s')
                update_values.append(data.get('fm_id'))

            if 'birth_date_solar' in columns:
                update_fields.append('birth_date_solar = %s')
                birth_date = data.get('birth_date_solar', '').strip() if data.get('birth_date_solar') else ''
                if birth_date and len(birth_date) == 4 and birth_date.isdigit():
                    birth_date = f'{birth_date}-01-01'
                update_values.append(birth_date if birth_date else None)

            if 'death_date_solar' in columns:
                update_fields.append('death_date_solar = %s')
                death_date = data.get('death_date_solar', '').strip() if data.get('death_date_solar') else ''
                if death_date and len(death_date) == 4 and death_date.isdigit():
                    death_date = f'{death_date}-01-01'
                update_values.append(death_date if death_date else None)

            if 'place_of_death' in columns:
                update_fields.append('place_of_death = %s')
                update_values.append(data.get('place_of_death'))

            if update_fields:
                update_values.append(person_id)
                update_query = f"UPDATE persons SET {', '.join(update_fields)} WHERE person_id = %s"
                cursor.execute(update_query, update_values)

            if data.get('father_name') or data.get('mother_name'):
                cursor.execute("DELETE FROM relationships WHERE child_id = %s AND relation_type IN ('father', 'mother')", (person_id,))

                if data.get('father_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['father_name'],))
                    father = cursor.fetchone()
                    if father:
                        cursor.execute("""
                            INSERT INTO relationships (child_id, parent_id, relation_type)
                            VALUES (%s, %s, 'father')
                        """, (person_id, father['person_id']))

                if data.get('mother_name'):
                    cursor.execute("SELECT person_id FROM persons WHERE full_name = %s LIMIT 1", (data['mother_name'],))
                    mother = cursor.fetchone()
                    if mother:
                        cursor.execute("""
                            INSERT INTO relationships (child_id, parent_id, relation_type)
                            VALUES (%s, %s, 'mother')
                        """, (person_id, mother['person_id']))

            _process_children_spouse_siblings(cursor, person_id, data)

            connection.commit()

            try:
                cursor.execute("""
                    SELECT full_name, gender, status, generation_level, birth_date_solar,
                           death_date_solar, place_of_death
                    FROM persons
                    WHERE person_id = %s
                """, (person_id,))
                after_data = cursor.fetchone()

                if before_data and after_data:
                    log_person_update(person_id, dict(before_data), dict(after_data))
            except Exception as log_error:
                logger.warning(f"Failed to log person update for {person_id}: {log_error}")

            return jsonify({'success': True, 'message': 'Cập nhật thành viên thành công'})

        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi database: {str(e)}'}), 500
        except Exception as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    @app.route('/admin/api/members/<person_id>', methods=['DELETE'])
    @permission_required('canViewDashboard')
    def delete_member(person_id):
        """API: Xóa thành viên từ database"""
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Không tìm thấy thành viên'}), 404

            cursor.execute("""
                SELECT full_name, gender, status, generation_level, birth_date_solar,
                       death_date_solar, place_of_death
                FROM persons
                WHERE person_id = %s
            """, (person_id,))
            before_data = cursor.fetchone()

            cursor.execute("DELETE FROM relationships WHERE parent_id = %s OR child_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM marriages WHERE person_id = %s OR spouse_person_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM in_law_relationships WHERE person_id = %s OR in_law_person_id = %s", (person_id, person_id))
            cursor.execute("DELETE FROM birth_records WHERE person_id = %s", (person_id,))
            cursor.execute("DELETE FROM death_records WHERE person_id = %s", (person_id,))
            cursor.execute("DELETE FROM personal_details WHERE person_id = %s", (person_id,))

            cursor.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
            connection.commit()

            try:
                if before_data:
                    log_activity('DELETE_PERSON', target_type='Person', target_id=person_id,
                                 before_data=dict(before_data), after_data=None)
            except Exception as log_error:
                logger.warning(f"Failed to log person delete for {person_id}: {log_error}")

            return jsonify({'success': True, 'message': 'Đã xóa thành viên thành công'})
        except Error as e:
            connection.rollback()
            return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
