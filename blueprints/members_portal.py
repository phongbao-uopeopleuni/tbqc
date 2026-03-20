# -*- coding: utf-8 -*-
"""
Cổng nội bộ Members - /members, /members/verify, /members/logout, /api/members
"""
import logging
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, session, send_file

logger = logging.getLogger(__name__)
members_portal_bp = Blueprint('members_portal', __name__)


@members_portal_bp.route('/members', strict_slashes=False)
def members():
    """Trang danh sách thành viên - hiển thị cổng đăng nhập hoặc trang members."""
    if not session.get('members_gate_ok'):
        return render_template('members_gate.html')
    from app import get_members_password
    members_password = get_members_password()
    gate_username = session.get('members_gate_user', '')
    return render_template('members.html', members_password=members_password or '', gate_username=gate_username)


@members_portal_bp.route('/members/verify', methods=['POST'])
def members_verify():
    """API xác thực đăng nhập cho cổng Members. Nhận JSON hoặc form."""
    try:
        data = request.get_json(silent=True) if request.is_json else {}
        if not data:
            data = {
                'username': (request.form.get('username') or '').strip(),
                'password': (request.form.get('password') or '').strip(),
            }
        else:
            data = {'username': (data.get('username') or '').strip(), 'password': (data.get('password') or '').strip()}
        username = data.get('username', '')
        password = data.get('password', '')
        if not username or not password:
            return (jsonify({'success': False, 'error': 'Tên đăng nhập và mật khẩu không được để trống'}), 400)
        from app import validate_tbqc_gate
        if validate_tbqc_gate(username, password):
            session['members_gate_ok'] = True
            session['members_gate_user'] = username
            session.permanent = True
            session.modified = True
            logger.info(f'Members gate login successful: {username}')
            return jsonify({'success': True, 'message': 'Đăng nhập thành công'})
        logger.warning(f'Members gate login failed: username={username!r} (len_pwd={len(password)})')
        return (jsonify({'success': False, 'error': 'Tên đăng nhập hoặc mật khẩu không đúng. Vui lòng thử lại.'}), 401)
    except Exception as e:
        logger.error(f'Error in members_verify: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': 'Lỗi server: ' + str(e)}), 500)


@members_portal_bp.route('/members/logout', methods=['GET', 'POST'])
def members_logout():
    """Đăng xuất khỏi cổng Members."""
    session.pop('members_gate_ok', None)
    session.pop('members_gate_user', None)
    logger.info('Members gate logout')
    from flask import redirect
    return redirect('/members')


@members_portal_bp.route('/api/members')
def get_members():
    """
    API lấy danh sách thành viên (source of truth).
    Yêu cầu session['members_gate_ok']. Có cache 5 phút.
    """
    from flask import current_app
    from mysql.connector import Error
    if not session.get('members_gate_ok'):
        logger.warning('Unauthorized access to /api/members')
        return (jsonify({'success': False, 'error': 'Chưa đăng nhập. Vui lòng đăng nhập lại.'}), 401)
    try:
        from app import cache
    except Exception:
        cache = None
    cache_key = 'api_members_data'
    if cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)
        except Exception as e:
            logger.warning(f'Cache get error: {e}')
    from app import get_db_connection, load_relationship_data
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email', 'place_of_death', 'occupation')
        """)
        _col_rows = cursor.fetchall()
        available_columns = set()
        for row in _col_rows:
            col = row.get('COLUMN_NAME') or row.get('column_name') or ''
            if col:
                available_columns.add(str(col).strip())

        # Nhánh: ưu tiên persons.branch_name nếu có; nếu không thì join branches qua branch_id
        has_branch_name_col = False
        has_branch_id = False
        has_branches_table = False
        try:
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons' AND COLUMN_NAME = 'branch_name'
                LIMIT 1
            """)
            has_branch_name_col = bool(cursor.fetchone())
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons' AND COLUMN_NAME = 'branch_id'
                LIMIT 1
            """)
            has_branch_id = bool(cursor.fetchone())
            cursor.execute("""
                SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'branches'
                LIMIT 1
            """)
            has_branches_table = bool(cursor.fetchone())
        except Exception as e:
            logger.warning(f'Could not detect branch schema: {e}')
            has_branch_name_col = False
            has_branch_id = False
            has_branches_table = False

        select_fields = [
            'p.person_id', 'p.father_mother_id AS fm_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status',
            'p.generation_level AS generation_number', 'p.birth_date_solar', 'p.birth_date_lunar',
            'p.death_date_solar', 'p.death_date_lunar', 'p.grave_info AS grave'
        ]
        select_fields.append('p.place_of_death' if 'place_of_death' in available_columns else 'NULL AS place_of_death')
        select_fields.append('p.personal_image_url AS personal_image_url' if 'personal_image_url' in available_columns else 'p.personal_image AS personal_image_url' if 'personal_image' in available_columns else 'NULL AS personal_image_url')
        select_fields.append('p.biography' if 'biography' in available_columns else 'NULL AS biography')
        select_fields.append('p.academic_rank' if 'academic_rank' in available_columns else 'NULL AS academic_rank')
        select_fields.append('p.academic_degree' if 'academic_degree' in available_columns else 'NULL AS academic_degree')
        select_fields.append('p.phone' if 'phone' in available_columns else 'NULL AS phone')
        select_fields.append('p.email' if 'email' in available_columns else 'NULL AS email')
        select_fields.append('p.occupation' if 'occupation' in available_columns else 'NULL AS occupation')
        if has_branch_name_col:
            select_fields.append('p.branch_name AS branch_name')
        else:
            select_fields.append('b.branch_name AS branch_name' if (has_branch_id and has_branches_table) else 'NULL AS branch_name')
        cursor.execute(f"""
            SELECT {', '.join(select_fields)}
            FROM persons p
            {'LEFT JOIN branches b ON p.branch_id = b.branch_id' if (has_branch_id and has_branches_table) else ''}
            ORDER BY COALESCE(p.generation_level, 999) ASC,
                CASE WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$'
                    THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(p.person_id, '-', 2), '-', -1) AS UNSIGNED) ELSE 999999 END ASC,
                CASE WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$'
                    THEN CAST(SUBSTRING_INDEX(p.person_id, '-', -1) AS UNSIGNED) ELSE 999999 END ASC,
                p.person_id ASC, p.full_name ASC
        """)
        persons = cursor.fetchall()
        relationship_data = load_relationship_data(cursor)
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        parent_data = relationship_data['parent_data']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        members = []
        for person in persons:
            person_id = person['person_id']
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            spouse_names = spouse_data_from_table.get(person_id) or spouse_data_from_marriages.get(person_id) or spouse_data_from_csv.get(person_id) or []
            siblings = siblings_map.get(person_id, [])
            children = children_map.get(person_id, [])
            member = {
                'person_id': person_id, 'csv_id': person_id, 'fm_id': person.get('fm_id'), 'full_name': person.get('full_name'),
                'alias': person.get('alias'), 'gender': person.get('gender'), 'status': person.get('status'),
                'generation_number': person.get('generation_number'),
                'birth_date_solar': str(person['birth_date_solar']) if person.get('birth_date_solar') else None,
                'birth_date_lunar': str(person['birth_date_lunar']) if person.get('birth_date_lunar') else None,
                'death_date_solar': str(person['death_date_solar']) if person.get('death_date_solar') else None,
                'death_date_lunar': str(person['death_date_lunar']) if person.get('death_date_lunar') else None,
                'grave': person.get('grave'), 'grave_info': person.get('grave'), 'place_of_death': person.get('place_of_death'),
                'branch_name': person.get('branch_name'),
                'father_name': rel.get('father_name'), 'mother_name': rel.get('mother_name'),
                'spouses': '; '.join(spouse_names) if spouse_names else None,
                'siblings': '; '.join(siblings) if siblings else None,
                'children': '; '.join(children) if children else None,
                'personal_image_url': person.get('personal_image_url'), 'biography': person.get('biography'),
                'academic_rank': person.get('academic_rank'), 'academic_degree': person.get('academic_degree'),
                'phone': person.get('phone'), 'email': person.get('email'),
                'occupation': person.get('occupation')
            }
            members.append(member)
        response_data = {'success': True, 'data': members}
        if cache:
            try:
                cache.set(cache_key, response_data, timeout=300)
            except Exception as e:
                logger.warning(f'Cache set error: {e}')
        return jsonify(response_data)
    except Error as e:
        logger.error(f'Error in /api/members: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    except Exception as e:
        logger.error(f'Unexpected error in /api/members: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection and getattr(connection, 'is_connected', lambda: False)():
            try:
                connection.close()
            except Exception:
                pass


def _fetch_members_list():
    """
    Lấy danh sách thành viên (giống /api/members), không dùng cache.
    Returns (list of member dicts, None) hoặc (None, error_message).
    """
    from app import get_db_connection, load_relationship_data
    from mysql.connector import Error as MySqlError
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            return (None, 'Không thể kết nối database')
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT COLUMN_NAME FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons'
            AND COLUMN_NAME IN ('personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email', 'place_of_death', 'occupation')
        """)
        _col_rows = cursor.fetchall()
        available_columns = set()
        for row in _col_rows:
            col = row.get('COLUMN_NAME') or row.get('column_name') or ''
            if col:
                available_columns.add(str(col).strip())

        # Nhánh: ưu tiên persons.branch_name nếu có; nếu không thì join branches qua branch_id
        has_branch_name_col = False
        has_branch_id = False
        has_branches_table = False
        try:
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons' AND COLUMN_NAME = 'branch_name'
                LIMIT 1
            """)
            has_branch_name_col = bool(cursor.fetchone())
            cursor.execute("""
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'persons' AND COLUMN_NAME = 'branch_id'
                LIMIT 1
            """)
            has_branch_id = bool(cursor.fetchone())
            cursor.execute("""
                SELECT TABLE_NAME FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'branches'
                LIMIT 1
            """)
            has_branches_table = bool(cursor.fetchone())
        except Exception as e:
            logger.warning(f'Could not detect branch schema (_fetch_members_list): {e}')
            has_branch_name_col = False
            has_branch_id = False
            has_branches_table = False

        select_fields = [
            'p.person_id', 'p.father_mother_id AS fm_id', 'p.full_name', 'p.alias', 'p.gender', 'p.status',
            'p.generation_level AS generation_number', 'p.birth_date_solar', 'p.birth_date_lunar',
            'p.death_date_solar', 'p.death_date_lunar', 'p.grave_info AS grave'
        ]
        select_fields.append('p.place_of_death' if 'place_of_death' in available_columns else 'NULL AS place_of_death')
        select_fields.append('p.personal_image_url AS personal_image_url' if 'personal_image_url' in available_columns else 'p.personal_image AS personal_image_url' if 'personal_image' in available_columns else 'NULL AS personal_image_url')
        select_fields.append('p.biography' if 'biography' in available_columns else 'NULL AS biography')
        select_fields.append('p.academic_rank' if 'academic_rank' in available_columns else 'NULL AS academic_rank')
        select_fields.append('p.academic_degree' if 'academic_degree' in available_columns else 'NULL AS academic_degree')
        select_fields.append('p.phone' if 'phone' in available_columns else 'NULL AS phone')
        select_fields.append('p.email' if 'email' in available_columns else 'NULL AS email')
        select_fields.append('p.occupation' if 'occupation' in available_columns else 'NULL AS occupation')
        if has_branch_name_col:
            select_fields.append('p.branch_name AS branch_name')
        else:
            select_fields.append('b.branch_name AS branch_name' if (has_branch_id and has_branches_table) else 'NULL AS branch_name')
        cursor.execute(f"""
            SELECT {', '.join(select_fields)}
            FROM persons p
            {'LEFT JOIN branches b ON p.branch_id = b.branch_id' if (has_branch_id and has_branches_table) else ''}
            ORDER BY COALESCE(p.generation_level, 999) ASC,
                CASE WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$'
                    THEN CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(p.person_id, '-', 2), '-', -1) AS UNSIGNED) ELSE 999999 END ASC,
                CASE WHEN p.person_id LIKE 'P-%' AND SUBSTRING(p.person_id, 3) REGEXP '^[0-9]+-[0-9]+$'
                    THEN CAST(SUBSTRING_INDEX(p.person_id, '-', -1) AS UNSIGNED) ELSE 999999 END ASC,
                p.person_id ASC, p.full_name ASC
        """)
        persons = cursor.fetchall()
        relationship_data = load_relationship_data(cursor)
        parent_data = relationship_data['parent_data']
        spouse_data_from_table = relationship_data['spouse_data_from_table']
        spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
        spouse_data_from_csv = relationship_data['spouse_data_from_csv']
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        members = []
        for person in persons:
            person_id = person['person_id']
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            spouse_names = spouse_data_from_table.get(person_id) or spouse_data_from_marriages.get(person_id) or spouse_data_from_csv.get(person_id) or []
            siblings = siblings_map.get(person_id, [])
            children = children_map.get(person_id, [])
            member = {
                'person_id': person_id, 'csv_id': person_id, 'fm_id': person.get('fm_id'), 'full_name': person.get('full_name'),
                'alias': person.get('alias'), 'gender': person.get('gender'), 'status': person.get('status'),
                'generation_number': person.get('generation_number'),
                'birth_date_solar': str(person['birth_date_solar']) if person.get('birth_date_solar') else None,
                'birth_date_lunar': str(person['birth_date_lunar']) if person.get('birth_date_lunar') else None,
                'death_date_solar': str(person['death_date_solar']) if person.get('death_date_solar') else None,
                'death_date_lunar': str(person['death_date_lunar']) if person.get('death_date_lunar') else None,
                'grave': person.get('grave'), 'grave_info': person.get('grave'), 'place_of_death': person.get('place_of_death'),
                'branch_name': person.get('branch_name'),
                'father_name': rel.get('father_name'), 'mother_name': rel.get('mother_name'),
                'spouses': '; '.join(spouse_names) if spouse_names else None,
                'siblings': '; '.join(siblings) if siblings else None,
                'children': '; '.join(children) if children else None,
                'personal_image_url': person.get('personal_image_url'), 'biography': person.get('biography'),
                'academic_rank': person.get('academic_rank'), 'academic_degree': person.get('academic_degree'),
                'phone': person.get('phone'), 'email': person.get('email'), 'occupation': person.get('occupation')
            }
            members.append(member)
        return (members, None)
    except MySqlError as e:
        logger.error(f'Error in _fetch_members_list: {e}', exc_info=True)
        return (None, str(e))
    except Exception as e:
        logger.error(f'Unexpected error in _fetch_members_list: {e}', exc_info=True)
        return (None, str(e))
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection and getattr(connection, 'is_connected', lambda: False)():
            try:
                connection.close()
            except Exception:
                pass


# Cột xuất Excel: (key trong dict, tiêu đề tiếng Việt)
_EXCEL_COLUMNS = [
    ('person_id', 'ID'), ('fm_id', 'FM_ID'), ('branch_name', 'Nhánh'), ('full_name', 'Họ và tên'), ('alias', 'Tên gọi khác'),
    ('gender', 'Giới tính'), ('status', 'Trạng thái'), ('generation_number', 'Đời'),
    ('birth_date_solar', 'Ngày sinh (dương lịch)'), ('birth_date_lunar', 'Ngày sinh (âm lịch)'),
    ('death_date_solar', 'Ngày mất (dương lịch)'), ('death_date_lunar', 'Ngày mất (âm lịch)'),
    ('grave', 'Mộ'), ('place_of_death', 'Nơi mất'),
    ('father_name', 'Cha'), ('mother_name', 'Mẹ'),
    ('spouses', 'Vợ/Chồng'), ('siblings', 'Anh chị em'), ('children', 'Con'),
    ('occupation', 'Nghề nghiệp'), ('academic_rank', 'Học hàm'), ('academic_degree', 'Học vị'),
    ('phone', 'Điện thoại'), ('email', 'Email'), ('biography', 'Tiểu sử'), ('personal_image_url', 'URL ảnh'),
]


@members_portal_bp.route('/members/export/excel')
def export_members_excel():
    """Xuất toàn bộ danh sách thành viên ra file Excel. Yêu cầu đã đăng nhập cổng Members."""
    if not session.get('members_gate_ok'):
        from flask import redirect
        return redirect('/members')
    members, err = _fetch_members_list()
    if err:
        return (jsonify({'success': False, 'error': err}), 500)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment
        from datetime import datetime
        wb = Workbook()
        ws = wb.active
        ws.title = 'Danh sách thành viên'
        # Header
        for col, (_, header) in enumerate(_EXCEL_COLUMNS, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        # Data rows
        for row_idx, member in enumerate(members, 2):
            for col_idx, (key, _) in enumerate(_EXCEL_COLUMNS, 1):
                val = member.get(key)
                if val is not None:
                    ws.cell(row=row_idx, column=col_idx, value=str(val) if not isinstance(val, (int, float)) else val)
        # Auto-fit column widths (approximate)
        from openpyxl.utils import get_column_letter
        for col_idx in range(1, len(_EXCEL_COLUMNS) + 1):
            ws.column_dimensions[get_column_letter(col_idx)].width = 16
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        filename = 'danh_sach_thanh_vien_{}.xlsx'.format(datetime.now().strftime('%Y%m%d_%H%M'))
        return send_file(buf, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
    except ImportError:
        logger.error('openpyxl not installed')
        return (jsonify({'success': False, 'error': 'Thư viện xuất Excel chưa được cài đặt.'}), 500)
    except Exception as e:
        logger.error(f'Error exporting Excel: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)


@members_portal_bp.route('/api/members/bulk-update-branch', methods=['POST'])
def bulk_update_members_branch():
    """
    Bulk update cột "Nhánh" cho members từ file Excel/CSV.

    Template file chỉ cần 2 cột:
    - ID: ứng với persons.person_id
    - Nhánh: chỉ nhận 1 trong {Một, Hai, Ba, Bốn}

    Rule:
    - Nếu Nhánh sai hoặc ID sai format => error_count++ và bỏ qua dòng
    - Nếu ID hợp lệ nhưng không tồn tại trong DB => silent (không update, không tính lỗi)
    - Trả về số dòng cập nhật thành công và số dòng lỗi.
    """
    import io
    import os
    import re
    import csv

    from app import get_db_connection, get_or_create_branch, get_members_password, secure_compare

    if not session.get('members_gate_ok'):
        logger.warning('Unauthorized access to /api/members/bulk-update-branch')
        return (jsonify({'success': False, 'error': 'Chưa đăng nhập. Vui lòng đăng nhập lại.'}), 401)

    # Auth: read password (multipart/form-data or JSON)
    if request.content_type and 'multipart/form-data' in request.content_type:
        password = (request.form.get('password') or '').strip()
    else:
        payload = request.get_json(silent=True) or {}
        password = (payload.get('password') or '').strip()

    correct_password = get_members_password()
    if not password or not secure_compare(password, correct_password):
        return (jsonify({'success': False, 'error': 'Mật khẩu không đúng hoặc chưa được cung cấp'}), 403)

    uploaded_file = request.files.get('file')
    if not uploaded_file or not uploaded_file.filename:
        return (jsonify({'success': False, 'error': 'Chưa nhận được file'}), 400)

    filename = uploaded_file.filename.strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in {'.xlsx', '.csv'}:
        return (jsonify({'success': False, 'error': 'Chỉ hỗ trợ file .xlsx hoặc .csv'}), 400)

    # Cho phép cả dạng text (Một/Hai/...) và dạng code số (0..7, -1)
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
    allowed_branch_names = set(branch_code_to_name.values())
    id_regex = re.compile(r'^P-\d+-\d+$')

    # Validate + map: {person_id: branch_name}
    valid_to_update = {}
    error_count = 0

    file_bytes = uploaded_file.read()
    if not file_bytes:
        return (jsonify({'success': False, 'error': 'File rỗng'}), 400)

    try:
        if ext == '.xlsx':
            from openpyxl import load_workbook

            buf = io.BytesIO(file_bytes)
            wb = load_workbook(filename=buf, read_only=True, data_only=True)
            ws = wb.active

            header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
            if not header_row:
                return (jsonify({'success': False, 'error': 'Không tìm thấy header trong file'}), 400)

            header_cells = [(str(c).strip() if c is not None else '') for c in header_row]
            id_idx = None
            branch_idx = None
            for i, h in enumerate(header_cells):
                if h == 'ID':
                    id_idx = i
                elif h == 'Nhánh':
                    branch_idx = i

            if id_idx is None or branch_idx is None:
                return (jsonify({'success': False, 'error': 'File phải có 2 cột: ID và Nhánh'}), 400)

            for row in ws.iter_rows(min_row=2, values_only=True):
                id_val = row[id_idx] if id_idx < len(row) else None
                branch_val = row[branch_idx] if branch_idx < len(row) else None

                id_str = str(id_val).strip() if id_val is not None else ''
                branch_str = str(branch_val).strip() if branch_val is not None else ''

                if not id_regex.match(id_str):
                    error_count += 1
                    continue
                canonical_branch = None
                if branch_str in allowed_branch_names:
                    canonical_branch = branch_str
                elif branch_str in branch_code_to_name:
                    canonical_branch = branch_code_to_name[branch_str]

                if not canonical_branch:
                    error_count += 1
                    continue

                valid_to_update[id_str] = canonical_branch

        else:
            # CSV
            text = file_bytes.decode('utf-8-sig', errors='replace')
            reader = csv.DictReader(io.StringIO(text))
            if not reader.fieldnames:
                return (jsonify({'success': False, 'error': 'Không tìm thấy header trong file CSV'}), 400)

            normalized = {(fn or '').strip(): fn for fn in reader.fieldnames if fn is not None}
            if 'ID' not in normalized or 'Nhánh' not in normalized:
                return (jsonify({'success': False, 'error': 'File phải có 2 cột: ID và Nhánh'}), 400)

            id_key = normalized['ID']
            branch_key = normalized['Nhánh']

            for row in reader:
                id_val = row.get(id_key)
                branch_val = row.get(branch_key)

                id_str = str(id_val).strip() if id_val is not None else ''
                branch_str = str(branch_val).strip() if branch_val is not None else ''

                if not id_regex.match(id_str):
                    error_count += 1
                    continue
                canonical_branch = None
                if branch_str in allowed_branch_names:
                    canonical_branch = branch_str
                elif branch_str in branch_code_to_name:
                    canonical_branch = branch_code_to_name[branch_str]

                if not canonical_branch:
                    error_count += 1
                    continue

                valid_to_update[id_str] = canonical_branch

    except Exception as e:
        logger.error(f'Failed to parse uploaded branch file: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': f'Lỗi đọc file: {str(e)}'}), 400)

    connection = get_db_connection()
    if not connection:
        return (jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500)

    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)

        if not valid_to_update:
            return jsonify({'success': True, 'updated_count': 0, 'error_count': error_count})

        ids = list(valid_to_update.keys())
        placeholders = ','.join(['%s'] * len(ids))
        cursor.execute(f'SELECT person_id FROM persons WHERE person_id IN ({placeholders})', tuple(ids))
        existing_set = {r['person_id'] for r in cursor.fetchall() if r.get('person_id')}

        # Silent: only update if exists
        existing_map = {pid: valid_to_update[pid] for pid in ids if pid in existing_set}
        updated_count = len(existing_map)

        if updated_count == 0:
            return jsonify({'success': True, 'updated_count': 0, 'error_count': error_count})

        # Detect schema for branch_name / branch_id
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'persons'
              AND COLUMN_NAME IN ('branch_name', 'branch_id')
        """)
        cols = {r.get('COLUMN_NAME') for r in cursor.fetchall() if r.get('COLUMN_NAME')}

        cursor.execute("""
            SELECT TABLE_NAME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'branches'
            LIMIT 1
        """)
        has_branches_table = bool(cursor.fetchone())

        if 'branch_name' in cols:
            update_rows = [(branch, pid) for pid, branch in existing_map.items()]
            cursor.executemany(
                'UPDATE persons SET branch_name = %s WHERE person_id = %s',
                update_rows
            )
        elif 'branch_id' in cols and has_branches_table:
            # Map branch_name -> branch_id and update branch_id
            unique_branch_names = set(existing_map.values())
            branch_name_to_id = {}
            # get_or_create_branch() trong app.py kỳ vọng fetchone() trả về tuple
            # nên dùng cursor thường (không dictionary=True) để tránh KeyError.
            cursor_for_branch = connection.cursor()
            try:
                for bn in unique_branch_names:
                    branch_name_to_id[bn] = get_or_create_branch(cursor_for_branch, bn)
            finally:
                try:
                    cursor_for_branch.close()
                except Exception:
                    pass

            update_rows = [(branch_name_to_id[bn], pid) for pid, bn in existing_map.items()]
            cursor.executemany(
                'UPDATE persons SET branch_id = %s WHERE person_id = %s',
                update_rows
            )
        else:
            return (jsonify({'success': False, 'error': 'Không tìm thấy cột branch_name hoặc branch_id trong persons'}), 500)

        connection.commit()

        # Invalidate members cache
        try:
            from app import cache
            if cache:
                cache.delete('api_members_data')
        except Exception as e:
            logger.warning(f'Cache invalidation error (continuing): {e}')

        return jsonify({'success': True, 'updated_count': updated_count, 'error_count': error_count})

    except Exception as e:
        connection.rollback()
        logger.error(f'Error in bulk_update_members_branch: {e}', exc_info=True)
        return (jsonify({'success': False, 'error': str(e)}), 500)
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if connection and getattr(connection, 'is_connected', lambda: False)():
            try:
                connection.close()
            except Exception:
                pass
