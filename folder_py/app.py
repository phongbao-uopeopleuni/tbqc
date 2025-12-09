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

# Xác định thư mục root của project (thư mục chứa index.html)
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"📂 BASE_DIR: {BASE_DIR}")
except Exception as e:
    print(f"❌ Lỗi khi xác định BASE_DIR: {e}")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

# Import và khởi tạo authentication
try:
    from auth import init_login_manager
except ImportError:
    # Nếu chạy từ root, import từ folder_py
    import sys
    import os
    folder_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
    if folder_py not in sys.path:
        sys.path.insert(0, folder_py)
    from folder_py.auth import init_login_manager

try:
    login_manager = init_login_manager(app)
except Exception as e:
    print(f"⚠️  Lỗi khi khởi tạo login manager: {e}")
    import traceback
    traceback.print_exc()

# Import và đăng ký admin routes
try:
    from admin_routes import register_admin_routes
except ImportError:
    try:
        from folder_py.admin_routes import register_admin_routes
    except ImportError as e:
        print(f"⚠️  Không thể import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký admin routes: {e}")

# Import và đăng ký marriage routes
try:
    from marriage_api import register_marriage_routes
except ImportError:
    try:
        from folder_py.marriage_api import register_marriage_routes
    except ImportError as e:
        print(f"⚠️  Không thể import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
    except Exception as e:
        print(f"⚠️  Lỗi khi đăng ký marriage routes: {e}")

# Cấu hình database - đọc từ environment variables (cho production) hoặc dùng giá trị mặc định (cho local)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'tbqc2025'),
    'user': os.environ.get('DB_USER', 'tbqc_admin'),
    'password': os.environ.get('DB_PASSWORD', 'tbqc2025'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
# Thêm port nếu cần (cho một số hosting)
if os.environ.get('DB_PORT'):
    DB_CONFIG['port'] = int(os.environ.get('DB_PORT'))

def get_db_connection():
    """Tạo kết nối database"""
    try:
        # Log config (ẩn password)
        config_log = {k: v if k != 'password' else '***' for k, v in DB_CONFIG.items()}
        print(f"🔌 Đang kết nối database với config: {config_log}")
        
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Kết nối database thành công!")
        return connection
    except Error as e:
        print(f"❌ Lỗi kết nối database: {e}")
        print(f"   Config được dùng: host={DB_CONFIG.get('host')}, db={DB_CONFIG.get('database')}, user={DB_CONFIG.get('user')}")
        import traceback
        traceback.print_exc()
        return None

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
    # Check admin permission
    if not current_user.is_authenticated or getattr(current_user, 'role', '') != 'admin':
        return redirect('/login')
    
    return send_from_directory(BASE_DIR, 'admin_activities.html')

# ---------------------------------------------------------------------------
# ACTIVITIES API (Hoạt động / Tin tức)
# ---------------------------------------------------------------------------

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
            return jsonify({'success': False, 'error': 'Bạn không có quyền tạo bài viết'}), 403

        data = request.get_json(silent=True) or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify({'success': False, 'error': 'Tiêu đề không được để trống'}), 400

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
            return jsonify({'success': False, 'error': 'Bạn không có quyền chỉnh sửa/xóa bài viết'}), 403

        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            title = data.get('title', '').strip()
            if not title:
                return jsonify({'success': False, 'error': 'Tiêu đề không được để trống'}), 400
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
    return send_from_directory(BASE_DIR, 'family-tree-core.js', mimetype='application/javascript')

@app.route('/family-tree-ui.js')
def serve_ui_js():
    """Serve file JavaScript UI"""
    return send_from_directory(BASE_DIR, 'family-tree-ui.js', mimetype='application/javascript')

@app.route('/genealogy-lineage.js')
def serve_genealogy_js():
    """Serve file JavaScript genealogy lineage"""
    return send_from_directory(BASE_DIR, 'genealogy-lineage.js', mimetype='application/javascript')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve các file ảnh từ folder images"""
    return send_from_directory(os.path.join(BASE_DIR, 'images'), filename)

@app.route('/test_genealogy_lineage.html')
def serve_test_page():
    """Serve trang test genealogy lineage"""
    return send_from_directory(BASE_DIR, 'test_genealogy_lineage.html')

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
        # Sử dụng GROUP BY và MAX() để đảm bảo mỗi person chỉ xuất hiện 1 lần
        # Nếu có nhiều relationships, lấy relationship đầu tiên (theo relationship_id)
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
                -- Ưu tiên dùng father_id/mother_id từ persons (đã được populate từ relationships)
                COALESCE(p.father_id, r.father_id) AS father_id,
                COALESCE(p.father_name, father.full_name) AS father_name,
                COALESCE(p.mother_id, r.mother_id) AS mother_id,
                COALESCE(p.mother_name, mother.full_name) AS mother_name,
                GROUP_CONCAT(DISTINCT CONCAT(sibling.full_name, ' (', sr.relation_type, ')') SEPARATOR '; ') AS siblings,
                GROUP_CONCAT(DISTINCT ms.spouse_name SEPARATOR '; ') AS spouse,
                GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN branches b ON p.branch_id = b.branch_id
            -- Fallback: Nếu chưa có trong persons, lấy từ relationships
            LEFT JOIN relationships r ON p.person_id = r.child_id
            LEFT JOIN persons father ON COALESCE(p.father_id, r.father_id) = father.person_id
            LEFT JOIN persons mother ON COALESCE(p.mother_id, r.mother_id) = mother.person_id
            LEFT JOIN sibling_relationships sr ON p.person_id = sr.person_id
            LEFT JOIN persons sibling ON sr.sibling_person_id = sibling.person_id
            LEFT JOIN marriages_spouses ms ON p.person_id = ms.person_id AND ms.is_active = TRUE
            LEFT JOIN relationships r_children ON (p.person_id = r_children.father_id OR p.person_id = r_children.mother_id)
            LEFT JOIN persons child ON r_children.child_id = child.person_id
            GROUP BY p.person_id, p.csv_id, p.full_name, p.common_name, p.gender, g.generation_number, b.branch_name, p.status, p.father_id, p.mother_id, r.father_id, r.mother_id
            ORDER BY g.generation_number, p.full_name
        """)
        persons = cursor.fetchall()
        
        # Xử lý giá trị mặc định cho Vua Minh Mạng
        for person in persons:
            # Nếu là Vua Minh Mạng (Đời 1) và không có thông tin cha mẹ
            if (person.get('generation_number') == 1 and 
                'Minh Mạng' in person.get('full_name', '') and
                not person.get('father_name') and not person.get('mother_name')):
                person['father_name'] = 'Vua Gia Long'
                person['mother_name'] = 'Thuận Thiên Hoàng hậu'
        
        return jsonify(persons)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_sheet3_data_by_name(person_name, csv_id=None, father_name=None, mother_name=None):
    """Đọc dữ liệu từ Sheet3 CSV theo tên người
    QUAN TRỌNG: Dùng csv_id hoặc tên bố/mẹ để phân biệt khi có nhiều người trùng tên
    """
    sheet3_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data_TBQC_Sheet3.csv')
    
    if not os.path.exists(sheet3_file):
        return None
    
    try:
        with open(sheet3_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            candidates = []
            for row in reader:
                # So sánh tên (không phân biệt hoa thường, loại bỏ khoảng trắng thừa)
                sheet3_name = (row.get('Họ và tên', '') or '').strip()
                person_name_clean = (person_name or '').strip()
                
                if sheet3_name.lower() == person_name_clean.lower():
                    candidates.append(row)
            
            # Nếu chỉ có 1 candidate, trả về luôn
            if len(candidates) == 1:
                row = candidates[0]
                return {
                    'sheet3_id': row.get('ID', ''),
                    'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
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
                                'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
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
                            father_clean = father_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            father_match = father_clean in sheet3_father or sheet3_father in father_clean
                        
                        if mother_name:
                            mother_clean = mother_name.replace('Ông', '').replace('Bà', '').strip().lower()
                            mother_match = mother_clean in sheet3_mother or sheet3_mother in mother_clean
                        
                        if father_match and mother_match:
                            return {
                                'sheet3_id': row.get('ID', ''),
                                'sheet3_number': row.get('Số thứ tự thành viên trong dòng họ', ''),
                                'sheet3_death_place': row.get('Nơi mất', ''),
                                'sheet3_grave': row.get('Mộ phần', ''),
                                'sheet3_parents': row.get('Thông tin Bố Mẹ', ''),
                                'sheet3_siblings': row.get('Thông tin Anh/Chị/Em', ''),
                                'sheet3_spouse': row.get('Thông tin Hôn Phối', ''),
                                'sheet3_children': row.get('Thông tin Con', '')
                            }
                
                # Nếu không phân biệt được, trả về None (không dùng dữ liệu Sheet3)
                return None
                
    except Exception as e:
        print(f"Lỗi đọc Sheet3: {e}")
        return None
    
    return None

@app.route('/api/person/<int:person_id>')
def get_person(person_id):
    """Lấy thông tin chi tiết một người"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        # Lấy thông tin từ persons để có csv_id
        cursor.execute("""
            SELECT p.person_id, p.csv_id, p.full_name, p.common_name, p.gender,
                   g.generation_number, b.branch_name, p.status, p.nationality, p.religion,
                   p.origin_location_id
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN branches b ON p.branch_id = b.branch_id
            WHERE p.person_id = %s
        """, (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy'}), 404
        
        # Lấy thông tin từ v_person_full_info cho các trường khác
        cursor.execute("SELECT * FROM v_person_full_info WHERE person_id = %s", (person_id,))
        person_full = cursor.fetchone()
        if person_full:
            # Merge thông tin từ v_person_full_info (trừ các trường đã có)
            for key, value in person_full.items():
                if key not in person or person[key] is None:
                    person[key] = value
        
        # Tính siblings từ relationships (những người có cùng cha mẹ)
        if person:
            # Lấy thông tin cha mẹ của người này
            cursor.execute("""
                SELECT r.father_id, r.mother_id
                FROM relationships r
                WHERE r.child_id = %s
                LIMIT 1
            """, (person_id,))
            parent_rel = cursor.fetchone()
            
            if parent_rel and (parent_rel.get('father_id') or parent_rel.get('mother_id')):
                # Tìm những người có cùng cha mẹ
                parent_ids = []
                if parent_rel.get('father_id'):
                    parent_ids.append(parent_rel['father_id'])
                if parent_rel.get('mother_id'):
                    parent_ids.append(parent_rel['mother_id'])
                
                if parent_ids:
                    placeholders = ','.join(['%s'] * len(parent_ids))
                    cursor.execute(f"""
                        SELECT p.person_id, p.full_name
                        FROM persons p
                        JOIN relationships r ON p.person_id = r.child_id
                        WHERE (r.father_id IN ({placeholders}) OR r.mother_id IN ({placeholders}))
                        AND p.person_id != %s
                        ORDER BY p.full_name
                    """, parent_ids + parent_ids + [person_id])
                    siblings = cursor.fetchall()
                    if siblings:
                        sibling_names = [s['full_name'] for s in siblings]
                        person['siblings'] = '; '.join(sibling_names)
            
            # Lấy thông tin ngày sinh
            cursor.execute("""
                SELECT birth_date_solar, birth_date_lunar, birth_location_id
                FROM birth_records
                WHERE person_id = %s
            """, (person_id,))
            birth_record = cursor.fetchone()
            if birth_record:
                person['birth_date_solar'] = birth_record.get('birth_date_solar')
                person['birth_date_lunar'] = birth_record.get('birth_date_lunar')
                if birth_record.get('birth_location_id'):
                    cursor.execute("SELECT location_name FROM locations WHERE location_id = %s", 
                                 (birth_record['birth_location_id'],))
                    birth_loc = cursor.fetchone()
                    person['birth_location'] = birth_loc['location_name'] if birth_loc else None
            
            # Lấy thông tin ngày mất
            cursor.execute("""
                SELECT death_date_solar, death_date_lunar, death_location_id
                FROM death_records
                WHERE person_id = %s
            """, (person_id,))
            death_record = cursor.fetchone()
            if death_record:
                person['death_date_solar'] = death_record.get('death_date_solar')
                person['death_date_lunar'] = death_record.get('death_date_lunar')
                if death_record.get('death_location_id'):
                    cursor.execute("SELECT location_name FROM locations WHERE location_id = %s", 
                                 (death_record['death_location_id'],))
                    death_loc = cursor.fetchone()
                    person['death_location'] = death_loc['location_name'] if death_loc else None
            
            # Lấy nguyên quán
            if person.get('origin_location_id'):
                cursor.execute("SELECT location_name FROM locations WHERE location_id = %s", 
                             (person['origin_location_id'],))
                origin_loc = cursor.fetchone()
                person['origin_location'] = origin_loc['location_name'] if origin_loc else None
            
            # Lấy thông tin hôn phối từ bảng marriages_spouses
            cursor.execute("""
                SELECT marriage_id, spouse_name, spouse_gender, 
                       marriage_date_solar, marriage_date_lunar, 
                       marriage_place, notes, source
                FROM marriages_spouses
                WHERE person_id = %s AND is_active = TRUE
                ORDER BY marriage_date_solar, created_at
            """, (person_id,))
            marriages = cursor.fetchall()
            person['marriages'] = marriages
            
            # Format spouse thành string từ marriages_spouses (QUAN TRỌNG: lấy từ database, không từ Sheet3)
            if marriages:
                spouse_names = [m['spouse_name'] for m in marriages if m.get('spouse_name')]
                person['spouse'] = '; '.join(spouse_names) if spouse_names else None
            
            # Lấy thông tin con từ relationships (QUAN TRỌNG: lấy từ database, không từ Sheet3)
            cursor.execute("""
                SELECT r.child_id, p.full_name as child_name
                FROM relationships r
                JOIN persons p ON r.child_id = p.person_id
                WHERE (r.father_id = %s OR r.mother_id = %s)
                ORDER BY p.full_name
            """, (person_id, person_id))
            children_records = cursor.fetchall()
            if children_records:
                child_names = [c['child_name'] for c in children_records if c.get('child_name')]
                person['children'] = '; '.join(child_names) if child_names else None
            
            # Lấy dữ liệu từ Sheet3 CSV
            # QUAN TRỌNG: Truyền csv_id và tên bố/mẹ để phân biệt khi có nhiều người trùng tên
            person_name = person.get('full_name', '')
            csv_id = person.get('csv_id')
            
            # Lấy tên bố/mẹ - ưu tiên từ relationships (nếu có father_id/mother_id), 
            # fallback về persons.father_name/mother_name (từ CSV)
            cursor.execute("""
                SELECT 
                    r.father_id, r.mother_id,
                    COALESCE(f.full_name, p.father_name) AS father_name,
                    COALESCE(m.full_name, p.mother_name) AS mother_name
                FROM persons p
                LEFT JOIN relationships r ON r.child_id = p.person_id
                LEFT JOIN persons f ON r.father_id = f.person_id
                LEFT JOIN persons m ON r.mother_id = m.person_id
                WHERE p.person_id = %s
                LIMIT 1
            """, (person_id,))
            rel = cursor.fetchone()
            
            # Nếu vẫn không có, lấy trực tiếp từ persons table (backup)
            if not rel or (not rel.get('father_name') and not rel.get('mother_name')):
                cursor.execute("""
                    SELECT father_name, mother_name
                    FROM persons
                    WHERE person_id = %s
                """, (person_id,))
                person_names = cursor.fetchone()
                if person_names:
                    if rel:
                        rel['father_name'] = rel.get('father_name') or person_names.get('father_name')
                        rel['mother_name'] = rel.get('mother_name') or person_names.get('mother_name')
                    else:
                        rel = person_names
            
            # Thêm thông tin cha mẹ vào person object
            if rel:
                person['father_id'] = rel.get('father_id')
                person['father_name'] = rel.get('father_name')
                person['mother_id'] = rel.get('mother_id')
                person['mother_name'] = rel.get('mother_name')
            else:
                # Fallback cuối cùng: lấy từ persons table
                cursor.execute("""
                    SELECT father_name, mother_name
                    FROM persons
                    WHERE person_id = %s
                """, (person_id,))
                person_names = cursor.fetchone()
                if person_names:
                    person['father_name'] = person_names.get('father_name')
                    person['mother_name'] = person_names.get('mother_name')
            
            # =====================================================
            # LẤY THÔNG TIN TỔ TIÊN (ANCESTORS) - ĐỆ QUY
            # =====================================================
            try:
                # Sử dụng stored procedure để lấy tổ tiên (lên đến 10 cấp)
                cursor.callproc('sp_get_ancestors', [person_id, 10])
                
                # Lấy kết quả từ stored procedure
                ancestors_result = None
                for result_set in cursor.stored_results():
                    ancestors_result = result_set.fetchall()
                    break
                
                if ancestors_result:
                    # Chuyển đổi về dạng list of dicts
                    ancestors = []
                    for row in ancestors_result:
                        # Kiểm tra định dạng row (có thể là tuple hoặc dict)
                        if isinstance(row, dict):
                            ancestors.append({
                                'person_id': row.get('person_id'),
                                'full_name': row.get('full_name'),
                                'gender': row.get('gender'),
                                'generation_number': row.get('generation_number'),
                                'level': row.get('level', 0)
                            })
                        else:
                            # Nếu là tuple, giả định thứ tự: person_id, full_name, gender, generation_number, level
                            ancestors.append({
                                'person_id': row[0] if len(row) > 0 else None,
                                'full_name': row[1] if len(row) > 1 else '',
                                'gender': row[2] if len(row) > 2 else None,
                                'generation_number': row[3] if len(row) > 3 else None,
                                'level': row[4] if len(row) > 4 else 0
                            })
                    
                    person['ancestors'] = ancestors
                    
                    # Tính toán chuỗi phả hệ (tổ tiên theo thứ tự từ xa đến gần)
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
                        
                        ancestors_chain.append({
                            'level': level,
                            'level_name': level_name,
                            'full_name': ancestor.get('full_name', ''),
                            'generation_number': ancestor.get('generation_number'),
                            'gender': ancestor.get('gender'),
                            'person_id': ancestor.get('person_id')
                        })
                    
                    # Sắp xếp theo level (từ xa đến gần - level cao nhất trước)
                    ancestors_chain.sort(key=lambda x: x['level'], reverse=True)
                    person['ancestors_chain'] = ancestors_chain
                else:
                    person['ancestors'] = []
                    person['ancestors_chain'] = []
            except Exception as e:
                # Nếu stored procedure không hoạt động, thử cách khác (đệ quy thủ công)
                print(f"Lỗi khi gọi sp_get_ancestors: {e}")
                try:
                    # Thử lấy tổ tiên bằng cách đệ quy thủ công (3 cấp)
                    ancestors_chain = []
                    
                    # Cấp 1: Cha mẹ (đã có trong rel)
                    if rel:
                        if rel.get('father_id'):
                            cursor.execute("""
                                SELECT p.person_id, p.full_name, p.gender, g.generation_number
                                FROM persons p
                                LEFT JOIN generations g ON p.generation_id = g.generation_id
                                WHERE p.person_id = %s
                            """, (rel['father_id'],))
                            father = cursor.fetchone()
                            if father:
                                ancestors_chain.append({
                                    'level': 1,
                                    'level_name': 'Cha/Mẹ',
                                    'full_name': father.get('full_name', ''),
                                    'generation_number': father.get('generation_number'),
                                    'gender': father.get('gender'),
                                    'person_id': father.get('person_id')
                                })
                        
                        if rel.get('mother_id'):
                            cursor.execute("""
                                SELECT p.person_id, p.full_name, p.gender, g.generation_number
                                FROM persons p
                                LEFT JOIN generations g ON p.generation_id = g.generation_id
                                WHERE p.person_id = %s
                            """, (rel['mother_id'],))
                            mother = cursor.fetchone()
                            if mother:
                                ancestors_chain.append({
                                    'level': 1,
                                    'level_name': 'Cha/Mẹ',
                                    'full_name': mother.get('full_name', ''),
                                    'generation_number': mother.get('generation_number'),
                                    'gender': mother.get('gender'),
                                    'person_id': mother.get('person_id')
                                })
                    
                    # Cấp 2: Ông bà (cha/mẹ của cha/mẹ)
                    for ancestor in ancestors_chain[:]:  # Copy list để tránh modify trong khi iterate
                        if ancestor['level'] == 1 and ancestor['person_id']:
                            cursor.execute("""
                                SELECT r.father_id, r.mother_id,
                                       f.person_id AS father_person_id, f.full_name AS father_name, f.gender AS father_gender, g_f.generation_number AS father_gen,
                                       m.person_id AS mother_person_id, m.full_name AS mother_name, m.gender AS mother_gender, g_m.generation_number AS mother_gen
                                FROM relationships r
                                LEFT JOIN persons f ON r.father_id = f.person_id
                                LEFT JOIN persons m ON r.mother_id = m.person_id
                                LEFT JOIN generations g_f ON f.generation_id = g_f.generation_id
                                LEFT JOIN generations g_m ON m.generation_id = g_m.generation_id
                                WHERE r.child_id = %s
                            """, (ancestor['person_id'],))
                            parent_rel = cursor.fetchone()
                            if parent_rel:
                                if parent_rel.get('father_person_id'):
                                    ancestors_chain.append({
                                        'level': 2,
                                        'level_name': 'Ông/Bà',
                                        'full_name': parent_rel.get('father_name', ''),
                                        'generation_number': parent_rel.get('father_gen'),
                                        'gender': parent_rel.get('father_gender'),
                                        'person_id': parent_rel.get('father_person_id')
                                    })
                                if parent_rel.get('mother_person_id'):
                                    ancestors_chain.append({
                                        'level': 2,
                                        'level_name': 'Ông/Bà',
                                        'full_name': parent_rel.get('mother_name', ''),
                                        'generation_number': parent_rel.get('mother_gen'),
                                        'gender': parent_rel.get('mother_gender'),
                                        'person_id': parent_rel.get('mother_person_id')
                                    })
                    
                    # Sắp xếp theo level (từ xa đến gần)
                    ancestors_chain.sort(key=lambda x: x['level'], reverse=True)
                    person['ancestors_chain'] = ancestors_chain
                    person['ancestors'] = ancestors_chain
                except Exception as e2:
                    print(f"Lỗi khi lấy tổ tiên thủ công: {e2}")
                    person['ancestors'] = []
                    person['ancestors_chain'] = []
            
            if person_name:
                sheet3_data = get_sheet3_data_by_name(person_name, csv_id=csv_id, 
                                                      father_name=father_name, mother_name=mother_name)
                if sheet3_data:
                    # CHỈ lấy siblings từ Sheet3 (nếu có)
                    # QUAN TRỌNG: KHÔNG ghi đè spouse và children từ Sheet3
                    # Vì dữ liệu từ database (marriages_spouses và relationships) là chính xác hơn
                    if sheet3_data.get('sheet3_siblings'):
                        person['siblings'] = sheet3_data['sheet3_siblings']
                    # KHÔNG ghi đè spouse và children từ Sheet3
                    # person['spouse'] và person['children'] đã được lấy từ database ở trên
                    
                    # Thêm các trường mới từ Sheet3
                    person['sheet3_death_place'] = sheet3_data.get('sheet3_death_place', '')
                    person['sheet3_grave'] = sheet3_data.get('sheet3_grave', '')
                    person['sheet3_parents'] = sheet3_data.get('sheet3_parents', '')
                    person['sheet3_number'] = sheet3_data.get('sheet3_number', '')
        
        if person:
            return jsonify(person)
        return jsonify({'error': 'Không tìm thấy'}), 404
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/family-tree')
def get_family_tree():
    """Lấy cây gia phả"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM v_family_tree ORDER BY generation_number, full_name")
        tree = cursor.fetchall()
        return jsonify(tree)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/relationships')
def get_relationships():
    """Lấy quan hệ gia đình với ID"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                r.relationship_id,
                r.child_id,
                r.father_id,
                r.mother_id,
                r.relationship_type,
                child.full_name AS child_name,
                child.gender AS child_gender,
                father.full_name AS father_name,
                mother.full_name AS mother_name
            FROM relationships r
            INNER JOIN persons child ON r.child_id = child.person_id
            LEFT JOIN persons father ON r.father_id = father.person_id
            LEFT JOIN persons mother ON r.mother_id = mother.person_id
        """)
        relationships = cursor.fetchall()
        return jsonify(relationships)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/children/<int:parent_id>')
def get_children(parent_id):
    """Lấy con của một người"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.gender,
                g.generation_number
            FROM relationships r
            INNER JOIN persons p ON r.child_id = p.person_id
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            WHERE r.father_id = %s OR r.mother_id = %s
            ORDER BY p.full_name
        """, (parent_id, parent_id))
        children = cursor.fetchall()
        return jsonify(children)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/edit-requests', methods=['POST'])
def create_edit_request():
    """API tạo yêu cầu chỉnh sửa (không cần đăng nhập)"""
    try:
        data = request.get_json()
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation')
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'error': 'Nội dung yêu cầu không được để trống'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        try:
            cursor = connection.cursor()
            user_id = None
            if current_user.is_authenticated:
                user_id = current_user.id
            
            cursor.execute("""
                INSERT INTO edit_requests (person_id, person_name, person_generation, user_id, content, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (person_id, person_name, person_generation, user_id, content))
            connection.commit()
            
            return jsonify({'success': True, 'message': 'Yêu cầu đã được gửi thành công'})
        except Error as e:
            return jsonify({'error': f'Lỗi database: {str(e)}'}), 500
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/current-user')
def get_current_user():
    """Lấy thông tin user hiện tại (cho frontend check permissions) - không cần đăng nhập"""
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'authenticated': False,
            'user': None
        })
    
    # Tạo object có method hasPermission
    user_data = {
        'success': True,
        'authenticated': True,
        'user': {
            'user_id': current_user.id,
            'username': current_user.username,
            'role': current_user.role,
            'full_name': getattr(current_user, 'full_name', ''),
            'email': getattr(current_user, 'email', ''),
            'permissions': current_user.get_permissions() if hasattr(current_user, 'get_permissions') else {}
        }
    }
    
    return jsonify(user_data)

@app.route('/api/stats')
def get_stats():
    """Lấy thống kê"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Tổng số người
        cursor.execute("SELECT COUNT(*) AS total FROM persons")
        total = cursor.fetchone()['total']
        
        # Số thế hệ
        cursor.execute("SELECT MAX(generation_number) AS max_gen FROM generations")
        max_gen = cursor.fetchone()['max_gen'] or 0
        
        # Số quan hệ
        cursor.execute("SELECT COUNT(*) AS total FROM relationships")
        relationships = cursor.fetchone()['total']
        
        return jsonify({
            'total_people': total,
            'max_generation': max_gen,
            'total_relationships': relationships
        })
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/person/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Xóa một người (yêu cầu mật khẩu admin)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        # Lấy mật khẩu từ request
        data = request.get_json() or {}
        password = data.get('password', '').strip()
        correct_password = 'tbqc2026'
        
        # Kiểm tra mật khẩu
        if password != correct_password:
            return jsonify({'error': 'Mật khẩu không đúng'}), 403
        
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT full_name, generation_number FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy người với ID này'}), 404
        
        # Xóa person (CASCADE sẽ tự động xóa các bảng liên quan)
        cursor.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
        connection.commit()
        
        return jsonify({
            'success': True,
            'message': f'Đã xóa người: {person["full_name"]} (Đời {person["generation_number"]})',
            'person_id': person_id
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi khi xóa: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Helper functions để get hoặc create
def get_or_create_location(cursor, location_name, location_type):
    """Lấy hoặc tạo location"""
    if not location_name or not location_name.strip():
        return None
    
    location_name = location_name.strip()
    cursor.execute(
        "SELECT location_id FROM locations WHERE location_name = %s AND location_type = %s",
        (location_name, location_type)
    )
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute(
        "INSERT INTO locations (location_name, location_type, full_address) VALUES (%s, %s, %s)",
        (location_name, location_type, location_name)
    )
    return cursor.lastrowid

def get_or_create_generation(cursor, generation_number):
    """Lấy hoặc tạo generation"""
    if not generation_number:
        return None
    
    try:
        gen_num = int(generation_number)
    except:
        return None
    
    cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (gen_num,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO generations (generation_number) VALUES (%s)", (gen_num,))
    return cursor.lastrowid

def get_or_create_branch(cursor, branch_name):
    """Lấy hoặc tạo branch"""
    if not branch_name or not branch_name.strip():
        return None
    
    branch_name = branch_name.strip()
    cursor.execute("SELECT branch_id FROM branches WHERE branch_name = %s", (branch_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    cursor.execute("INSERT INTO branches (branch_name) VALUES (%s)", (branch_name,))
    return cursor.lastrowid

def find_person_by_name(cursor, name, generation_id=None):
    """Tìm person_id theo tên, có thể lọc theo generation_id"""
    if not name or not name.strip():
        return None
    
    name = name.strip()
    if generation_id:
        cursor.execute("""
            SELECT person_id FROM persons 
            WHERE full_name = %s AND generation_id = %s
            LIMIT 1
        """, (name, generation_id))
    else:
        cursor.execute("""
            SELECT person_id FROM persons 
            WHERE full_name = %s
            LIMIT 1
        """, (name,))
    
    result = cursor.fetchone()
    return result[0] if result else None

@app.route('/api/person/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """Cập nhật thông tin một người - LƯU TẤT CẢ DỮ LIỆU VÀO DATABASE"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT person_id, generation_id FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        if not person:
            return jsonify({'error': 'Không tìm thấy người này'}), 404
        
        current_generation_id = person['generation_id']
        
        # =====================================================
        # 1. CẬP NHẬT BẢNG PERSONS
        # =====================================================
        updates = {}
        
        if 'full_name' in data and data['full_name']:
            updates['full_name'] = data['full_name'].strip()
        
        if 'gender' in data:
            updates['gender'] = data['gender']
        
        if 'status' in data:
            updates['status'] = data['status']
        
        if 'nationality' in data:
            updates['nationality'] = data['nationality'].strip() if data['nationality'] else 'Việt Nam'
        
        if 'religion' in data:
            updates['religion'] = data['religion'].strip() if data['religion'] else None
        
        # Xử lý generation_number
        if 'generation_number' in data:
            generation_id = get_or_create_generation(cursor, data['generation_number'])
            if generation_id:
                updates['generation_id'] = generation_id
                current_generation_id = generation_id  # Cập nhật cho các bước sau
        
        # Xử lý branch_name
        if 'branch_name' in data:
            branch_id = get_or_create_branch(cursor, data['branch_name'])
            updates['branch_id'] = branch_id
        
        # Xử lý origin_location
        if 'origin_location' in data:
            origin_location_id = get_or_create_location(cursor, data['origin_location'], 'Nguyên quán')
            updates['origin_location_id'] = origin_location_id
        
        # Cập nhật bảng persons
        if updates:
            set_clause = ', '.join([f"{k} = %s" for k in updates.keys()])
            values = list(updates.values()) + [person_id]
            cursor.execute(f"""
                UPDATE persons 
                SET {set_clause}
                WHERE person_id = %s
            """, values)
        
        # =====================================================
        # 2. CẬP NHẬT BIRTH_RECORDS
        # =====================================================
        birth_location_id = None
        if 'birth_location' in data:
            birth_location_id = get_or_create_location(cursor, data['birth_location'], 'Nơi sinh')
        
        cursor.execute("SELECT birth_record_id FROM birth_records WHERE person_id = %s", (person_id,))
        birth_record = cursor.fetchone()
        
        if birth_record:
            # Update existing
            cursor.execute("""
                UPDATE birth_records 
                SET birth_date_solar = %s,
                    birth_date_lunar = %s,
                    birth_location_id = %s
                WHERE person_id = %s
            """, (
                data.get('birth_date_solar') or None,
                data.get('birth_date_lunar') or None,
                birth_location_id,
                person_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO birth_records (person_id, birth_date_solar, birth_date_lunar, birth_location_id)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                data.get('birth_date_solar') or None,
                data.get('birth_date_lunar') or None,
                birth_location_id
            ))
        
        # =====================================================
        # 3. CẬP NHẬT DEATH_RECORDS
        # =====================================================
        death_location_id = None
        if 'death_location' in data:
            death_location_id = get_or_create_location(cursor, data['death_location'], 'Nơi mất')
        
        cursor.execute("SELECT death_record_id FROM death_records WHERE person_id = %s", (person_id,))
        death_record = cursor.fetchone()
        
        if death_record:
            # Update existing
            cursor.execute("""
                UPDATE death_records 
                SET death_date_solar = %s,
                    death_date_lunar = %s,
                    death_location_id = %s
                WHERE person_id = %s
            """, (
                data.get('death_date_solar') or None,
                data.get('death_date_lunar') or None,
                death_location_id,
                person_id
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO death_records (person_id, death_date_solar, death_date_lunar, death_location_id)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                data.get('death_date_solar') or None,
                data.get('death_date_lunar') or None,
                death_location_id
            ))
        
        # =====================================================
        # 4. CẬP NHẬT RELATIONSHIPS (CHA/MẸ)
        # =====================================================
        father_id = None
        mother_id = None
        
        if 'father_name' in data and data['father_name']:
            # Tìm father_id: đời của cha = đời của con - 1
            father_generation_id = None
            if current_generation_id:
                cursor.execute("""
                    SELECT generation_id FROM generations 
                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)
                """, (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    father_generation_id = gen_result[0]
            
            father_id = find_person_by_name(cursor, data['father_name'], father_generation_id)
        
        if 'mother_name' in data and data['mother_name']:
            # Tìm mother_id: đời của mẹ = đời của con - 1
            mother_generation_id = None
            if current_generation_id:
                cursor.execute("""
                    SELECT generation_id FROM generations 
                    WHERE generation_number = (SELECT generation_number - 1 FROM generations WHERE generation_id = %s)
                """, (current_generation_id,))
                gen_result = cursor.fetchone()
                if gen_result:
                    mother_generation_id = gen_result[0]
            
            mother_id = find_person_by_name(cursor, data['mother_name'], mother_generation_id)
        
        # Cập nhật hoặc tạo relationship
        cursor.execute("SELECT relationship_id FROM relationships WHERE child_id = %s", (person_id,))
        relationship = cursor.fetchone()
        
        if relationship:
            cursor.execute("""
                UPDATE relationships 
                SET father_id = %s, mother_id = %s
                WHERE relationship_id = %s
            """, (father_id, mother_id, relationship['relationship_id']))
        else:
            cursor.execute("""
                INSERT INTO relationships (child_id, father_id, mother_id)
                VALUES (%s, %s, %s)
            """, (person_id, father_id, mother_id))
        
        # =====================================================
        # 5. CẬP NHẬT MARRIAGES_SPOUSES (VỢ/CHỒNG)
        # =====================================================
        if 'spouse' in data:
            spouse_text = data['spouse'].strip() if data['spouse'] else ''
            
            # Xóa tất cả marriages_spouses cũ (inactive)
            cursor.execute("""
                UPDATE marriages_spouses 
                SET is_active = FALSE 
                WHERE person_id = %s
            """, (person_id,))
            
            # Parse danh sách vợ/chồng (tách theo ; hoặc ,)
            if spouse_text:
                import re
                spouse_names = [s.strip() for s in re.split(r'[;,]', spouse_text) if s.strip()]
                
                for spouse_name in spouse_names:
                    # Kiểm tra đã tồn tại chưa
                    cursor.execute("""
                        SELECT marriage_id FROM marriages_spouses 
                        WHERE person_id = %s AND spouse_name = %s
                    """, (person_id, spouse_name))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Kích hoạt lại
                        cursor.execute("""
                            UPDATE marriages_spouses 
                            SET is_active = TRUE 
                            WHERE marriage_id = %s
                        """, (existing['marriage_id'],))
                    else:
                        # Tạo mới
                        # Tìm spouse_person_id nếu có
                        spouse_person_id = find_person_by_name(cursor, spouse_name)
                        cursor.execute("""
                            INSERT INTO marriages_spouses (person_id, spouse_name, spouse_person_id, is_active)
                            VALUES (%s, %s, %s, TRUE)
                        """, (person_id, spouse_name, spouse_person_id))
        
        # =====================================================
        # 6. COMMIT TẤT CẢ THAY ĐỔI
        # =====================================================
        connection.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Đã cập nhật và đồng bộ dữ liệu thành công!',
            'updated_fields': list(updates.keys()) + ['birth_records', 'death_records', 'relationships', 'marriages']
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi database: {str(e)}'}), 500
    except Exception as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/person/<int:person_id>/sync', methods=['POST'])
def sync_person(person_id):
    """Đồng bộ dữ liệu Person sau khi cập nhật
    - Đồng bộ relationships (cha mẹ, con cái)
    - Đồng bộ marriages_spouses (vợ/chồng)
    - Tính lại siblings từ relationships
    """
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        sync_messages = []
        
        # 1. Lấy thông tin person hiện tại
        cursor.execute("""
            SELECT p.person_id, p.csv_id, p.full_name, p.gender,
                   g.generation_number
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            WHERE p.person_id = %s
        """, (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy người này'}), 404
        
        # 2. Lấy thông tin từ relationships hiện tại
        cursor.execute("""
            SELECT r.father_id, r.mother_id,
                   f.full_name AS father_name, m.full_name AS mother_name
            FROM relationships r
            LEFT JOIN persons f ON r.father_id = f.person_id
            LEFT JOIN persons m ON r.mother_id = m.person_id
            WHERE r.child_id = %s
            LIMIT 1
        """, (person_id,))
        current_rel = cursor.fetchone()
        
        # 3. Lấy thông tin marriages_spouses hiện tại
        cursor.execute("""
            SELECT spouse_name, is_active
            FROM marriages_spouses
            WHERE person_id = %s
            ORDER BY is_active DESC, created_at
        """, (person_id,))
        current_spouses = cursor.fetchall()
        active_spouses = [s['spouse_name'] for s in current_spouses if s['is_active']]
        
        # 4. Lấy thông tin con cái hiện tại
        cursor.execute("""
            SELECT child.person_id, child.full_name
            FROM relationships r
            JOIN persons child ON r.child_id = child.person_id
            WHERE r.father_id = %s OR r.mother_id = %s
            ORDER BY child.full_name
        """, (person_id, person_id))
        current_children = cursor.fetchall()
        current_children_names = [c['full_name'] for c in current_children]
        
        sync_messages.append(f"Đã kiểm tra dữ liệu hiện tại:")
        sync_messages.append(f"- Vợ/Chồng: {len(active_spouses)} người ({', '.join(active_spouses) if active_spouses else 'Không có'})")
        sync_messages.append(f"- Con cái: {len(current_children)} người ({', '.join(current_children_names) if current_children_names else 'Không có'})")
        
        # 5. Tính lại siblings từ relationships (nếu có cha mẹ)
        if current_rel and (current_rel.get('father_id') or current_rel.get('mother_id')):
            parent_ids = []
            if current_rel.get('father_id'):
                parent_ids.append(current_rel['father_id'])
            if current_rel.get('mother_id'):
                parent_ids.append(current_rel['mother_id'])
            
            if parent_ids:
                placeholders = ','.join(['%s'] * len(parent_ids))
                cursor.execute(f"""
                    SELECT p.person_id, p.full_name
                    FROM persons p
                    JOIN relationships r ON p.person_id = r.child_id
                    WHERE (r.father_id IN ({placeholders}) OR r.mother_id IN ({placeholders}))
                    AND p.person_id != %s
                    ORDER BY p.full_name
                """, parent_ids + parent_ids + [person_id])
                siblings = cursor.fetchall()
                siblings_names = [s['full_name'] for s in siblings]
                sync_messages.append(f"- Anh/Chị/Em: {len(siblings)} người ({', '.join(siblings_names) if siblings_names else 'Không có'})")
        
        # 6. Đồng bộ hoàn tất
        connection.commit()
        
        message = '\n'.join(sync_messages)
        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'spouses_count': len(active_spouses),
                'children_count': len(current_children),
                'siblings_count': len(siblings) if 'siblings' in locals() else 0
            }
        })
        
    except Error as e:
        connection.rollback()
        return jsonify({'error': f'Lỗi khi đồng bộ: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/members')
def get_members():
    """API lấy danh sách thành viên với đầy đủ thông tin"""
    print("📥 API /api/members được gọi")
    connection = get_db_connection()
    if not connection:
        print("❌ Không thể kết nối database trong get_members()")
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Lấy danh sách tất cả persons với thông tin đầy đủ
        cursor.execute("""
            SELECT 
                p.person_id,
                p.csv_id,
                p.fm_id,
                p.full_name,
                p.gender,
                p.status,
                g.generation_number,
                br.birth_date_solar,
                br.birth_date_lunar,
                dr.death_date_solar,
                dr.death_date_lunar,
                dr.grave_location AS grave
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN birth_records br ON p.person_id = br.person_id
            LEFT JOIN death_records dr ON p.person_id = dr.person_id
            ORDER BY 
                COALESCE(g.generation_number, 999) ASC,
                CASE 
                    WHEN p.csv_id LIKE 'P%' AND SUBSTRING(p.csv_id, 2) REGEXP '^[0-9]+$' 
                    THEN CAST(SUBSTRING(p.csv_id, 2) AS UNSIGNED)
                    ELSE 999999
                END ASC,
                p.csv_id ASC,
                p.full_name ASC
        """)
        
        persons = cursor.fetchall()
        
        # Lấy thông tin quan hệ cho từng person
        members = []
        for person in persons:
            person_id = person['person_id']
            
            # Lấy tên bố/mẹ - ưu tiên từ relationships (nếu có father_id/mother_id), 
            # fallback về persons.father_name/mother_name (từ CSV)
            cursor.execute("""
                SELECT 
                    COALESCE(f.full_name, p.father_name) AS father_name,
                    COALESCE(m.full_name, p.mother_name) AS mother_name
                FROM persons p
                LEFT JOIN relationships r ON r.child_id = p.person_id
                LEFT JOIN persons f ON r.father_id = f.person_id
                LEFT JOIN persons m ON r.mother_id = m.person_id
                WHERE p.person_id = %s
                LIMIT 1
            """, (person_id,))
            rel = cursor.fetchone()
            
            # Nếu vẫn không có, lấy trực tiếp từ persons table (backup)
            if not rel:
                cursor.execute("""
                    SELECT father_name, mother_name
                    FROM persons
                    WHERE person_id = %s
                """, (person_id,))
                rel = cursor.fetchone()
            
            # Lấy hôn phối
            cursor.execute("""
                SELECT spouse_name
                FROM marriages_spouses
                WHERE person_id = %s AND is_active = TRUE
                ORDER BY created_at
            """, (person_id,))
            spouses = cursor.fetchall()
            
            # Lấy anh/chị/em
            cursor.execute("""
                SELECT COALESCE(p.full_name, sr.sibling_name) AS sibling_name
                FROM sibling_relationships sr
                LEFT JOIN persons p ON sr.sibling_person_id = p.person_id
                WHERE sr.person_id = %s
            """, (person_id,))
            siblings = cursor.fetchall()
            
            # Lấy con cái
            cursor.execute("""
                SELECT child.full_name
                FROM relationships r
                JOIN persons child ON r.child_id = child.person_id
                WHERE r.father_id = %s OR r.mother_id = %s
                ORDER BY child.full_name
            """, (person_id, person_id))
            children = cursor.fetchall()
            
            # Tạo object member
            member = {
                'person_id': person_id,
                'csv_id': person.get('csv_id'),
                'fm_id': person.get('fm_id'),
                'full_name': person.get('full_name'),
                'gender': person.get('gender'),
                'status': person.get('status'),
                'generation_number': person.get('generation_number'),
                'birth_date_solar': str(person['birth_date_solar']) if person.get('birth_date_solar') else None,
                'birth_date_lunar': str(person['birth_date_lunar']) if person.get('birth_date_lunar') else None,
                'death_date_solar': str(person['death_date_solar']) if person.get('death_date_solar') else None,
                'death_date_lunar': str(person['death_date_lunar']) if person.get('death_date_lunar') else None,
                'grave': person.get('grave'),
                'father_name': rel['father_name'] if rel else None,
                'mother_name': rel['mother_name'] if rel else None,
                'spouses': '; '.join([s['spouse_name'] for s in spouses]) if spouses else None,
                'siblings': '; '.join([s['sibling_name'] for s in siblings]) if siblings else None,
                'children': '; '.join([c['full_name'] for c in children]) if children else None
            }
            
            members.append(member)
        
        return jsonify({'success': True, 'data': members})
        
    except Error as e:
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/persons', methods=['POST'])
def create_person():
    """API thêm thành viên mới"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra csv_id đã tồn tại chưa
        if data.get('csv_id'):
            cursor.execute("SELECT person_id FROM persons WHERE csv_id = %s", (data['csv_id'],))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'ID {data["csv_id"]} đã tồn tại'}), 400
        
        # Lấy hoặc tạo generation_id nếu có generation_number
        generation_id = None
        if data.get('generation_number'):
            cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (data['generation_number'],))
            gen = cursor.fetchone()
            if gen:
                generation_id = gen['generation_id']
            else:
                cursor.execute("INSERT INTO generations (generation_number) VALUES (%s)", (data['generation_number'],))
                generation_id = cursor.lastrowid
        
        # Thêm person
        cursor.execute("""
            INSERT INTO persons (
                csv_id, fm_id, full_name, gender, status, generation_id, father_name, mother_name
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('csv_id'),
            data.get('fm_id'),
            data.get('full_name'),
            data.get('gender'),
            data.get('status', 'Không rõ'),
            generation_id,
            data.get('father_name'),
            data.get('mother_name')
        ))
        
        person_id = cursor.lastrowid
        
        # Nếu có tên bố/mẹ, tìm và tạo relationship
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
            
            if father_id or mother_id or data.get('fm_id'):
                # Kiểm tra relationship đã tồn tại chưa
                cursor.execute("""
                    SELECT relationship_id FROM relationships WHERE child_id = %s
                """, (person_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Cập nhật relationship hiện có
                    cursor.execute("""
                        UPDATE relationships SET
                            father_id = %s,
                            mother_id = %s,
                            fm_id = %s,
                            updated_at = NOW()
                        WHERE child_id = %s
                    """, (
                        father_id,
                        mother_id,
                        data.get('fm_id'),
                        person_id
                    ))
                else:
                    # Tạo relationship mới
                    cursor.execute("""
                        INSERT INTO relationships (child_id, father_id, mother_id, fm_id)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        person_id,
                        father_id,
                        mother_id,
                        data.get('fm_id')
                    ))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Thêm thành viên thành công', 'person_id': person_id})
        
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

@app.route('/api/persons/<int:person_id>', methods=['PUT'])
def update_person_members(person_id):
    """API cập nhật thành viên từ trang members"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        cursor = connection.cursor(dictionary=True)
        
        # Kiểm tra person có tồn tại không
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Không tìm thấy thành viên'}), 404
        
        # Kiểm tra csv_id trùng (nếu thay đổi)
        if data.get('csv_id'):
            cursor.execute("SELECT person_id FROM persons WHERE csv_id = %s AND person_id != %s", (data['csv_id'], person_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'error': f'ID {data["csv_id"]} đã tồn tại'}), 400
        
        # Lấy hoặc tạo generation_id
        generation_id = None
        if data.get('generation_number'):
            cursor.execute("SELECT generation_id FROM generations WHERE generation_number = %s", (data['generation_number'],))
            gen = cursor.fetchone()
            if gen:
                generation_id = gen['generation_id']
            else:
                cursor.execute("INSERT INTO generations (generation_number) VALUES (%s)", (data['generation_number'],))
                generation_id = cursor.lastrowid
        
        # Cập nhật person
        cursor.execute("""
            UPDATE persons SET
                csv_id = %s,
                fm_id = %s,
                full_name = %s,
                gender = %s,
                status = %s,
                generation_id = %s,
                father_name = %s,
                mother_name = %s,
                updated_at = NOW()
            WHERE person_id = %s
        """, (
            data.get('csv_id'),
            data.get('fm_id'),
            data.get('full_name'),
            data.get('gender'),
            data.get('status'),
            generation_id,
            data.get('father_name'),
            data.get('mother_name'),
            person_id
        ))
        
        # Cập nhật relationship
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
        
        # Kiểm tra relationship đã tồn tại chưa
        cursor.execute("""
            SELECT relationship_id FROM relationships WHERE child_id = %s
        """, (person_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Cập nhật relationship hiện có
            cursor.execute("""
                UPDATE relationships SET
                    father_id = %s,
                    mother_id = %s,
                    fm_id = %s,
                    updated_at = NOW()
                WHERE child_id = %s
            """, (
                father_id,
                mother_id,
                data.get('fm_id'),
                person_id
            ))
        else:
            # Tạo relationship mới
            cursor.execute("""
                INSERT INTO relationships (child_id, father_id, mother_id, fm_id)
                VALUES (%s, %s, %s, %s)
            """, (
                person_id,
                father_id,
                mother_id,
                data.get('fm_id')
            ))
        
        connection.commit()
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

@app.route('/api/persons/batch', methods=['DELETE'])
def delete_persons_batch():
    """API xóa nhiều thành viên"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        person_ids = data.get('person_ids', [])
        
        if not person_ids:
            return jsonify({'success': False, 'error': 'Không có ID nào được chọn'}), 400
        
        cursor = connection.cursor()
        
        # Xóa theo batch (cascade sẽ tự động xóa relationships, marriages, etc.)
        placeholders = ','.join(['%s'] * len(person_ids))
        cursor.execute(f"DELETE FROM persons WHERE person_id IN ({placeholders})", tuple(person_ids))
        
        deleted_count = cursor.rowcount
        connection.commit()
        
        return jsonify({'success': True, 'message': f'Đã xóa {deleted_count} thành viên'})
        
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

@app.route('/api/send-edit-request-email', methods=['POST'])
def send_edit_request_email():
    """API gửi email yêu cầu cập nhật thông tin"""
    try:
        data = request.get_json()
        
        person_id = data.get('person_id')
        person_name = data.get('person_name', '')
        person_generation = data.get('person_generation', '')
        requester_name = data.get('requester_name', '')
        requester_contact = data.get('requester_contact', '')
        content = data.get('content', '')
        
        if not requester_name or not requester_contact or not content:
            return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin'}), 400
        
        # Tạo nội dung email
        email_subject = f"Yêu cầu cập nhật thông tin: {person_name} (Đời {person_generation})"
        email_body = f"""
Yêu cầu cập nhật thông tin gia phả

Thông tin người cần cập nhật:
- ID: P{person_id}
- Họ và tên: {person_name}
- Đời: {person_generation}

Thông tin người gửi yêu cầu:
- Họ và tên: {requester_name}
- Email/SĐT: {requester_contact}

Nội dung yêu cầu cập nhật:
{content}

---
Email này được gửi tự động từ hệ thống Gia Phả Nguyễn Phước Tộc
"""
        
        # Gửi email qua SMTP
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Log thông tin yêu cầu
            print("="*80)
            print("📧 YÊU CẦU CẬP NHẬT THÔNG TIN")
            print("="*80)
            print(f"Người cần cập nhật: {person_name} (Đời {person_generation}, ID: P{person_id})")
            print(f"Người gửi: {requester_name}")
            print(f"Liên hệ: {requester_contact}")
            print(f"Nội dung: {content}")
            print("="*80)
            
            # Cấu hình SMTP - lấy từ biến môi trường hoặc file config
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            smtp_user = os.environ.get('SMTP_USER', '')
            smtp_password = os.environ.get('SMTP_PASSWORD', '')
            smtp_to = os.environ.get('SMTP_TO', 'baophongcmu@gmail.com')
            
            # Thử đọc từ file config nếu có
            config_file = os.path.join(BASE_DIR, '.smtp_config')
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == 'SMTP_SERVER' and not smtp_server:
                                    smtp_server = value
                                elif key == 'SMTP_PORT' and not smtp_port:
                                    smtp_port = int(value)
                                elif key == 'SMTP_USER' and not smtp_user:
                                    smtp_user = value
                                elif key == 'SMTP_PASSWORD' and not smtp_password:
                                    smtp_password = value
                                elif key == 'SMTP_TO' and not smtp_to:
                                    smtp_to = value
                except Exception as config_error:
                    print(f"⚠️  Lỗi đọc file config: {config_error}")
            
            if smtp_user and smtp_password:
                try:
                    # Tạo email
                    msg = MIMEMultipart()
                    msg['From'] = smtp_user
                    msg['To'] = smtp_to
                    msg['Subject'] = email_subject
                    msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
                    
                    # Gửi email
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                    server.quit()
                    
                    print(f"✅ Email đã được gửi thành công đến {smtp_to}")
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được gửi thành công đến email baophongcmu@gmail.com. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
                except Exception as email_error:
                    print(f"⚠️  Lỗi khi gửi email qua SMTP: {email_error}")
                    import traceback
                    traceback.print_exc()
                    # Vẫn trả về success nhưng log lỗi
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
            else:
                print("⚠️  SMTP chưa được cấu hình.")
                print("Vui lòng cấu hình bằng một trong các cách sau:")
                print("1. Set biến môi trường:")
                print("   - SMTP_SERVER (mặc định: smtp.gmail.com)")
                print("   - SMTP_PORT (mặc định: 587)")
                print("   - SMTP_USER (email gửi)")
                print("   - SMTP_PASSWORD (mật khẩu hoặc app password)")
                print("   - SMTP_TO (mặc định: baophongcmu@gmail.com)")
                print("2. Hoặc tạo file .smtp_config trong thư mục root với nội dung:")
                print("   SMTP_SERVER=smtp.gmail.com")
                print("   SMTP_PORT=587")
                print("   SMTP_USER=your-email@gmail.com")
                print("   SMTP_PASSWORD=your-app-password")
                print("   SMTP_TO=baophongcmu@gmail.com")
                print("Nội dung yêu cầu đã được ghi log ở trên")
                return jsonify({
                    'success': True, 
                    'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                })
            
        except Exception as e:
            # Nếu không gửi được email, vẫn trả về success nhưng log lỗi
            print(f"⚠️  Lỗi khi xử lý email: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': True, 
                'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
            })
            
    except Exception as e:
        print(f"❌ Lỗi khi xử lý yêu cầu: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500

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
    
    # Test database connection
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

@app.route('/api/stats/members', methods=['GET'])
def api_member_stats():
    """Trả về thống kê thành viên: tổng, nam, nữ, không rõ"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_members,
                SUM(CASE WHEN gender = 'Nam' THEN 1 ELSE 0 END) AS male_count,
                SUM(CASE WHEN gender = 'Nữ' THEN 1 ELSE 0 END) AS female_count,
                SUM(CASE 
                        WHEN gender IS NULL OR gender = '' OR gender NOT IN ('Nam', 'Nữ') 
                        THEN 1 ELSE 0 END) AS unknown_gender_count
            FROM persons
        """)
        row = cursor.fetchone() or {}
        return jsonify({
            'total_members': row.get('total_members', 0),
            'male_count': row.get('male_count', 0),
            'female_count': row.get('female_count', 0),
            'unknown_gender_count': row.get('unknown_gender_count', 0)
        })
    except Exception as e:
        print(f"❌ Lỗi khi lấy thống kê thành viên: {e}")
        return jsonify({'success': False, 'error': 'Không thể lấy thống kê'}), 500
    finally:
        try:
            if connection.is_connected():
                cursor.close()
                connection.close()
        except Exception:
            pass

@app.route('/api/login', methods=['POST'])
def api_login():
    """API đăng nhập (trả về JSON)"""
    from flask_login import login_user
    from auth import get_user_by_username, verify_password, User
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Vui lòng nhập đầy đủ username và password'}), 400
    
    # Tìm user
    user_data = get_user_by_username(username)
    if not user_data:
        return jsonify({'success': False, 'error': 'Không tồn tại tài khoản'}), 401
    
    # Xác thực mật khẩu
    if not verify_password(password, user_data['password_hash']):
        return jsonify({'success': False, 'error': 'Sai mật khẩu'}), 401
    
    # Tạo user object và đăng nhập
    permissions = user_data.get('permissions', {})
    user = User(
        user_id=user_data['user_id'],
        username=user_data['username'],
        role=user_data['role'],
        full_name=user_data.get('full_name'),
        email=user_data.get('email'),
        permissions=permissions
    )
    
    login_user(user, remember=True)
    
    # Cập nhật last_login
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE users 
                SET last_login = NOW() 
                WHERE user_id = %s
            """, (user_data['user_id'],))
            connection.commit()
        except Error as e:
            print(f"Lỗi cập nhật last_login: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    # Check redirect parameter or default to activities management for admins
    redirect_to = request.form.get('redirect', '')
    if not redirect_to:
        # Default: admins go to activities management, others to activities page
        if user.role == 'admin':
            redirect_to = '/admin/activities'
        else:
            redirect_to = '/activities'
    
    return jsonify({
        'success': True,
        'message': 'Đăng nhập thành công',
        'user': {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'full_name': user.full_name,
            'email': user.email
        },
        'redirect': redirect_to
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    """API đăng xuất"""
    from flask_login import logout_user
    logout_user()
    return jsonify({'success': True, 'message': 'Đã đăng xuất thành công'})


# Print startup info (chạy mỗi khi import, không chỉ khi __main__)
print("="*80)
print("🚀 FLASK APP ĐANG KHỞI ĐỘNG...")
print("="*80)
print(f"📂 Working directory: {os.getcwd()}")
print(f"📂 Base directory: {BASE_DIR}")
print(f"📂 __file__: {__file__}")
print("="*80)

if __name__ == '__main__':
    print("\n🌐 Server sẽ chạy tại:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Thành viên: http://localhost:5000/members")
    print("   - Admin: http://localhost:5000/admin/login")
    print("\n⚠️  Nhấn Ctrl+C để dừng server")
    print("="*80 + "\n")
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"🌐 Starting server on port {port}...")
        app.run(debug=False, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"\n❌ LỖI KHI KHỞI ĐỘNG SERVER: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
