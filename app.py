#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask API Server cho Gia Phả Nguyễn Phước Tộc
Kết nối HTML với MySQL database
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)  # Cho phép frontend gọi API

# Cấu hình database
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gia_pha_nguyen_phuoc_toc',
    'user': 'admin',
    'password': 'admin',
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
    """Trang chủ - trả về file HTML"""
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
        cursor.execute("""
            SELECT 
                p.person_id,
                p.full_name,
                p.common_name,
                p.gender,
                g.generation_number,
                b.branch_name,
                p.status,
                father.full_name AS father_name,
                mother.full_name AS mother_name
            FROM persons p
            LEFT JOIN generations g ON p.generation_id = g.generation_id
            LEFT JOIN branches b ON p.branch_id = b.branch_id
            LEFT JOIN relationships r ON p.person_id = r.child_id
            LEFT JOIN persons father ON r.father_id = father.person_id
            LEFT JOIN persons mother ON r.mother_id = mother.person_id
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

if __name__ == '__main__':
    print("Đang khởi động server...")
    print("Mở trình duyệt: http://localhost:5000")
    app.run(debug=True, port=5000)

