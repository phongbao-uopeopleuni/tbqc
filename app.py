#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory, request, redirect, render_template
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import os
import secrets
import csv
import sys
import logging

logger = logging.getLogger(__name__)

# Xác định thư mục root của project (thư mục chứa index.html)
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"BASE_DIR: {BASE_DIR}")
except Exception as e:
    print(f"ERROR: Loi khi xac dinh BASE_DIR: {e}")
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    # Flask config với templates và static folders chuẩn
    app = Flask(__name__, 
                static_folder='static', 
                static_url_path='/static',
                template_folder='templates')
    app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
    CORS(app)  # Cho phép frontend gọi API
    print("OK: Flask app da duoc khoi tao")
    print(f"   Static folder: {app.static_folder}")
    print(f"   Template folder: {app.template_folder}")
except Exception as e:
    print(f"ERROR: Loi khi khoi tao Flask app: {e}")
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
    print(f"WARNING: Loi khi khoi tao login manager: {e}")
    import traceback
    traceback.print_exc()

# Import và đăng ký admin routes
try:
    from admin_routes import register_admin_routes
except ImportError:
    try:
        from folder_py.admin_routes import register_admin_routes
    except ImportError as e:
        print(f"WARNING: Khong the import admin_routes: {e}")
        register_admin_routes = None

if register_admin_routes:
    try:
        register_admin_routes(app)
    except Exception as e:
        print(f"WARNING: Loi khi dang ky admin routes: {e}")

# Import và đăng ký marriage routes
try:
    from marriage_api import register_marriage_routes
except ImportError:
    try:
        from folder_py.marriage_api import register_marriage_routes
    except ImportError as e:
        print(f"WARNING: Khong the import marriage_api: {e}")
        register_marriage_routes = None

if register_marriage_routes:
    try:
        register_marriage_routes(app)
    except Exception as e:
        print(f"WARNING: Loi khi dang ky marriage routes: {e}")

# Import unified DB config and connection
try:
    from folder_py.db_config import get_db_config, get_db_connection
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from db_config import get_db_config, get_db_connection
    except ImportError:
        print("WARNING: Cannot import db_config, using fallback")
        def get_db_config():
            return {
                'host': os.environ.get('DB_HOST') or os.environ.get('MYSQLHOST') or 'localhost',
                'database': os.environ.get('DB_NAME') or os.environ.get('MYSQLDATABASE') or 'tbqc2025',
                'user': os.environ.get('DB_USER') or os.environ.get('MYSQLUSER') or 'tbqc_admin',
                'password': os.environ.get('DB_PASSWORD') or os.environ.get('MYSQLPASSWORD') or 'tbqc2025',
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
        def get_db_connection():
            import mysql.connector
            from mysql.connector import Error
            try:
                config = get_db_config()
                return mysql.connector.connect(**config)
            except Error as e:
                print(f"ERROR: Loi ket noi database: {e}")
                return None

# Get DB config for health endpoint
DB_CONFIG = get_db_config()

@app.route('/')
def index():
    """Trang chủ - render template"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Trang đăng nhập (public)"""
    return render_template('login.html')

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
    return render_template('members.html')

@app.route('/gia-pha')
def genealogy_old():
    """Trang gia phả cũ (backup)"""
    return send_from_directory(BASE_DIR, 'gia-pha-nguyen-phuoc-toc.html')

# Legacy routes for JS files (now served from static/js/)
# These are kept for backward compatibility but templates should use /static/js/
@app.route('/family-tree-core.js')
def serve_core_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'family-tree-core.js', mimetype='application/javascript')

@app.route('/family-tree-ui.js')
def serve_ui_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'family-tree-ui.js', mimetype='application/javascript')

@app.route('/genealogy-lineage.js')
def serve_genealogy_js():
    """Legacy route - serves from static/js/"""
    return send_from_directory('static/js', 'genealogy-lineage.js', mimetype='application/javascript')

# Image routes - serve from static/images/
@app.route('/static/images/<path:filename>')
def serve_image_static(filename):
    """Serve images from static/images/"""
    return send_from_directory('static/images', filename)

# Legacy route for backward compatibility
@app.route('/images/<path:filename>')
def serve_image(filename):
    """Legacy route - serves from static/images/"""
    return send_from_directory('static/images', filename)

@app.route('/test_genealogy_lineage.html')
def serve_test_page():
    """Serve trang test genealogy lineage"""
    return send_from_directory(BASE_DIR, 'test_genealogy_lineage.html')

@app.route('/api/persons')
def get_persons():
    """Lấy danh sách tất cả người từ schema mới (person_id VARCHAR, relationships mới)"""
    print("📥 API /api/persons được gọi")
    connection = get_db_connection()
    if not connection:
        print("ERROR: Khong the ket noi database trong get_persons()")
        return jsonify({'error': 'Không thể kết nối database'}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Query chính: lấy mỗi person 1 dòng, kèm thông tin cha/mẹ và danh sách tên con
        # Schema mới: person_id VARCHAR(50), relationships dùng parent_id/child_id với relation_type
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level,
                p.home_town,
                p.nationality,
                p.religion,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id,

                -- Cha từ relationships
                father.person_id AS father_id,
                father.full_name AS father_name,

                -- Mẹ từ relationships
                mother.person_id AS mother_id,
                mother.full_name AS mother_name,

                -- Con cái
                GROUP_CONCAT(
                    DISTINCT child.full_name
                    ORDER BY child.full_name
                    SEPARATOR '; '
                ) AS children
            FROM persons p

            -- Cha từ relationships (relation_type = 'father')
            LEFT JOIN relationships rel_father
                ON rel_father.child_id = p.person_id 
                AND rel_father.relation_type = 'father'
            LEFT JOIN persons father
                ON rel_father.parent_id = father.person_id

            -- Mẹ từ relationships (relation_type = 'mother')
            LEFT JOIN relationships rel_mother
                ON rel_mother.child_id = p.person_id 
                AND rel_mother.relation_type = 'mother'
            LEFT JOIN persons mother
                ON rel_mother.parent_id = mother.person_id

            -- Con cái: những người có parent_id = p.person_id
            LEFT JOIN relationships rel_child
                ON rel_child.parent_id = p.person_id
                AND rel_child.relation_type IN ('father', 'mother')
            LEFT JOIN persons child
                ON child.person_id = rel_child.child_id

            GROUP BY
                p.person_id,
                p.full_name,
                p.alias,
                p.gender,
                p.status,
                p.generation_level,
                p.home_town,
                p.nationality,
                p.religion,
                p.birth_date_solar,
                p.birth_date_lunar,
                p.death_date_solar,
                p.death_date_lunar,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id,
                father.person_id,
                father.full_name,
                mother.person_id,
                mother.full_name
            ORDER BY
                p.generation_level,
                p.full_name
        """)

        persons = cursor.fetchall()

        # Tính thêm siblings và spouses bằng Python
        for person in persons:
            person_id = person['person_id']

            # Lấy cha/mẹ từ relationships để tìm anh/chị/em ruột
            cursor.execute("""
                SELECT parent_id, relation_type
                FROM relationships
                WHERE child_id = %s AND relation_type IN ('father', 'mother')
            """, (person_id,))
            parent_rels = cursor.fetchall()
            
            father_id = None
            mother_id = None
            for rel in parent_rels:
                if rel['relation_type'] == 'father':
                    father_id = rel['parent_id']
                elif rel['relation_type'] == 'mother':
                    mother_id = rel['parent_id']

            if father_id or mother_id:
                # Tìm siblings (cùng cha hoặc cùng mẹ)
                conditions = []
                params = [person_id]
                
                if father_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'father')")
                    params.append(father_id)
                if mother_id:
                    conditions.append("(r.parent_id = %s AND r.relation_type = 'mother')")
                    params.append(mother_id)

                sibling_query = f"""
                    SELECT DISTINCT s.full_name
                    FROM persons s
                    JOIN relationships r ON s.person_id = r.child_id
                    WHERE s.person_id <> %s
                      AND ({' OR '.join(conditions)})
                    ORDER BY s.full_name
                """
                cursor.execute(sibling_query, params)
                siblings = cursor.fetchall()
                person['siblings'] = '; '.join(
                    [s['full_name'] for s in siblings]
                ) if siblings else None
            else:
                person['siblings'] = None

            # Lấy spouses từ marriages
            cursor.execute("""
                SELECT DISTINCT 
                    CASE 
                        WHEN m.person_id = %s THEN m.spouse_person_id
                        ELSE m.person_id
                    END AS spouse_id,
                    sp.full_name AS spouse_name
                FROM marriages m
                JOIN persons sp ON (
                    CASE 
                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                        ELSE sp.person_id = m.person_id
                    END
                )
                WHERE (m.person_id = %s OR m.spouse_person_id = %s)
                AND m.status != 'Đã ly dị'
            """, (person_id, person_id, person_id, person_id))
            spouses = cursor.fetchall()
            if spouses:
                spouse_names = [s['spouse_name'] for s in spouses if s.get('spouse_name')]
                person['spouse'] = '; '.join(spouse_names) if spouse_names else None
            else:
                person['spouse'] = None

        return jsonify(persons)

    except Error as e:
        print(f"ERROR: Loi trong /api/persons: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@app.route("/api/generations", methods=["GET"])
def get_generations_api():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()  # use the existing helper in app.py
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                generation_id,
                generation_number,
                description AS generation_name
            FROM generations
            ORDER BY generation_number
        """)
        rows = cursor.fetchall()
        return jsonify(rows), 200
    except Exception as e:
        print("Error in /api/generations:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

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

@app.route('/api/person/<person_id>')
def get_person(person_id):
    """Lấy thông tin chi tiết một người từ schema mới"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Lấy thông tin từ persons (schema mới)
        cursor.execute("""
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
                p.nationality,
                p.religion,
                p.place_of_death,
                p.grave_info,
                p.contact,
                p.social,
                p.occupation,
                p.education,
                p.events,
                p.titles,
                p.blood_type,
                p.genetic_disease,
                p.note,
                p.father_mother_id
            FROM persons p
            WHERE p.person_id = %s
        """, (person_id,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Không tìm thấy'}), 404
        
        # Lấy thông tin cha mẹ từ relationships
            cursor.execute("""
            SELECT 
                r.parent_id,
                r.relation_type,
                parent.full_name AS parent_name
                FROM relationships r
            JOIN persons parent ON r.parent_id = parent.person_id
            WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
            """, (person_id,))
        parent_rels = cursor.fetchall()
        
        father_id = None
        father_name = None
        mother_id = None
        mother_name = None
        
        for rel in parent_rels:
            if rel['relation_type'] == 'father':
                father_id = rel['parent_id']
                father_name = rel['parent_name']
            elif rel['relation_type'] == 'mother':
                mother_id = rel['parent_id']
                mother_name = rel['parent_name']
        
        person['father_id'] = father_id
        person['father_name'] = father_name
        person['mother_id'] = mother_id
        person['mother_name'] = mother_name
        
        # Lấy siblings (cùng cha hoặc cùng mẹ)
        if father_id or mother_id:
            conditions = []
            params = [person_id]
            
            if father_id:
                conditions.append("(r.parent_id = %s AND r.relation_type = 'father')")
                params.append(father_id)
            if mother_id:
                conditions.append("(r.parent_id = %s AND r.relation_type = 'mother')")
                params.append(mother_id)
            
            sibling_query = f"""
                SELECT DISTINCT s.person_id, s.full_name
                FROM persons s
                JOIN relationships r ON s.person_id = r.child_id
                WHERE s.person_id <> %s
                  AND ({' OR '.join(conditions)})
                ORDER BY s.full_name
            """
            cursor.execute(sibling_query, params)
            siblings = cursor.fetchall()
            if siblings:
                sibling_names = [s['full_name'] for s in siblings]
                person['siblings'] = '; '.join(sibling_names)
            else:
                person['siblings'] = None
            
            # Lấy con từ relationships
            cursor.execute("""
            SELECT 
                r.child_id,
                child.full_name AS child_name
                FROM relationships r
            JOIN persons child ON r.child_id = child.person_id
            WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')
            ORDER BY child.full_name
        """, (person_id,))
            children_records = cursor.fetchall()
            if children_records:
                child_names = [c['child_name'] for c in children_records if c.get('child_name')]
                person['children'] = '; '.join(child_names) if child_names else None
            
        # Lấy spouses từ marriages
            cursor.execute("""
                SELECT 
                m.id AS marriage_id,
                CASE 
                    WHEN m.person_id = %s THEN m.spouse_person_id
                    ELSE m.person_id
                END AS spouse_id,
                sp.full_name AS spouse_name,
                sp.gender AS spouse_gender,
                m.status AS marriage_status,
                m.note AS marriage_note
            FROM marriages m
            JOIN persons sp ON (
                CASE 
                    WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                    ELSE sp.person_id = m.person_id
                END
            )
            WHERE (m.person_id = %s OR m.spouse_person_id = %s)
            ORDER BY m.created_at
        """, (person_id, person_id, person_id, person_id))
        marriages = cursor.fetchall()
        
        if marriages:
            person['marriages'] = marriages
            spouse_names = [m['spouse_name'] for m in marriages if m.get('spouse_name')]
            person['spouse'] = '; '.join(spouse_names) if spouse_names else None
        else:
            person['marriages'] = []
            person['spouse'] = None
            
            # =====================================================
            # LẤY THÔNG TIN TỔ TIÊN (ANCESTORS) - ĐỆ QUY
            # =====================================================
            try:
            # Sử dụng stored procedure mới để lấy tổ tiên (lên đến 10 cấp)
            # Schema mới: person_id là VARCHAR(50)
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
                            'generation_level': row.get('generation_level'),
                                'level': row.get('level', 0)
                            })
                        else:
                        # Nếu là tuple, giả định thứ tự: person_id, full_name, gender, generation_level, level
                            ancestors.append({
                                'person_id': row[0] if len(row) > 0 else None,
                                'full_name': row[1] if len(row) > 1 else '',
                                'gender': row[2] if len(row) > 2 else None,
                            'generation_level': row[3] if len(row) > 3 else None,
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
                        'generation_level': ancestor.get('generation_level'),
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
                    
                    # Cấp 1: Cha mẹ (đã có trong person)
                    if father_id:
                        cursor.execute("""
                            SELECT p.person_id, p.full_name, p.gender, p.generation_level
                            FROM persons p
                            WHERE p.person_id = %s
                        """, (father_id,))
                        father = cursor.fetchone()
                        if father:
                            ancestors_chain.append({
                                'level': 1,
                                'level_name': 'Cha/Mẹ',
                                'full_name': father.get('full_name', ''),
                                'generation_level': father.get('generation_level'),
                                'gender': father.get('gender'),
                                'person_id': father.get('person_id')
                            })
                    
                    if mother_id:
                        cursor.execute("""
                            SELECT p.person_id, p.full_name, p.gender, p.generation_level
                            FROM persons p
                            WHERE p.person_id = %s
                        """, (mother_id,))
                        mother = cursor.fetchone()
                        if mother:
                            ancestors_chain.append({
                                'level': 1,
                                'level_name': 'Cha/Mẹ',
                                'full_name': mother.get('full_name', ''),
                                'generation_level': mother.get('generation_level'),
                                'gender': mother.get('gender'),
                                'person_id': mother.get('person_id')
                            })
                    
                    # Cấp 2: Ông bà (cha/mẹ của cha/mẹ)
                    for ancestor in ancestors_chain[:]:  # Copy list để tránh modify trong khi iterate
                        if ancestor['level'] == 1 and ancestor['person_id']:
                            cursor.execute("""
                                SELECT 
                                    r.parent_id,
                                    r.relation_type,
                                    parent.person_id,
                                    parent.full_name,
                                    parent.gender,
                                    parent.generation_level
                                FROM relationships r
                                JOIN persons parent ON r.parent_id = parent.person_id
                                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
                            """, (ancestor['person_id'],))
                            parent_rels = cursor.fetchall()
                            for parent_rel in parent_rels:
                                ancestors_chain.append({
                                    'level': 2,
                                    'level_name': 'Ông/Bà',
                                    'full_name': parent_rel.get('full_name', ''),
                                    'generation_level': parent_rel.get('generation_level'),
                                    'gender': parent_rel.get('gender'),
                                    'person_id': parent_rel.get('person_id')
                                })
                    
                    # Sắp xếp theo level (từ xa đến gần)
                    ancestors_chain.sort(key=lambda x: x['level'], reverse=True)
                    person['ancestors_chain'] = ancestors_chain
                    person['ancestors'] = ancestors_chain
                except Exception as e2:
                    print(f"Lỗi khi lấy tổ tiên thủ công: {e2}")
                    person['ancestors_chain'] = []
                    person['ancestors'] = []
                    person['ancestors'] = []
                    person['ancestors_chain'] = []
        
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
    """Lấy quan hệ gia đình với ID (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                r.id AS relationship_id,
                r.child_id,
                r.parent_id,
                r.relation_type,
                child.full_name AS child_name,
                child.gender AS child_gender,
                parent.full_name AS parent_name,
                parent.gender AS parent_gender
            FROM relationships r
            INNER JOIN persons child ON r.child_id = child.person_id
            INNER JOIN persons parent ON r.parent_id = parent.person_id
            ORDER BY r.id
        """)
        relationships = cursor.fetchall()
        return jsonify(relationships)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/children/<parent_id>')
def get_children(parent_id):
    """Lấy con của một người (schema mới)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        # Schema mới: dùng stored procedure hoặc query trực tiếp
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.gender,
                p.generation_level,
                r.relation_type
            FROM relationships r
            INNER JOIN persons p ON r.child_id = p.person_id
            WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')
            ORDER BY p.full_name
        """, (parent_id,))
        children = cursor.fetchall()
        return jsonify(children)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Import genealogy tree helpers
try:
    from folder_py.genealogy_tree import (
        build_tree,
        build_ancestors_chain,
        build_descendants,
        build_children_map,
        build_parent_map,
        load_persons_data
    )
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from genealogy_tree import (
            build_tree,
            build_ancestors_chain,
            build_descendants,
            build_children_map,
            build_parent_map,
            load_persons_data
        )
    except ImportError as e:
        logger.warning(f"Cannot import genealogy_tree: {e}")
        build_tree = None
        build_ancestors_chain = None
        build_descendants = None
        build_children_map = None
        build_parent_map = None
        load_persons_data = None

@app.route('/api/tree', methods=['GET'])
def get_tree():
    """Get genealogy tree from root_id up to max_gen (schema mới)"""
    # Kiểm tra xem genealogy_tree functions có sẵn không
    if build_tree is None or load_persons_data is None or build_children_map is None:
        logger.error("genealogy_tree functions not available")
        return jsonify({'error': 'Tree functions not available. Please check server logs.'}), 500
    
    connection = None
    cursor = None
    
    try:
        root_id = request.args.get('root_id', 'P-1-1')  # Default to P-1-1 (Vua Minh Mạng)
        # Hỗ trợ cả max_gen và max_generation (frontend có thể dùng max_generation)
        max_gen_param = request.args.get('max_gen')
        max_generation_param = request.args.get('max_generation')
        
        if max_gen_param:
            max_gen = int(max_gen_param)
        elif max_generation_param:
            max_gen = int(max_generation_param)
        else:
            max_gen = 5  # Default value
            
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid max_gen or max_generation parameter: {e}")
        return jsonify({'error': 'Invalid max_gen or max_generation parameter. Must be an integer.'}), 400
    
    try:
        connection = get_db_connection()
        if not connection:
            logger.error("Cannot connect to database")
            return jsonify({'error': 'Không thể kết nối database'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Validate root_id exists
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (root_id,))
        if not cursor.fetchone():
            logger.warning(f"Person {root_id} not found in database")
            return jsonify({'error': f'Person {root_id} not found'}), 404
        
        # Load all persons data
        persons_by_id = load_persons_data(cursor)
        logger.info(f"Loaded {len(persons_by_id)} persons from database")
        
        # Build children map
        children_map = build_children_map(cursor)
        logger.info(f"Built children map with {len(children_map)} parent-child relationships")
        
        # Build tree
        tree = build_tree(root_id, persons_by_id, children_map, 1, max_gen)
        
        if not tree:
            logger.error(f"Could not build tree for root_id={root_id}")
            return jsonify({'error': 'Could not build tree'}), 500
        
        logger.info(f"Built tree for root_id={root_id}, max_gen={max_gen}, nodes={len(persons_by_id)}")
        return jsonify(tree)
        
    except Error as e:
        logger.error(f"Database error in /api/tree: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/tree: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

@app.route('/api/ancestors/<person_id>', methods=['GET'])
def get_ancestors(person_id):
    """Get ancestors chain for a person (schema mới - dùng stored procedure)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        max_level = int(request.args.get('max_level', 10))
    except (ValueError, TypeError):
        max_level = 10
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Validate person_id exists
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
        if not cursor.fetchone():
            return jsonify({'error': f'Person {person_id} not found'}), 404
        
        # Sử dụng stored procedure mới
        cursor.callproc('sp_get_ancestors', [person_id, max_level])
        
        # Lấy kết quả từ stored procedure
        ancestors_result = None
        for result_set in cursor.stored_results():
            ancestors_result = result_set.fetchall()
            break
        
        ancestors_chain = []
        if ancestors_result:
            for row in ancestors_result:
                if isinstance(row, dict):
                    ancestors_chain.append({
                        'person_id': row.get('person_id'),
                        'full_name': row.get('full_name', ''),
                        'gender': row.get('gender'),
                        'generation_level': row.get('generation_level'),
                        'level': row.get('level', 0)
                    })
                else:
                    ancestors_chain.append({
                        'person_id': row[0] if len(row) > 0 else None,
                        'full_name': row[1] if len(row) > 1 else '',
                        'gender': row[2] if len(row) > 2 else None,
                        'generation_level': row[3] if len(row) > 3 else None,
                        'level': row[4] if len(row) > 4 else 0
                    })
        
        # Lấy thông tin person hiện tại
        cursor.execute("""
            SELECT person_id, full_name, alias, gender, generation_level, status
            FROM persons
            WHERE person_id = %s
        """, (person_id,))
        person_info = cursor.fetchone()
        
        logger.info(f"Built ancestors chain for person_id={person_id}, length={len(ancestors_chain)}")
        return jsonify({
            "person": person_info,
            "ancestors_chain": ancestors_chain
        })
        
    except Error as e:
        logger.error(f"Error in /api/ancestors/{person_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/descendants/<person_id>', methods=['GET'])
def get_descendants(person_id):
    """Get descendants of a person (schema mới - dùng stored procedure)"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        max_level = int(request.args.get('max_level', 5))
    except (ValueError, TypeError):
        max_level = 5
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Validate person_id exists
        cursor.execute("SELECT person_id FROM persons WHERE person_id = %s", (person_id,))
        if not cursor.fetchone():
            return jsonify({'error': f'Person {person_id} not found'}), 404
        
        # Sử dụng stored procedure mới
        cursor.callproc('sp_get_descendants', [person_id, max_level])
        
        # Lấy kết quả từ stored procedure
        descendants_result = None
        for result_set in cursor.stored_results():
            descendants_result = result_set.fetchall()
            break
        
        descendants = []
        if descendants_result:
            for row in descendants_result:
                if isinstance(row, dict):
                    descendants.append({
                        'person_id': row.get('person_id'),
                        'full_name': row.get('full_name', ''),
                        'gender': row.get('gender'),
                        'generation_level': row.get('generation_level'),
                        'level': row.get('level', 0)
                    })
                else:
                    descendants.append({
                        'person_id': row[0] if len(row) > 0 else None,
                        'full_name': row[1] if len(row) > 1 else '',
                        'gender': row[2] if len(row) > 2 else None,
                        'generation_level': row[3] if len(row) > 3 else None,
                        'level': row[4] if len(row) > 4 else 0
                    })
        
        logger.info(f"Built descendants for person_id={person_id}, count={len(descendants)}")
        return jsonify({
            "person_id": person_id,
            "descendants": descendants
        })
        
    except Error as e:
        logger.error(f"Error in /api/descendants/{person_id}: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/search', methods=['GET'])
def search_persons():
    """Search persons by name, alias, generation_level, or person_id (schema mới)"""
    q = request.args.get('q', '').strip() or request.args.get('query', '').strip()
    if not q:
        return jsonify([])
    
    try:
        generation_level = int(request.args.get('generation')) if request.args.get('generation') else None
    except (ValueError, TypeError):
        generation_level = None
    
    try:
        limit = int(request.args.get('limit', 50))
        limit = min(limit, 200)  # Max 200
    except (ValueError, TypeError):
        limit = 50
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        search_pattern = f"%{q}%"
        
        # Schema mới: search theo full_name, alias, generation_level, person_id
        if generation_level:
            cursor.execute("""
                SELECT
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.status,
                    p.generation_level,
                    p.home_town,
                    p.gender,
                    p.father_mother_id,
                    -- Cha từ relationships
                    (SELECT parent.full_name 
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'father' 
                     LIMIT 1) AS father_name,
                    -- Mẹ từ relationships
                    (SELECT parent.full_name 
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'mother' 
                     LIMIT 1) AS mother_name
                FROM persons p
                WHERE (p.full_name LIKE %s 
                       OR p.alias LIKE %s 
                       OR p.person_id LIKE %s)
                  AND p.generation_level = %s
                ORDER BY p.generation_level, p.full_name
                LIMIT %s
            """, (search_pattern, search_pattern, search_pattern, generation_level, limit))
        else:
            cursor.execute("""
                SELECT
                    p.person_id,
                    p.full_name,
                    p.alias,
                    p.status,
                    p.generation_level,
                    p.home_town,
                    p.gender,
                    p.father_mother_id,
                    -- Cha từ relationships
                    (SELECT parent.full_name 
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'father' 
                     LIMIT 1) AS father_name,
                    -- Mẹ từ relationships
                    (SELECT parent.full_name 
                     FROM relationships r 
                     JOIN persons parent ON r.parent_id = parent.person_id 
                     WHERE r.child_id = p.person_id AND r.relation_type = 'mother' 
                     LIMIT 1) AS mother_name
                FROM persons p
                WHERE (p.full_name LIKE %s 
                       OR p.alias LIKE %s 
                       OR p.person_id LIKE %s)
                ORDER BY p.generation_level, p.full_name
                LIMIT %s
            """, (search_pattern, search_pattern, search_pattern, limit))
        
        results = cursor.fetchall()
        
        # Remove duplicates by person_id (LEFT JOIN với relationships có thể tạo duplicate nếu có nhiều relationships)
        seen_ids = set()
        unique_results = []
        for row in results:
            person_id = row.get('person_id')
            if person_id and person_id not in seen_ids:
                seen_ids.add(person_id)
                unique_results.append(row)
            elif person_id in seen_ids:
                # Log duplicate for debugging
                logger.debug(f"Duplicate person_id={person_id} in search results for query='{q}'")
        
        logger.info(f"Search query='{q}', generation_level={generation_level}, found={len(results)} rows, {len(unique_results)} unique persons")
        return jsonify(unique_results)
        
    except Error as e:
        logger.error(f"Error in /api/search: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection and connection.is_connected():
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
        # 5. HÔN PHỐI (marriages_spouses deprecated)
        # =====================================================
        # TODO: derive and upsert spouse info using normalized `marriages` table
        
        # =====================================================
        # 6. COMMIT TẤT CẢ THAY ĐỔI
        # =====================================================
        connection.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Đã cập nhật và đồng bộ dữ liệu thành công!',
            'updated_fields': list(updates.keys()) + ['birth_records', 'death_records', 'relationships', 'marriages (todo: use normalized table)']
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
        
        # 3. Hôn phối: marriages_spouses deprecated
        # TODO: fetch active spouses from normalized `marriages` table
        active_spouses = []
        
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
    logger.info("📥 API /api/members được gọi")
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        if not connection:
            logger.error("❌ Không thể kết nối database trong get_members()")
            return jsonify({'success': False, 'error': 'Không thể kết nối database'}), 500
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
            
            # Hôn phối: marriages_spouses deprecated
            # TODO: derive spouse info from normalized `marriages` table
            spouses = []
            
            # Lấy anh/chị/em từ relationships (những người có cùng cha mẹ)
            # Get parent info first
            cursor.execute("""
                SELECT father_id, mother_id
                FROM relationships
                WHERE child_id = %s
                LIMIT 1
            """, (person_id,))
            parent_rel = cursor.fetchone()
            
            siblings = []
            if parent_rel and (parent_rel.get('father_id') or parent_rel.get('mother_id')):
                father_id = parent_rel.get('father_id')
                mother_id = parent_rel.get('mother_id')
                cursor.execute("""
                    SELECT DISTINCT s.full_name AS sibling_name
                    FROM persons s
                    JOIN relationships r_sibling ON s.person_id = r_sibling.child_id
                    WHERE s.person_id != %s
                    AND (
                        (%s IS NOT NULL AND r_sibling.father_id = %s)
                        OR (%s IS NOT NULL AND r_sibling.mother_id = %s)
                    )
                    ORDER BY s.full_name
                """, (person_id, father_id, father_id, mother_id, mother_id))
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
                'father_name': rel.get('father_name') if rel else None,
                'mother_name': rel.get('mother_name') if rel else None,
                'spouses': '; '.join([s.get('spouse_name', '') for s in spouses]) if spouses else None,
                'siblings': '; '.join([s.get('sibling_name', '') for s in siblings]) if siblings else None,
                'children': '; '.join([c.get('full_name', '') for c in children]) if children else None
            }
            
            members.append(member)
        
        logger.info(f"✅ API /api/members trả về {len(members)} thành viên")
        return jsonify({'success': True, 'data': members})
        
    except Error as e:
        logger.error(f"❌ Lỗi trong /api/members: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Lỗi: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"❌ Lỗi không mong đợi trong /api/members: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Lỗi không mong đợi: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            if cursor:
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
                    print(f"WARNING: Loi doc file config: {config_error}")
            
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
                    
                    print(f"OK: Email da duoc gui thanh cong den {smtp_to}")
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được gửi thành công đến email baophongcmu@gmail.com. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
                except Exception as email_error:
                    print(f"WARNING: Loi khi gui email qua SMTP: {email_error}")
                    import traceback
                    traceback.print_exc()
                    # Vẫn trả về success nhưng log lỗi
                    return jsonify({
                        'success': True, 
                        'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
                    })
            else:
                print("WARNING: SMTP chua duoc cau hinh.")
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
            print(f"WARNING: Loi khi xu ly email: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': True, 
                'message': 'Yêu cầu đã được ghi nhận. Chúng tôi sẽ xem xét và phản hồi sớm nhất có thể.'
            })
            
    except Exception as e:
        print(f"ERROR: Loi khi xu ly yeu cau: {e}")
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
        'stats': {
            'persons_count': 0,
            'relationships_count': 0
        }
    }
    
    # Test database connection and get stats
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_status['database'] = 'connected'
            
            # Get stats
            try:
                cursor.execute("SELECT COUNT(*) as count FROM persons")
                result = cursor.fetchone()
                health_status['stats']['persons_count'] = result['count'] if result else 0
                
                cursor.execute("SELECT COUNT(*) as count FROM relationships")
                result = cursor.fetchone()
                health_status['stats']['relationships_count'] = result['count'] if result else 0
            except Exception as e:
                logger.warning(f"Error getting stats: {e}")
            
            cursor.close()
            connection.close()
        except Exception as e:
            health_status['database'] = f'error: {str(e)}'
            logger.error(f"Database health check error: {e}")
    else:
        health_status['database'] = 'connection_failed'
    
    return jsonify(health_status)

# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    # For non-API routes, try to render index.html (SPA fallback)
    try:
        return render_template('index.html')
    except:
        return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return jsonify({'error': 'Internal server error'}), 500

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
        print(f"ERROR: Loi khi lay thong ke thanh vien: {e}")
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


# -----------------------------------------------------------------------------
# Lightweight smoke tests (manual run)
# -----------------------------------------------------------------------------
def run_smoke_tests():
    """Basic smoke tests for key endpoints using Flask test client."""
    with app.test_client() as client:
        resp = client.get("/api/health")
        assert resp.status_code == 200

        resp = client.get("/api/persons")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

        persons = resp.get_json()
        if persons:
            pid = persons[0].get("person_id")
            if pid:
                detail = client.get(f"/api/person/{pid}")
                assert detail.status_code == 200


# Print startup info (chạy mỗi khi import, không chỉ khi __main__)
print("="*80)
print("FLASK APP DANG KHOI DONG...")
print("="*80)
print(f"Working directory: {os.getcwd()}")
print(f"Base directory: {BASE_DIR}")
print(f"__file__: {__file__}")
print("="*80)

if __name__ == '__main__':
    print("\nServer se chay tai:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Thành viên: http://localhost:5000/members")
    print("   - Admin: http://localhost:5000/admin/login")
    print("\nNhan Ctrl+C de dung server")
    print("="*80 + "\n")
    try:
        port = int(os.environ.get('PORT', 5000))
        print(f"Starting server on port {port}...")
        app.run(debug=False, port=port, host='0.0.0.0')
    except Exception as e:
        print(f"\nERROR: LOI KHI KHOI DONG SERVER: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
