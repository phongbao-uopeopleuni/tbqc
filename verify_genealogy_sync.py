#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để verify /genealogy đồng bộ với /members

Test cases:
1. Search normalization (hoa/thường, khoảng trắng)
2. Person_ID variants (P-7-654, p-7-654, 7-654, 654)
3. Spouse và children khớp với /members
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"  # Thay đổi nếu cần

def test_search_normalization():
    """Test search normalization"""
    print("\n=== Test 1: Search Normalization ===")
    
    test_cases = [
        ("Bảo Phong", "Tên có dấu"),
        ("bao phong", "Tên không dấu, chữ thường"),
        ("BAO PHONG", "Tên chữ hoa"),
        (" Bảo Phong ", "Khoảng trắng thừa"),
        ("Bảo  Phong", "Khoảng trắng kép"),
    ]
    
    for query, description in test_cases:
        print(f"\n  Testing: {description} - Query: '{query}'")
        try:
            response = requests.get(f"{BASE_URL}/api/search", params={"q": query, "limit": 10})
            if response.status_code == 200:
                results = response.json()
                print(f"    ✅ Found {len(results)} results")
                if results:
                    print(f"    First result: {results[0].get('full_name')} ({results[0].get('person_id')})")
            else:
                print(f"    ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_person_id_variants():
    """Test Person_ID variants"""
    print("\n=== Test 2: Person_ID Variants ===")
    
    test_cases = [
        ("P-7-654", "Full Person_ID uppercase"),
        ("p-7-654", "Full Person_ID lowercase"),
        ("7-654", "Without P prefix"),
        ("654", "Only number"),
    ]
    
    for query, description in test_cases:
        print(f"\n  Testing: {description} - Query: '{query}'")
        try:
            response = requests.get(f"{BASE_URL}/api/search", params={"q": query, "limit": 10})
            if response.status_code == 200:
                results = response.json()
                print(f"    ✅ Found {len(results)} results")
                if results:
                    for r in results:
                        if "654" in str(r.get('person_id', '')):
                            print(f"    ✅ Match: {r.get('full_name')} ({r.get('person_id')})")
                            break
            else:
                print(f"    ❌ HTTP {response.status_code}")
        except Exception as e:
            print(f"    ❌ Error: {e}")

def test_spouse_children_consistency():
    """Test spouse và children khớp với /members"""
    print("\n=== Test 3: Spouse & Children Consistency ===")
    
    # Lấy danh sách từ /api/members
    print("\n  Fetching data from /api/members...")
    try:
        members_response = requests.get(f"{BASE_URL}/api/members")
        if members_response.status_code != 200:
            print(f"    ❌ Cannot fetch /api/members: HTTP {members_response.status_code}")
            return
        
        members_data = members_response.json()
        if not members_data.get('success'):
            print(f"    ❌ /api/members returned error: {members_data.get('error')}")
            return
        
        members = members_data.get('data', [])
        print(f"    ✅ Loaded {len(members)} members")
        
        # Test với một vài person có spouse/children
        test_persons = []
        for m in members[:20]:  # Test với 20 người đầu tiên
            if m.get('spouses') or m.get('children'):
                test_persons.append(m)
                if len(test_persons) >= 5:  # Test với 5 người có spouse/children
                    break
        
        if not test_persons:
            print("    ⚠️  No persons with spouse/children found in first 20 members")
            return
        
        print(f"\n  Testing {len(test_persons)} persons with spouse/children...")
        
        for person in test_persons:
            person_id = person.get('person_id')
            person_name = person.get('full_name')
            members_spouse = person.get('spouses', '')
            members_children = person.get('children', '')
            
            print(f"\n    Person: {person_name} ({person_id})")
            
            # Test /api/person
            try:
                person_response = requests.get(f"{BASE_URL}/api/person/{person_id}")
                if person_response.status_code == 200:
                    person_data = person_response.json()
                    person_detail = person_data.get('person') or person_data
                    
                    api_spouse = person_detail.get('spouse') or person_detail.get('spouse_name', '')
                    api_children = person_detail.get('children_string') or person_detail.get('children', '')
                    
                    # Normalize để so sánh
                    members_spouse_norm = (members_spouse or '').strip()
                    api_spouse_norm = (api_spouse or '').strip()
                    members_children_norm = (members_children or '').strip()
                    api_children_norm = (api_children or '').strip()
                    
                    spouse_match = members_spouse_norm == api_spouse_norm
                    children_match = members_children_norm == api_children_norm
                    
                    if spouse_match and children_match:
                        print(f"      ✅ Spouse & Children match")
                    else:
                        print(f"      ⚠️  Mismatch:")
                        if not spouse_match:
                            print(f"        Spouse:")
                            print(f"          /members: '{members_spouse_norm}'")
                            print(f"          /api/person: '{api_spouse_norm}'")
                        if not children_match:
                            print(f"        Children:")
                            print(f"          /members: '{members_children_norm}'")
                            print(f"          /api/person: '{api_children_norm}'")
                else:
                    print(f"      ❌ Cannot fetch /api/person/{person_id}: HTTP {person_response.status_code}")
            except Exception as e:
                print(f"      ❌ Error fetching /api/person/{person_id}: {e}")
            
            # Test /api/search
            try:
                search_response = requests.get(f"{BASE_URL}/api/search", params={"q": person_name, "limit": 10})
                if search_response.status_code == 200:
                    search_results = search_response.json()
                    # Tìm person trong kết quả
                    found = None
                    for r in search_results:
                        if r.get('person_id') == person_id:
                            found = r
                            break
                    
                    if found:
                        search_spouse = found.get('spouse') or found.get('spouse_name', '')
                        search_children = found.get('children') or found.get('children_string', '')
                        
                        search_spouse_norm = (search_spouse or '').strip()
                        search_children_norm = (search_children or '').strip()
                        
                        spouse_match = members_spouse_norm == search_spouse_norm
                        children_match = members_children_norm == search_children_norm
                        
                        if spouse_match and children_match:
                            print(f"      ✅ /api/search spouse & children match")
                        else:
                            print(f"      ⚠️  /api/search mismatch:")
                            if not spouse_match:
                                print(f"        Spouse: /members='{members_spouse_norm}' vs /api/search='{search_spouse_norm}'")
                            if not children_match:
                                print(f"        Children: /members='{members_children_norm}' vs /api/search='{search_children_norm}'")
                    else:
                        print(f"      ⚠️  Person not found in /api/search results")
                else:
                    print(f"      ❌ Cannot fetch /api/search: HTTP {search_response.status_code}")
            except Exception as e:
                print(f"      ❌ Error fetching /api/search: {e}")
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("=" * 60)
    print("Genealogy Sync Verification Script")
    print("=" * 60)
    
    try:
        test_search_normalization()
        test_person_id_variants()
        test_spouse_children_consistency()
        
        print("\n" + "=" * 60)
        print("Verification complete!")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

