#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để kiểm tra dữ liệu của P-7-654 trong database và so sánh với API response
"""

import sys
import os
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(__file__))

try:
    from folder_py.db_config import get_db_connection
except ImportError:
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))
        from db_config import get_db_connection
    except ImportError:
        print("ERROR: Cannot import db_config")
        sys.exit(1)

def check_database():
    """Kiểm tra dữ liệu trong database"""
    print("=" * 60)
    print("KIỂM TRA DATABASE CHO P-7-654")
    print("=" * 60)
    
    connection = get_db_connection()
    if not connection:
        print("❌ Không thể kết nối database")
        return
    
    cursor = connection.cursor(dictionary=True)
    person_id = "P-7-654"
    
    try:
        # 1. Kiểm tra person cơ bản
        print(f"\n1. Thông tin cơ bản của {person_id}:")
        cursor.execute("SELECT person_id, full_name, gender, generation_level FROM persons WHERE person_id = %s", (person_id,))
        person = cursor.fetchone()
        if person:
            print(f"   ✅ Tìm thấy: {person['full_name']} (Đời {person.get('generation_level')})")
        else:
            print(f"   ❌ Không tìm thấy {person_id}")
            return
        
        # 2. Kiểm tra spouse từ spouse_sibling_children table
        print(f"\n2. Spouse từ spouse_sibling_children table:")
        try:
            cursor.execute("SELECT spouse_name FROM spouse_sibling_children WHERE person_id = %s", (person_id,))
            ssc_row = cursor.fetchone()
            if ssc_row and ssc_row.get('spouse_name'):
                print(f"   ✅ Tìm thấy: {ssc_row['spouse_name']}")
            else:
                print(f"   ⚠️  Không có dữ liệu")
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
        
        # 3. Kiểm tra spouse từ marriages table
        print(f"\n3. Spouse từ marriages table:")
        try:
            cursor.execute("""
                SELECT 
                    m.id AS marriage_id,
                    CASE 
                        WHEN m.person_id = %s THEN m.spouse_person_id
                        ELSE m.person_id
                    END AS spouse_id,
                    sp.full_name AS spouse_name
                FROM marriages m
                LEFT JOIN persons sp ON (
                    CASE 
                        WHEN m.person_id = %s THEN sp.person_id = m.spouse_person_id
                        ELSE sp.person_id = m.person_id
                    END
                )
                WHERE (m.person_id = %s OR m.spouse_person_id = %s)
            """, (person_id, person_id, person_id, person_id))
            marriages = cursor.fetchall()
            if marriages:
                for m in marriages:
                    print(f"   ✅ Tìm thấy: {m.get('spouse_name')} (spouse_id: {m.get('spouse_id')})")
            else:
                print(f"   ⚠️  Không có dữ liệu")
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
        
        # 4. Kiểm tra children từ relationships table
        print(f"\n4. Children từ relationships table:")
        try:
            cursor.execute("""
                SELECT 
                    r.child_id,
                    child.full_name AS child_name,
                    child.generation_level,
                    r.relation_type
                FROM relationships r
                JOIN persons child ON r.child_id = child.person_id
                WHERE r.parent_id = %s AND r.relation_type IN ('father', 'mother')
                ORDER BY child.full_name
            """, (person_id,))
            children = cursor.fetchall()
            if children:
                print(f"   ✅ Tìm thấy {len(children)} con:")
                for c in children:
                    print(f"      - {c['child_name']} ({c['child_id']}, Đời {c.get('generation_level')})")
            else:
                print(f"   ⚠️  Không có dữ liệu")
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
        
        # 5. Kiểm tra siblings từ relationships table
        print(f"\n5. Siblings từ relationships table:")
        try:
            # Lấy parent_id của person này
            cursor.execute("""
                SELECT DISTINCT r.parent_id, r.relation_type
                FROM relationships r
                WHERE r.child_id = %s AND r.relation_type IN ('father', 'mother')
            """, (person_id,))
            parents = cursor.fetchall()
            
            if parents:
                parent_ids = [p['parent_id'] for p in parents]
                print(f"   Parents: {parent_ids}")
                
                # Tìm siblings (cùng parent)
                placeholders = ','.join(['%s'] * len(parent_ids))
                cursor.execute(f"""
                    SELECT DISTINCT
                        s.person_id,
                        s.full_name AS sibling_name
                    FROM persons s
                    JOIN relationships r ON s.person_id = r.child_id
                    WHERE r.parent_id IN ({placeholders})
                      AND s.person_id != %s
                    ORDER BY s.full_name
                """, parent_ids + [person_id])
                siblings = cursor.fetchall()
                
                if siblings:
                    print(f"   ✅ Tìm thấy {len(siblings)} anh/chị/em:")
                    for s in siblings:
                        print(f"      - {s['sibling_name']} ({s['person_id']})")
                else:
                    print(f"   ⚠️  Không có siblings")
            else:
                print(f"   ⚠️  Không có parent, không thể tìm siblings")
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
        
        # 6. Kiểm tra CSV file
        print(f"\n6. Spouse từ CSV file:")
        try:
            import csv
            csv_file = 'spouse_sibling_children.csv'
            if os.path.exists(csv_file):
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('person_id', '').strip() == person_id:
                            spouse_name = row.get('spouse_name', '').strip()
                            if spouse_name:
                                print(f"   ✅ Tìm thấy trong CSV: {spouse_name}")
                                break
                    else:
                        print(f"   ⚠️  Không tìm thấy trong CSV")
            else:
                print(f"   ⚠️  CSV file không tồn tại")
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
        
        # 7. Test load_relationship_data helper
        print(f"\n7. Test load_relationship_data helper:")
        try:
            # Import helper function
            sys.path.insert(0, os.path.dirname(__file__))
            from app import load_relationship_data
            
            relationship_data = load_relationship_data(cursor)
            
            spouse_data_from_table = relationship_data['spouse_data_from_table']
            spouse_data_from_marriages = relationship_data['spouse_data_from_marriages']
            spouse_data_from_csv = relationship_data['spouse_data_from_csv']
            children_map = relationship_data['children_map']
            siblings_map = relationship_data['siblings_map']
            
            print(f"   Spouse từ table: {spouse_data_from_table.get(person_id, 'Không có')}")
            print(f"   Spouse từ marriages: {spouse_data_from_marriages.get(person_id, 'Không có')}")
            print(f"   Spouse từ CSV: {spouse_data_from_csv.get(person_id, 'Không có')}")
            print(f"   Children: {children_map.get(person_id, 'Không có')}")
            print(f"   Siblings: {siblings_map.get(person_id, 'Không có')}")
            
        except Exception as e:
            print(f"   ⚠️  Lỗi: {e}")
            import traceback
            traceback.print_exc()
        
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    check_database()

