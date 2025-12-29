#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API /api/person/P-7-654 để xem response có đầy đủ không
"""

import requests
import json
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def test_api_person():
    """Test API /api/person/P-7-654"""
    print("=" * 60)
    print("TEST API /api/person/P-7-654")
    print("=" * 60)
    
    person_id = "P-7-654"
    
    try:
        print(f"\n1. Gọi API: GET {BASE_URL}/api/person/{person_id}")
        response = requests.get(f"{BASE_URL}/api/person/{person_id}")
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Kiểm tra structure
            person = data.get('person') or data
            
            print(f"\n2. Response Structure:")
            print(f"   - person_id: {person.get('person_id')}")
            print(f"   - full_name: {person.get('full_name')}")
            
            print(f"\n3. Spouse Fields:")
            print(f"   - spouse: {person.get('spouse')}")
            print(f"   - spouse_name: {person.get('spouse_name')}")
            print(f"   - marriages: {person.get('marriages')}")
            if person.get('marriages'):
                print(f"     + marriages count: {len(person.get('marriages', []))}")
                for m in person.get('marriages', []):
                    print(f"     + marriage: {m}")
            
            print(f"\n4. Children Fields:")
            print(f"   - children: {person.get('children')}")
            print(f"   - children_string: {person.get('children_string')}")
            if person.get('children'):
                print(f"     + children count: {len(person.get('children', []))}")
                for c in person.get('children', []):
                    print(f"     + child: {c}")
            
            print(f"\n5. Siblings:")
            print(f"   - siblings: {person.get('siblings')}")
            
            print(f"\n6. Full JSON Response:")
            print(json.dumps(person, indent=2, ensure_ascii=False))
            
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Không thể kết nối đến {BASE_URL}")
        print(f"   Hãy đảm bảo Flask app đang chạy")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_person()

