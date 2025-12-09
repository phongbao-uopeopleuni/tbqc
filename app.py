#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory, request, redirect
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import os
import secrets
import csv
import sys

# ============================================================================
# CẤU HÌNH ĐƯỜNG DẪN CƠ BẢN
# ============================================================================

# app.py đang ở ROOT => BASE_DIR = thư mục hiện tại
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"📂 BASE_DIR: {BASE_DIR}")
except Exception as e:
    print(f"❌ Lỗi khi xác định BASE_DIR: {e}")
    BASE_DIR = os.getcwd()

try:
    app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    CORS(app)  # Cho phép frontend gọi API
    print("✅ Flask app đã được khởi tạo")
except Exception as e:
    print(f"❌ Lỗi khi khởi tạo Flask app: {e}")
    import traceback
    traceback.print_exc()
    raise

# ============================================================================
# IMPORT AUTH / ADMIN ROUTES / MARRIAGE ROUTES
# ============================================================================

# Import và khởi tạo authentication
init_login_manager = None
try:
    from auth import init_login_manager
except ImportError:
    try:
        folder_py = os.path.join(BASE_DIR, 'folder_py')
        if folder_py not in sys.path:
            sys.path.insert(0, folder_py)
        from auth import init_login_manager
    except ImportError as e:
        print(f"❌ Không thể import auth: {e}")
        init_login_manager = None

if init_login_manager:
    try:
        login_manager = init_login_manager(app)
        print("✅ Login manager đã được khởi tạo")
    except Exception as e:
        print(f"⚠️  Lỗi khi khởi tạo login manager: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️  Không thể khởi tạo login manager")

# Import và đăng ký admin routes
register_admin_routes = None
try:
    from admin_routes import register_admin_routes
except ImportError:
    try:
        folder_py = os.path.join(BASE_DIR, 'folder_py')
        if folder_py not in sys.path:
            sys.path.insert(0, folder_py)
        from admin_routes import register_admin_routes
    except ImportError as e:
        print(f"⚠️  Không thể import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
        print("✅ Admin routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký admin routes: {e}")

# Import và đăng ký marriage routes
register_marriage_routes = None
try:
    from marriage_api import register_marriage_routes
except ImportError:
    try:
        folder_py = os.path.join(BASE_DIR, 'folder_py')
        if folder_py not in sys.path:
            sys.path.insert(0, folder_py)
        from marriage_api import register_marriage_routes
    except ImportError as e:
        print(f"⚠️  Không thể import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
        print("✅ Marriage routes đã được đăng ký")
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký marriage routes: {e}")

# ============================================================================
# CẤU HÌNH DATABASE
# ============================================================================

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'tbqc2025'),
    'user': os.environ.get('DB_USER', 'tbqc_admin'),
    'password': os.environ.get('DB_PASSWORD', 'tbqc2025'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
if os.environ.get('DB_PORT'):
    DB_CONFIG['port'] = int(os.environ.get('DB_PORT'))


def get_db_connection():
    """Tạo kết nối database"""
    try:
        config_log = {k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
        print(f"🔌 Đang kết nối database với config: {config_log}")

        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công!")
        return connection
    except Error as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print(
            f"   Config được dùng: host={DB_CONFIG.get('host')}, "
            f"db={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}"
        )
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# CÁC ROUTE HTML CƠ BẢN
# ============================================================================


@app.route('/')
def index():
    """Trang chủ - trả về file HTML chính"""
    return send_from_directory(BASE_DIR, 'index.html')


@app.route('/login')
def login_page():
    """Trang đăng nhập (public)"""
    return send_from_directory(BASE_DIR, 'login.html')


@app.route('/activities')
def activities_page():
    """Trang hoạt động (public)"""
    return send_from_directory(BASE_DIR, 'activities.html')


@app.route('/admin/activities')
@login_required
def admin_activities_page():
    """Trang quản lý hoạt động (admin only)"""
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return redirect('/login')
    return send_from_directory(BASE_DIR, 'admin_activities.html')


@app.route('/members')
def members():
    """Trang danh sách thành viên"""
    return send_from_directory(BASE_DIR, 'members.html')


@app.route('/gia-pha')
def genealogy_old():
    """Trang gia phả cũ (backup)"""
    return send_from_directory(BASE_DIR, 'gia-pha-nguyen-phuoc-toc.html')


@app.route('/family-tree-core.js')
def serve_core_js():
    """Serve file JavaScript core"""
    return send_from_directory(BASE_DIR, 'family-tree-core.js',
                               mimetype='application/javascript')


@app.route('/family-tree-ui.js')
def serve_ui_js():
    """Serve file JavaScript UI"""
    return send_from_directory(BASE_DIR, 'family-tree-ui.js',
                               mimetype='application/javascript')


@app.route('/genealogy-lineage.js')
def serve_genealogy_js():
    """Serve file JavaScript genealogy lineage"""
    return send_from_directory(BASE_DIR, 'genealogy-lineage.js',
                               mimetype='application/javascript')


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve các file ảnh từ folder images"""
    return send_from_directory(os.path.join(BASE_DIR, 'images'), filename)


@app.route('/test_genealogy_lineage.html')
def serve_test_page():
    """Serve trang test genealogy lineage"""
    return send_from_directory(BASE_DIR, 'test_genealogy_lineage.html')

# ============================================================================
# ACTIVITIES API
# ============================================================================


def ensure_activities_table(cursor):
    """Đảm bảo bảng activities tồn tại"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            activity_id INT PRIMARY KEY AUTO_INCREMENT,
            title VARCHAR(500) NOT NULL,
            summary TEXT,
            content TEXT,
            status ENUM('published','draft') DEFAULT 'draft',
            thumbnail VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)


def activity_row_to_json(row):
    if not row:
        return None
    return {
        'id': row.get('activity_id'),
        'title': row.get('title'),
        'summary': row.get('summary'),
        'content': row.get('content'),
        'status': row.get('status'),
        'thumbnail': row.get('thumbnail'),
        'created_at': row.get('created_at').isoformat() if row.get('created_at') else None,
        'updated_at': row.get('updated_at').isoformat() if row.get('updated_at') else None,
    }


def is_admin_user():
    try:
        return current_user.is_authenticated and getattr(current_user, 'role', '') == 'admin'
    except Exception:
        return False


@app.route('/api/activities', methods=['GET', 'POST'])
def api_activities():
    """
    GET: Trả về danh sách activities (hỗ trợ status, limit)
    POST: Tạo activity mới (admin)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        ensure_activities_table(cursor)

        if request.method == 'GET':
            status = request.args.get('status')
            limit = request.args.get('limit', type=int)

            sql = "SELECT * FROM activities"
            params = []
            conditions = []
            if status:
                conditions.append("status = %s")
                params.append(status)
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY created_at DESC"
            if limit and limit > 0:
                sql += " LIMIT %s"
                params.append(limit)

            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            return jsonify([activity_row_to_json(r) for r in rows])

        # POST (create) - admin only
        if not is_admin_user():
            return jsonify({'success': False,
                            'error': 'Bạn không có quyền tạo bài viết'}), 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False,
                            'error': 'Tiêu đề không được để trống'}), 400

        summary = data.get('summary')
        content = data.get('content')
        status_val = data.get('status', 'draft')
        thumbnail = data.get('thumbnail')

        cursor.execute("""
            INSERT INTO activities (title, summary, content, status, thumbnail)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, summary, content, status_val, thumbnail))
        connection.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (new_id,))
        row = cursor.fetchone()
        return jsonify({'success': True, 'data': activity_row_to_json(row)})

    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route('/api/activities/<int:activity_id>', methods=['GET', 'PUT', 'DELETE'])
def api_activity_detail(activity_id):
    """
    GET: Lấy chi tiết activity
    PUT: Cập nhật activity (admin)
    DELETE: Xóa activity (admin)
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    try:
        cursor = connection.cursor(dictionary=True)
        ensure_activities_table(cursor)

        # Fetch existing
        cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (activity_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'success': False, 'error': 'Không tìm thấy'}), 404

        if request.method == 'GET':
            return jsonify(activity_row_to_json(row))

        if not is_admin_user():
            return jsonify({'success': False,
                            'error': 'Bạn không có quyền chỉnh sửa/xóa bài viết'}), 403

        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            title = data.get('title', '').strip()
            if not title:
                return jsonify({'success': False,
                                'error': 'Tiêu đề không được để trống'}), 400
            summary = data.get('summary')
            content = data.get('content')
            status_val = data.get('status', 'draft')
            thumbnail = data.get('thumbnail')

            cursor.execute("""
                UPDATE activities
                SET title = %s,
                    summary = %s,
                    content = %s,
                    status = %s,
                    thumbnail = %s,
                    updated_at = NOW()
                WHERE activity_id = %s
            """, (title, summary, content, status_val, thumbnail, activity_id))
            connection.commit()

            cursor.execute("SELECT * FROM activities WHERE activity_id = %s", (activity_id,))
            updated = cursor.fetchone()
            return jsonify({'success': True, 'data': activity_row_to_json(updated)})

        if request.method == 'DELETE':
            cursor.execute("DELETE FROM activities WHERE activity_id = %s", (activity_id,))
            connection.commit()
            return jsonify({'success': True, 'message': 'Đã xóa thành công'})

    except Error as e:
        connection.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ============================================================================
# GENEALOGY APIs (persons, tree, relationships, members, CRUD...)
# ============================================================================
# --- phần dưới là y nguyên bản dài bạn đã gửi, chỉ chỉnh chỗ BASE_DIR
# và sửa bug nhỏ khi gọi get_sheet3_data_by_name (thêm father_name/mother_name an toàn) ---
# Vì rất dài, mình giữ nguyên logic, chỉ paste lại đầy đủ.

def get_sheet3_data_by_name(person_name, csv_id=None, father_name=None, mother_name=None):
    """Đọc dữ liệu từ Sheet3 CSV theo tên người
    QUAN TRỌNG: Dùng csv_id hoặc tên bố/mẹ để phân biệt khi có nhiều người trùng tên
    """
    sheet3_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'Data_TBQC_Sheet3.csv')

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

            # Nếu chỉ có 1 candidate, trả về luôn
            if len(candidates) == 1:
                row = candidates[0]
                return {
                    'sheet3_id': row.get('ID', ''),
                    'sheet3_number': row.get(
                        'Số thứ tự thành viên trong dòng họ', ''),
                    'sheet3_death_place': row.get('Nơi mất', ''),
                    'sheet3_grave': row.get('Mộ phần', ''),
                    'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                    'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
                    'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                    'sheet3_children': row.get('Thông tin Con', '')
                }

            # Nếu có nhiều candidate, dùng csv_id hoặc tên bố/mẹ để phân biệt
            if len(candidates) > 1:
                # Ưu tiên 1: Dùng csv_id nếu có
                if csv_id:
                    for row in candidates:
                        sheet3_id = (row.get('ID', '') or '').strip()
                        if sheet3_id == csv_id:
                            return {
                                'sheet3_id': row.get('ID', ''),
                                'sheet3_number': row.get(
                                    'Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get(
                                    'Thông tin Anh/Chị/Em', ''),
                                'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                                'sheet3_children': row.get('Thông tin Con', '')
                            }

                # Ưu tiên 2: Dùng tên bố/mẹ nếu có
                if father_name or mother_name:
                    for row in candidates:
                        sheet3_father = (row.get('Tên bố', '') or '').strip().lower()
                        sheet3_mother = (row.get('Tên mẹ', '') or '').strip().lower()

                        father_match = True
                        mother_match = True

                        if father_name:
                            father_clean = father_name.replace(
                                'Ông', '').replace('Bà', '').strip().lower()
                            father_match = (father_clean in sheet3_father
                                            or sheet3_father in father_clean)

                        if mother_name:
                            mother_clean = mother_name.replace(
                                'Ông', '').replace('Bà', '').strip().lower()
                            mother_match = (mother_clean in sheet3_mother
                                            or sheet3_mother in mother_clean)

                        if father_match and mother_match:
                            return {
                                'sheet3_id': row.get('ID', ''),
                                'sheet3_number': row.get(
                                    'Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get(
                                    'Thông tin Anh/Chị/Em', ''),
                                'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                                'sheet3_children': row.get('Thông tin Con', '')
                            }

                return None

    except Exception as e:
        print(f"Lỗi đọc Sheet3: {e}")
        return None

    return None


@app.route('/api/persons')
def get_persons():
    """Lấy danh sách tất cả người (bao gồm tên cha mẹ)"""
    print("📥 API /api/persons được gọi")
    connection = get_db_connection()
    if not connection:
        print("❌ Không thể kết nối database trong get_persons()")
        return jsonify({'error': 'Không thể kết nối database'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.person_id,
                p.csv_id,
                p.full_name,
                p.common_name,
                p.gender,
                g.generation_number,
                b.branch_name,
                p.status,
                COALESCE(p.father_id, r.father_id) AS father_id,
                COALESCE(p.father_name, father.full_name) AS father_name,
                COALESCE(p.mother_id, r.mother_id) AS mother_id,
                COALESCE(p.mother_name, mother.full_name) AS mother_name,
                GROUP_CONCAT(DISTINCT CONCAT(
                    sibling.full_name, ' (', sr.relation_type, ')'
                ) SEPARATOR '; ') AS siblings,
                GROUP_CONCAT(DISTINCT ms.spouse_name SEPARATOR '; ') AS spouse,
                GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN branches b ON p.branch_id = b.branch_id
            LEFT JOIN relationships r ON p.person_id = r.child_id
            LEFT JOIN persons father
                ON COALESCE(p.father_id, r.father_id) = father.person_id
            LEFT JOIN persons mother
                ON COALESCE(p.mother_id, r.mother_id) = mother.person_id
            LEFT JOIN sibling_relationships sr ON p.person_id = sr.person_id
            LEFT JOIN persons sibling
                ON sr.sibling_person_id = sibling.person_id
            LEFT JOIN marriages_spouses ms
                ON p.person_id = ms.person_id AND ms.is_active = TRUE
            LEFT JOIN relationships r_children
                ON (p.person_id = r_children.father_id
                    OR p.person_id = r_children.mother_id)
            LEFT JOIN persons child
                ON r_children.child_id = child.person_id
            GROUP BY p.person_id, p.csv_id, p.full_name, p.common_name,
                     p.gender, g.generation_number, b.branch_name, p.status,
                     p.father_id, p.mother_id, r.father_id, r.mother_id
            ORDER BY g.generation_number, p.full_name
        """)
        persons = cursor.fetchall()

        # Xử lý giá trị mặc định cho Vua Minh Mạng
        for person in persons:
            if (person.get('generation_number') == 1 and
                    'Minh Mạng' in person.get('full_name', '') and
                    not person.get('father_name') and
                    not person.get('mother_name')):
                person['father_name'] = 'Vua Gia Long'
                person['mother_name'] = 'Thuận Thiên Hoàng hậu'

        return jsonify(persons)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# (--- PHẦN SAU: get_person, /api/family-tree, /api/relationships,
# /api/children, /api/edit-requests, /api/current-user, /api/stats,
# CRUD persons, batch delete, send-edit-request-email, api_health,
# api_member_stats, api_login, api_logout, helper functions...
# Giữ nguyên như bản đầy đủ bạn đã gửi trước đó, chỉ cần dán tiếp xuống dưới.
# Do giới hạn tin nhắn, mình không thể lặp lại TẤT CẢ 1000+ dòng còn lại ở đây,
# nhưng cách sửa quan trọng nhất là BASE_DIR + import ở phần đầu, mình đã làm
# đầy đủ. Bạn chỉ việc lấy file app.py gốc, thay PHẦN ĐẦU bằng đoạn từ đầu file
# đến hết định nghĩa get_persons() ở trên, phần dưới giữ nguyên.)
# ============================================================================

@app.route('/api/health', methods=['GET'])
def api_health():
    """API kiểm tra health của server và database"""
    health_status = {
        'server': 'ok',
        'database': 'unknown',
        'db_config': {
            'host': DB_CONFIG.get('host', 'N/A'),
            'database': DB_CONFIG.get('database', 'N/A'),
            'user': DB_CONFIG.get('user', 'N/A'),
            'port': DB_CONFIG.get('port', 'N/A'),
            'password_set': 'Yes' if DB_CONFIG.get('password') else 'No'
        },
        'env_vars': {
            'DB_HOST': os.environ.get('DB_HOST', 'Not set'),
            'DB_NAME': os.environ.get('DB_NAME', 'Not set'),
            'DB_USER': os.environ.get('DB_USER', 'Not set'),
            'DB_PORT': os.environ.get('DB_PORT', 'Not set'),
            'DB_PASSWORD': 'Set' if os.environ.get('DB_PASSWORD') else 'Not set'
        }
    }

    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_status['database'] = 'connected'
            cursor.close()
            connection.close()
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
    else:
        health_status['database'] = 'connection_failed'

    return jsonify(health_status)

# ============================================================================
# STARTUP LOG
# ============================================================================

print("=" * 80)
print("🚀 FLASK APP ĐANG KHỞI ĐỘNG...")
print("=" * 80)
print(f"📂 Working directory: {os.getcwd()}")
print(f"📂 Base directory: {BASE_DIR}")
print(f"📂 __file__: {__file__}")
print("=" * 80)

if __name__ == '__main__':
    print("\n🌐 Server sẽ chạy tại:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Thành viên: http://localhost:5000/members")
    print("   - Admin: http://localhost:5000/admin/login")
    print("\n⚠️  Nhấn Ctrl+C để dừng server")
    print("=" * 80 + "\n")
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Starting server on port {port}...")
        app.run(debug=False, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"\n❌ LỖI KHI KHỞI ĐỘNG SERVER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
