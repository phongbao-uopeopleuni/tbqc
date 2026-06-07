import logging
from datetime import datetime

from flask import request, jsonify
from auth import permission_required
from folder_py.db_config import get_db_connection
from mysql.connector import Error

logger = logging.getLogger(__name__)


def _gen_unit_id(cursor) -> str:
    """Sinh unit_id theo format FU-YYYYMMDD-NNN (unique trong ngày)."""
    prefix = 'FU-' + datetime.now().strftime('%Y%m%d') + '-'
    cursor.execute(
        "SELECT unit_id FROM family_units WHERE unit_id LIKE %s ORDER BY unit_id DESC LIMIT 1",
        (prefix + '%',)
    )
    row = cursor.fetchone()
    if row:
        last_seq = int(row['unit_id'].rsplit('-', 1)[-1])
        return f"{prefix}{last_seq + 1:03d}"
    return f"{prefix}001"


def register_admin_family_units_routes(app):

    @app.route('/admin/api/family-units', methods=['GET'])
    @permission_required('canViewDashboard')
    def list_family_units():
        """List family units, tuỳ chọn filter theo father_id hoặc mother_id."""
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB connection failed'}), 500
        try:
            cur = conn.cursor(dictionary=True)
            where, params = [], []
            if request.args.get('father_id'):
                where.append('fu.father_id = %s')
                params.append(request.args['father_id'])
            if request.args.get('mother_id'):
                where.append('fu.mother_id = %s')
                params.append(request.args['mother_id'])
            clause = ('WHERE ' + ' AND '.join(where)) if where else ''
            cur.execute(f"""
                SELECT fu.unit_id, fu.father_id, fu.mother_id, fu.note,
                       fu.created_at, fu.updated_at,
                       pf.full_name AS father_name,
                       pm.full_name AS mother_name,
                       COUNT(p.person_id) AS members_count
                FROM family_units fu
                LEFT JOIN persons pf ON pf.person_id = fu.father_id
                LEFT JOIN persons pm ON pm.person_id = fu.mother_id
                LEFT JOIN persons p  ON p.family_unit_id = fu.unit_id
                {clause}
                GROUP BY fu.unit_id
                ORDER BY fu.unit_id
            """, params)
            return jsonify({'success': True, 'data': cur.fetchall()})
        except Error as e:
            logger.error('list_family_units: %s', e)
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cur.close(); conn.close()

    @app.route('/admin/api/family-units', methods=['POST'])
    @permission_required('canViewDashboard')
    def create_family_unit():
        """Tạo family unit mới. Body JSON: {father_id?, mother_id?, note?}."""
        data = request.get_json(silent=True) or {}
        father_id = data.get('father_id') or None
        mother_id = data.get('mother_id') or None
        note = data.get('note') or None
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB connection failed'}), 500
        try:
            cur = conn.cursor(dictionary=True)
            unit_id = _gen_unit_id(cur)
            cur.execute(
                "INSERT INTO family_units (unit_id, father_id, mother_id, note) VALUES (%s, %s, %s, %s)",
                (unit_id, father_id, mother_id, note)
            )
            conn.commit()
            return jsonify({'success': True, 'unit_id': unit_id}), 201
        except Error as e:
            conn.rollback()
            logger.error('create_family_unit: %s', e)
            code = 409 if e.errno == 1062 else 400 if e.errno == 1452 else 500
            return jsonify({'success': False, 'error': str(e)}), code
        finally:
            cur.close(); conn.close()

    @app.route('/admin/api/family-units/<unit_id>', methods=['PUT'])
    @permission_required('canViewDashboard')
    def update_family_unit(unit_id):
        """Cập nhật father_id, mother_id, note của một family unit."""
        data = request.get_json(silent=True) or {}
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB connection failed'}), 500
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT unit_id FROM family_units WHERE unit_id = %s", (unit_id,))
            if not cur.fetchone():
                return jsonify({'success': False, 'error': 'Not found'}), 404
            fields, vals = [], []
            for col in ('father_id', 'mother_id', 'note'):
                if col in data:
                    fields.append(f"{col} = %s")
                    vals.append(data[col] or None)
            if not fields:
                return jsonify({'success': False, 'error': 'Không có field nào để cập nhật'}), 400
            vals.append(unit_id)
            cur.execute(f"UPDATE family_units SET {', '.join(fields)} WHERE unit_id = %s", vals)
            conn.commit()
            return jsonify({'success': True})
        except Error as e:
            conn.rollback()
            logger.error('update_family_unit: %s', e)
            code = 409 if e.errno == 1062 else 400 if e.errno == 1452 else 500
            return jsonify({'success': False, 'error': str(e)}), code
        finally:
            cur.close(); conn.close()

    @app.route('/admin/api/family-units/<unit_id>', methods=['DELETE'])
    @permission_required('canViewDashboard')
    def delete_family_unit(unit_id):
        """Xóa family unit — chỉ cho phép nếu không còn persons nào dùng."""
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'DB connection failed'}), 500
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) AS cnt FROM persons WHERE family_unit_id = %s", (unit_id,))
            if cur.fetchone()['cnt'] > 0:
                return jsonify({
                    'success': False,
                    'error': 'Không thể xóa: vẫn còn thành viên thuộc family unit này'
                }), 409
            cur.execute("DELETE FROM family_units WHERE unit_id = %s", (unit_id,))
            if cur.rowcount == 0:
                return jsonify({'success': False, 'error': 'Not found'}), 404
            conn.commit()
            return jsonify({'success': True})
        except Error as e:
            conn.rollback()
            logger.error('delete_family_unit: %s', e)
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            cur.close(); conn.close()
