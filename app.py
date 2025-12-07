#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_login import login_required, current_user
import mysql.connector
from mysql.connector import Error
import os
import secrets
import csv
import csv

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)  # Cho phép frontend gọi API

# Import và khởi tạo authentication
from auth import init_login_manager
login_manager = init_login_manager(app)

# Import và đăng ký admin routes
from admin_routes import register_admin_routes
register_admin_routes(app)

# Import và đăng ký marriage routes
from marriage_api import register_marriage_routes
register_marriage_routes(app)

# Cấu hình database
DB_CONFIG = {
    'host': 'localhost',
    'database': 'tbqc2025',
    'user': 'tbqc_admin',
    'password': 'tbqc2025',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_db_connection():
    """Tạo kết nối database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Lỗi kết nối database: {e}")
        return None

@app.route('/')
def index():
    """Trang chủ - trả về file HTML chính"""
    return send_from_directory('.', 'index.html')

@app.route('/gia-pha')
def genealogy_old():
    """Trang gia phả cũ (backup)"""
    return send_from_directory('.', 'gia-pha-nguyen-phuoc-toc.html')

@app.route('/family-tree-core.js')
def serve_core_js():
    """Serve file JavaScript core"""
    return send_from_directory('.', 'family-tree-core.js', mimetype='application/javascript')

@app.route('/family-tree-ui.js')
def serve_ui_js():
    """Serve file JavaScript UI"""
    return send_from_directory('.', 'family-tree-ui.js', mimetype='application/javascript')

@app.route('/genealogy-lineage.js')
def serve_genealogy_js():
    """Serve file JavaScript genealogy lineage"""
    return send_from_directory('.', 'genealogy-lineage.js', mimetype='application/javascript')

@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve các file ảnh từ folder images"""
    return send_from_directory('images', filename)

@app.route('/test_genealogy_lineage.html')
def serve_test_page():
    """Serve trang test genealogy lineage"""
    return send_from_directory('.', 'test_genealogy_lineage.html')

@app.route('/api/persons')
def get_persons():
    """Lấy danh sách tất cả người (bao gồm tên cha mẹ)"""
    connection = get_db_connection()
    if not connection:
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
                r.father_id,
                MAX(father.full_name) AS father_name,
                r.mother_id,
                MAX(mother.full_name) AS mother_name,
                GROUP_CONCAT(DISTINCT CONCAT(sibling.full_name, ' (', sr.relation_type, ')') SEPARATOR '; ') AS siblings,
                GROUP_CONCAT(DISTINCT ms.spouse_name SEPARATOR '; ') AS spouse,
                GROUP_CONCAT(DISTINCT child.full_name SEPARATOR '; ') AS children
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN branches b ON p.branch_id = b.branch_id
            LEFT JOIN relationships r ON p.person_id = r.child_id
            LEFT JOIN persons father ON r.father_id = father.person_id
            LEFT JOIN persons mother ON r.mother_id = mother.person_id
            LEFT JOIN sibling_relationships sr ON p.person_id = sr.person_id
            LEFT JOIN persons sibling ON sr.sibling_person_id = sibling.person_id
            LEFT JOIN marriages_spouses ms ON p.person_id = ms.person_id AND ms.is_active = TRUE
            LEFT JOIN relationships r_children ON (p.person_id = r_children.father_id OR p.person_id = r_children.mother_id)
            LEFT JOIN persons child ON r_children.child_id = child.person_id
            GROUP BY p.person_id, p.csv_id, p.full_name, p.common_name, p.gender, g.generation_number, b.branch_name, p.status, r.father_id, r.mother_id
            ORDER BY g.generation_number, p.full_name
        """)
        persons = cursor.fetchall()
        return jsonify(persons)
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_sheet3_data_by_name(person_name):
    """Đọc dữ liệu từ Sheet3 CSV theo tên người"""
    sheet3_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Data_TBQC_Sheet3.csv')
    
    if not os.path.exists(sheet3_file):
        return None
    
    try:
        with open(sheet3_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # So sánh tên (không phân biệt hoa thường, loại bỏ khoảng trắng thừa)
                sheet3_name = (row.get('Họ và tên', '') or '').strip()
                person_name_clean = (person_name or '').strip()
                
                if sheet3_name.lower() == person_name_clean.lower():
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
        cursor.execute("SELECT * FROM v_person_full_info WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        
        # Lấy thông tin từ personal_details
        if person:
            cursor.execute("""
                SELECT siblings, spouse, children 
                FROM personal_details 
                WHERE person_id = %s
            """, (person_id,))
            details = cursor.fetchone()
            if details:
                person['siblings'] = details.get('siblings')
                person['spouse'] = details.get('spouse')
                person['children'] = details.get('children')
            
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
            
            # Lấy dữ liệu từ Sheet3 CSV
            person_name = person.get('full_name', '')
            if person_name:
                sheet3_data = get_sheet3_data_by_name(person_name)
                if sheet3_data:
                    # Ưu tiên dữ liệu từ Sheet3 cho các trường: siblings, spouse, children
                    # Nếu Sheet3 có dữ liệu thì dùng, nếu không thì dùng từ database
                    if sheet3_data.get('sheet3_siblings'):
                        person['siblings'] = sheet3_data['sheet3_siblings']
                    if sheet3_data.get('sheet3_spouse'):
                        person['spouse'] = sheet3_data['sheet3_spouse']
                    if sheet3_data.get('sheet3_children'):
                        person['children'] = sheet3_data['sheet3_children']
                    
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
            'authenticated': False,
            'id': None,
            'username': None,
            'role': None,
            'permissions': {},
            'hasPermission': lambda perm: False
        })
    
    # Tạo object có method hasPermission
    user_data = {
        'authenticated': True,
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role,
        'full_name': getattr(current_user, 'full_name', ''),
        'permissions': current_user.get_permissions() if hasattr(current_user, 'get_permissions') else {}
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

@app.route('/api/person/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    """Cập nhật thông tin một người"""
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Không thể kết nối database'}), 500
    
    try:
        data = request.get_json()
        cursor = connection.cursor(dictionary=True)
        
        # Cập nhật personal_details nếu có
        if any(key in data for key in ['siblings', 'spouse', 'children']):
            cursor.execute("SELECT detail_id FROM personal_details WHERE person_id = %s", (person_id,))
            detail_exists = cursor.fetchone()
            
            if detail_exists:
                updates = []
                params = []
                if 'siblings' in data:
                    updates.append("siblings = %s")
                    params.append(data.get('siblings'))
                if 'spouse' in data:
                    updates.append("spouse = %s")
                    params.append(data.get('spouse'))
                if 'children' in data:
                    updates.append("children = %s")
                    params.append(data.get('children'))
                
                if updates:
                    params.append(person_id)
                    cursor.execute(f"""
                        UPDATE personal_details 
                        SET {', '.join(updates)}
                        WHERE person_id = %s
                    """, params)
            else:
                cursor.execute("""
                    INSERT INTO personal_details (person_id, siblings, spouse, children)
                    VALUES (%s, %s, %s, %s)
                """, (person_id, data.get('siblings'), data.get('spouse'), data.get('children')))
        
        connection.commit()
        return jsonify({'success': True, 'message': 'Đã cập nhật thành công'})
    except Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    print("Đang khởi động server...")
    print("Mở trình duyệt: http://localhost:5000")
    print("Trang admin: http://localhost:5000/admin/login")
    print("Tạo admin đầu tiên: python create_admin.py")
    app.run(debug=True, port=5000)

