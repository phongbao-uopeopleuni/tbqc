# -*- coding: utf-8 -*-
"""Members password, admin backup API handlers, and members list service."""
import logging
import os
from pathlib import Path

from flask import jsonify, request, send_from_directory

from audit_log import log_activity
from services.person_helpers import get_preferred_spouse_names
from utils.validation import secure_compare

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from folder_py.db_config import load_env_file
except ImportError:
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "folder_py"))
    from db_config import load_env_file  # type: ignore


def get_members_password():
    """
    Lấy mật khẩu cho các thao tác trên trang Members (Add, Update, Delete, Backup).
    Priority: MEMBERS_PASSWORD > ADMIN_PASSWORD > BACKUP_PASSWORD.
    Tự động load từ tbqc_db.env nếu không có trong environment variables (local dev).
    Trên production: chỉ dùng environment variables. Chỉ lưu mật khẩu local, không commit Git.

    Returns:
        Password string để sử dụng cho các thao tác Members
        Password string to use for Members operations
    """
    password = os.environ.get("MEMBERS_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or os.environ.get("BACKUP_PASSWORD", "")
    if not password:
        try:
            env_file = os.path.join(BASE_DIR, "tbqc_db.env")
            if os.path.exists(env_file):
                env_vars = load_env_file(env_file)
                file_password = env_vars.get("MEMBERS_PASSWORD") or env_vars.get("ADMIN_PASSWORD") or env_vars.get("BACKUP_PASSWORD", "")
                if file_password:
                    password = file_password
                    os.environ["MEMBERS_PASSWORD"] = password
                    logger.info("Password loaded from tbqc_db.env (local dev)")
            else:
                logger.debug("File tbqc_db.env không tồn tại (production mode), sử dụng environment variables")
        except Exception as e:
            logger.error(f"Could not load password from tbqc_db.env: {e}")
            import traceback

            logger.error(traceback.format_exc())
    if not password:
        logger.warning(
            "MEMBERS_PASSWORD/ADMIN_PASSWORD/BACKUP_PASSWORD chưa cấu hình - đặt trong .env hoặc biến môi trường (chỉ lưu local)"
        )
    return password or ""


def create_backup_api():
    """API tạo backup database - Yêu cầu mật khẩu"""
    data = request.get_json() or {}
    password = data.get("password", "").strip()
    correct_password = get_members_password()
    if not correct_password:
        logger.error("MEMBERS_PASSWORD, ADMIN_PASSWORD hoặc BACKUP_PASSWORD chưa được cấu hình")
        return (jsonify({"success": False, "error": "Cấu hình bảo mật chưa được thiết lập"}), 500)
    if not password or not secure_compare(password, correct_password):
        return (jsonify({"success": False, "error": "Mật khẩu không đúng hoặc chưa được cung cấp"}), 403)
    try:
        from scripts.backup_database import create_backup

        backup_dir = os.environ.get("BACKUP_DIR", "").strip() or "backups"
        result = create_backup(backup_dir=backup_dir)
        if result["success"]:
            log_activity(
                'BACKUP_CREATE_APP',
                target_type='Backup',
                target_id=result['backup_filename'],
                after_data={'file_size': result['file_size'], 'timestamp': result['timestamp']},
            )
            return jsonify(
                {
                    "success": True,
                    "message": "Backup thành công",
                    "backup_file": result["backup_filename"],
                    "file_size": result["file_size"],
                    "timestamp": result["timestamp"],
                }
            )
        else:
            return (jsonify({"success": False, "error": result.get("error", "Backup failed")}), 500)
    except Exception as e:
        logger.error(f"Error creating backup: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)


def list_backups_api():
    """API liệt kê các backup có sẵn"""
    try:
        from scripts.backup_database import list_backups

        backup_dir = os.environ.get("BACKUP_DIR", "").strip() or "backups"
        backups = list_backups(backup_dir=backup_dir)
        backup_list = []
        for backup in backups:
            backup_list.append(
                {
                    "filename": backup["filename"],
                    "size": backup["size"],
                    "size_mb": round(backup["size"] / 1024 / 1024, 2),
                    "created_at": backup["created_at"],
                }
            )
        return jsonify({"success": True, "backups": backup_list, "count": len(backup_list)})
    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)


def download_backup(filename):
    """API download file backup"""
    try:
        if not filename.startswith("tbqc_backup_") or not filename.endswith(".sql"):
            return (jsonify({"success": False, "error": "Invalid backup filename"}), 400)
        backup_dir = Path(os.environ.get("BACKUP_DIR", "").strip() or "backups")
        backup_file = backup_dir / filename
        if not backup_file.exists():
            return (jsonify({"success": False, "error": "Backup file not found"}), 404)
        
        try:
            file_size = backup_file.stat().st_size
        except OSError:
            file_size = None
        from audit_log import log_activity
        log_activity(
            'BACKUP_DOWNLOAD',
            target_type='Backup',
            target_id=filename,
            after_data={'file_size': file_size, 'route': 'members'},
        )
        
        return send_from_directory(str(backup_dir), filename, as_attachment=True, mimetype="application/sql")
    except Exception as e:
        logger.error(f"Error downloading backup: {e}", exc_info=True)
        return (jsonify({"success": False, "error": f"Lỗi: {str(e)}"}), 500)


def fetch_members_list():
    """
    Lấy danh sách thành viên đầy đủ (không cache).
    Dùng bởi export_members_excel và các caller cần raw list.
    Returns (list of member dicts, None) hoặc (None, error_message).
    """
    from db import get_db_connection
    from mysql.connector import Error as MySqlError
    from services.person_service import load_relationship_data

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
            AND COLUMN_NAME IN ('csv_id', 'personal_image_url', 'personal_image', 'biography', 'academic_rank', 'academic_degree', 'phone', 'email', 'place_of_death', 'occupation')
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
            logger.warning(f'Could not detect branch schema (fetch_members_list): {e}')
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
        select_fields.append('p.csv_id' if 'csv_id' in available_columns else 'NULL AS csv_id')
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
        children_map = relationship_data['children_map']
        siblings_map = relationship_data['siblings_map']
        members = []
        for person in persons:
            person_id = person['person_id']
            rel = parent_data.get(person_id, {'father_name': None, 'mother_name': None})
            spouse_names = get_preferred_spouse_names(relationship_data, person_id)
            siblings = siblings_map.get(person_id, [])
            children = children_map.get(person_id, [])
            member = {
                'person_id': person_id, 'csv_id': person.get('csv_id') or person_id, 'fm_id': person.get('fm_id'), 'full_name': person.get('full_name'),
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
        logger.error(f'Error in fetch_members_list: {e}', exc_info=True)
        return (None, str(e))
    except Exception as e:
        logger.error(f'Unexpected error in fetch_members_list: {e}', exc_info=True)
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
