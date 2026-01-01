#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để bổ sung thông tin hôn phối và tổ tiên cho:
- Vua Minh Mạng
- Kỳ Ngoại Hầu Hường Phiêu  
- Hường Chiêm
- Vua Gia Long (bố của Vua Minh Mạng)
- Thuận Thiên Cao Hoàng Hậu (mẹ của Vua Minh Mạng)
"""

import sys
import os

# Add folder_py to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

from folder_py.db_config import get_db_connection
import mysql.connector
from mysql.connector import Error

def find_person_by_name(cursor, name_pattern):
    """Tìm person theo tên (LIKE pattern)"""
    cursor.execute("""
        SELECT person_id, full_name, gender, generation_level
        FROM persons
        WHERE full_name LIKE %s
        LIMIT 5
    """, (f'%{name_pattern}%',))
    results = cursor.fetchall()
    return results

def find_or_create_person(cursor, person_id, full_name, gender, generation_level=None):
    """Tìm hoặc tạo person"""
    cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = %s", (person_id,))
    person = cursor.fetchone()
    
    if person:
        return person['person_id']
    
    # Tạo person mới
    if generation_level is None:
        generation_level = 0  # Sẽ cần điều chỉnh
    
    cursor.execute("""
        INSERT INTO persons (person_id, full_name, gender, generation_level)
        VALUES (%s, %s, %s, %s)
    """, (person_id, full_name, gender, generation_level))
    
    return person_id

def add_marriage(cursor, person_id, spouse_name, spouse_gender=None, spouse_id=None):
    """Thêm hôn phối vào bảng marriages"""
    # Nếu có spouse_id, dùng luôn
    if spouse_id:
        spouse_person_id = spouse_id
    else:
        # Tìm spouse theo tên
        cursor.execute("""
            SELECT person_id FROM persons 
            WHERE full_name LIKE %s
            LIMIT 1
        """, (f'%{spouse_name}%',))
        spouse = cursor.fetchone()
        if not spouse:
            print(f"⚠️  Không tìm thấy spouse: {spouse_name}")
            return False
        spouse_person_id = spouse['person_id']
    
    # Kiểm tra marriage đã tồn tại chưa
    cursor.execute("""
        SELECT * FROM marriages 
        WHERE (person_id = %s AND spouse_person_id = %s)
           OR (person_id = %s AND spouse_person_id = %s)
        LIMIT 1
    """, (person_id, spouse_person_id, spouse_person_id, person_id))
    
    if cursor.fetchone():
        print(f"✅ Marriage đã tồn tại: {person_id} <-> {spouse_person_id}")
        return True
    
    # Thêm marriage
    cursor.execute("""
        INSERT INTO marriages (person_id, spouse_person_id)
        VALUES (%s, %s)
    """, (person_id, spouse_person_id))
    
    print(f"✅ Đã thêm marriage: {person_id} <-> {spouse_person_id} ({spouse_name})")
    return True

def add_relationship(cursor, child_id, parent_id, relation_type):
    """Thêm relationship (father/mother)"""
    # Kiểm tra đã tồn tại chưa
    cursor.execute("""
        SELECT * FROM relationships
        WHERE child_id = %s AND parent_id = %s AND relation_type = %s
        LIMIT 1
    """, (child_id, parent_id, relation_type))
    
    if cursor.fetchone():
        print(f"✅ Relationship đã tồn tại: {child_id} -{relation_type}-> {parent_id}")
        return True
    
    # Thêm relationship
    cursor.execute("""
        INSERT INTO relationships (child_id, parent_id, relation_type)
        VALUES (%s, %s, %s)
    """, (child_id, parent_id, relation_type))
    
    print(f"✅ Đã thêm relationship: {child_id} -{relation_type}-> {parent_id}")
    return True

def main():
    """Main function"""
    print("=" * 80)
    print("BỔ SUNG THÔNG TIN GIA PHẢ")
    print("=" * 80)
    
    connection = get_db_connection()
    if not connection:
        print("❌ Không thể kết nối database")
        sys.exit(1)
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 1. Tìm các person cần thiết
        print("\n🔍 Tìm kiếm các person...")
        
        vua_minh_mang = None
        huong_phieu = None
        huong_chiem = None
        vua_gia_long = None
        thuan_thien = None
        
        # Tìm Vua Minh Mạng
        results = find_person_by_name(cursor, "Minh Mạng")
        if results:
            for r in results:
                if "Minh Mạng" in r['full_name']:
                    vua_minh_mang = r
                    break
        if not vua_minh_mang:
            # Thử tìm P-1-1
            cursor.execute("SELECT person_id, full_name, gender, generation_level FROM persons WHERE person_id = 'P-1-1'")
            vua_minh_mang = cursor.fetchone()
        
        # Tìm Kỳ Ngoại Hầu Hường Phiêu
        results = find_person_by_name(cursor, "Hường Phiêu")
        if results:
            huong_phieu = results[0]
        
        # Tìm Hường Chiêm
        results = find_person_by_name(cursor, "Hường Chiêm")
        if results:
            huong_chiem = results[0]
        
        # Tìm Vua Gia Long
        results = find_person_by_name(cursor, "Gia Long")
        if results:
            for r in results:
                if "Gia Long" in r['full_name']:
                    vua_gia_long = r
                    break
        
        # Tìm Thuận Thiên Cao Hoàng Hậu
        results = find_person_by_name(cursor, "Thuận Thiên")
        if results:
            for r in results:
                if "Thuận Thiên" in r['full_name']:
                    thuan_thien = r
                    break
        
        # In kết quả tìm kiếm
        print(f"\n📋 Kết quả tìm kiếm:")
        if vua_minh_mang:
            print(f"  ✅ Vua Minh Mạng: {vua_minh_mang['person_id']} - {vua_minh_mang['full_name']}")
        else:
            print(f"  ❌ Không tìm thấy Vua Minh Mạng")
        
        if huong_phieu:
            print(f"  ✅ Kỳ Ngoại Hầu Hường Phiêu: {huong_phieu['person_id']} - {huong_phieu['full_name']}")
        else:
            print(f"  ❌ Không tìm thấy Kỳ Ngoại Hầu Hường Phiêu")
        
        if huong_chiem:
            print(f"  ✅ Hường Chiêm: {huong_chiem['person_id']} - {huong_chiem['full_name']}")
        else:
            print(f"  ❌ Không tìm thấy Hường Chiêm")
        
        if vua_gia_long:
            print(f"  ✅ Vua Gia Long: {vua_gia_long['person_id']} - {vua_gia_long['full_name']}")
        else:
            print(f"  ❌ Không tìm thấy Vua Gia Long")
        
        if thuan_thien:
            print(f"  ✅ Thuận Thiên Cao Hoàng Hậu: {thuan_thien['person_id']} - {thuan_thien['full_name']}")
        else:
            print(f"  ❌ Không tìm thấy Thuận Thiên Cao Hoàng Hậu")
        
        # 2. Bổ sung hôn phối
        print("\n💑 Bổ sung hôn phối...")
        
        # Vua Minh Mạng - Tiệp dư Nguyễn Thị Viên
        if vua_minh_mang:
            spouse_name = "Tiệp dư Nguyễn Thị Viên"
            results = find_person_by_name(cursor, "Tiệp dư Nguyễn Thị Viên")
            if results:
                add_marriage(cursor, vua_minh_mang['person_id'], spouse_name, 'Nữ', results[0]['person_id'])
            else:
                print(f"⚠️  Không tìm thấy {spouse_name}, bỏ qua")
        
        # Kỳ Ngoại Hầu Hường Phiêu - cần tìm spouse
        if huong_phieu:
            # Tìm spouse của Hường Phiêu (cần biết tên)
            print(f"⚠️  Cần thông tin về hôn phối của {huong_phieu['full_name']}")
        
        # Hường Chiêm - cần tìm spouse
        if huong_chiem:
            # Tìm spouse của Hường Chiêm (cần biết tên)
            print(f"⚠️  Cần thông tin về hôn phối của {huong_chiem['full_name']}")
        
        # 3. Bổ sung tổ tiên cho Vua Minh Mạng
        print("\n👨‍👩‍👦 Bổ sung tổ tiên cho Vua Minh Mạng...")
        
        if vua_minh_mang:
            if vua_gia_long:
                add_relationship(cursor, vua_minh_mang['person_id'], vua_gia_long['person_id'], 'father')
            else:
                print("⚠️  Không tìm thấy Vua Gia Long, không thể thêm relationship father")
            
            if thuan_thien:
                add_relationship(cursor, vua_minh_mang['person_id'], thuan_thien['person_id'], 'mother')
            else:
                print("⚠️  Không tìm thấy Thuận Thiên Cao Hoàng Hậu, không thể thêm relationship mother")
        else:
            print("⚠️  Không tìm thấy Vua Minh Mạng, không thể thêm relationships")
        
        # Commit changes
        connection.commit()
        print("\n✅ Hoàn thành!")
        
    except Error as e:
        print(f"\n❌ Lỗi database: {e}")
        connection.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        connection.rollback()
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    main()

