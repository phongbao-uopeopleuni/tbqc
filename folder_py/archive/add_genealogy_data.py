#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to add genealogy data: marriages and parent relationships
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'folder_py'))

from folder_py.db_config import get_db_connection

def main():
    conn = get_db_connection()
    if not conn:
        print("Cannot connect to database")
        return
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Find persons
        persons = {}
        queries = [
            ("P-1-1", "Minh Mang"),
            ("", "Huong Phieu"),
            ("", "Huong Chiem"),
            ("", "Gia Long"),
            ("", "Thuan Thien")
        ]
        
        for person_id, name_pattern in queries:
            if person_id:
                cursor.execute("SELECT person_id, full_name FROM persons WHERE person_id = %s", (person_id,))
            else:
                cursor.execute("SELECT person_id, full_name FROM persons WHERE full_name LIKE %s LIMIT 1", (f'%{name_pattern}%',))
            result = cursor.fetchone()
            if result:
                key = name_pattern.lower().replace(' ', '_')
                persons[key] = result
                print(f"Found: {result['person_id']} - {result['full_name']}")
        
        # Add marriages
        if 'minh_mang' in persons:
            # Find Tep du Nguyen Thi Vien
            cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1", ('%Tiep du Nguyen Thi Vien%',))
            spouse = cursor.fetchone()
            if not spouse:
                cursor.execute("SELECT person_id FROM persons WHERE full_name LIKE %s LIMIT 1", ('%Nguyen Thi Vien%',))
                spouse = cursor.fetchone()
            
            if spouse and 'minh_mang' in persons:
                # Check if marriage exists
                cursor.execute("""
                    SELECT * FROM marriages 
                    WHERE (person_id = %s AND spouse_person_id = %s)
                       OR (person_id = %s AND spouse_person_id = %s)
                """, (persons['minh_mang']['person_id'], spouse['person_id'], 
                      spouse['person_id'], persons['minh_mang']['person_id']))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO marriages (person_id, spouse_person_id) VALUES (%s, %s)",
                                 (persons['minh_mang']['person_id'], spouse['person_id']))
                    print(f"Added marriage: {persons['minh_mang']['person_id']} <-> {spouse['person_id']}")
        
        # Add parent relationships for Minh Mang
        if 'minh_mang' in persons and 'gia_long' in persons:
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE child_id = %s AND parent_id = %s AND relation_type = 'father'
            """, (persons['minh_mang']['person_id'], persons['gia_long']['person_id']))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES (%s, %s, 'father')
                """, (persons['minh_mang']['person_id'], persons['gia_long']['person_id']))
                print(f"Added father relationship")
        
        if 'minh_mang' in persons and 'thuan_thien' in persons:
            cursor.execute("""
                SELECT * FROM relationships 
                WHERE child_id = %s AND parent_id = %s AND relation_type = 'mother'
            """, (persons['minh_mang']['person_id'], persons['thuan_thien']['person_id']))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO relationships (child_id, parent_id, relation_type)
                    VALUES (%s, %s, 'mother')
                """, (persons['minh_mang']['person_id'], persons['thuan_thien']['person_id']))
                print(f"Added mother relationship")
        
        conn.commit()
        print("Done!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()

