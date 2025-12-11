#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test for /api/tree endpoint
"""

import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add folder_py to path
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_py = os.path.join(current_dir, 'folder_py')
if folder_py not in sys.path:
    sys.path.insert(0, folder_py)
    sys.path.insert(0, current_dir)

os.chdir(current_dir)

from app import app

# Create test client
client = app.test_client()

print("="*80)
print("COMPREHENSIVE TEST API /api/tree")
print("="*80)

# Test 1: Check route exists
print("\n1. Checking route registration...")
with app.app_context():
    routes = [r for r in app.url_map.iter_rules() if 'tree' in r.rule.lower()]
    if routes:
        print(f"   [OK] Found {len(routes)} route(s) with 'tree':")
        for r in routes:
            print(f"      - {r.rule} [{', '.join(r.methods)}]")
    else:
        print("   [ERROR] No routes found with 'tree'")

# Test 2: Basic request with max_generation
print("\n2. Test GET /api/tree?max_generation=5")
response = client.get('/api/tree?max_generation=5')
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.get_json()
    if data:
        print(f"   [OK] Response received")
        print(f"   Person ID: {data.get('person_id', 'N/A')}")
        print(f"   Full Name: {data.get('full_name', 'N/A')}")
        print(f"   Children Count: {len(data.get('children', []))}")
    else:
        print("   [ERROR] No data in response")
else:
    print(f"   [ERROR] Response: {response.get_data(as_text=True)[:300]}")

# Test 3: Request with max_gen
print("\n3. Test GET /api/tree?max_gen=3")
response = client.get('/api/tree?max_gen=3')
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.get_json()
    if data:
        print(f"   [OK] Response received")
        print(f"   Person ID: {data.get('person_id', 'N/A')}")
    else:
        print("   [ERROR] No data in response")
else:
    print(f"   [ERROR] Response: {response.get_data(as_text=True)[:300]}")

# Test 4: Request with root_id and max_generation
print("\n4. Test GET /api/tree?root_id=P-1-1&max_generation=5")
response = client.get('/api/tree?root_id=P-1-1&max_generation=5')
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.get_json()
    if data:
        print(f"   [OK] Response received")
        print(f"   Person ID: {data.get('person_id', 'N/A')}")
        print(f"   Full Name: {data.get('full_name', 'N/A')}")
    else:
        print("   [ERROR] No data in response")
else:
    print(f"   [ERROR] Response: {response.get_data(as_text=True)[:300]}")

# Test 5: Default request (no parameters)
print("\n5. Test GET /api/tree (default)")
response = client.get('/api/tree')
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.get_json()
    if data:
        print(f"   [OK] Response received")
        print(f"   Person ID: {data.get('person_id', 'N/A')}")
    else:
        print("   [ERROR] No data in response")
else:
    print(f"   [ERROR] Response: {response.get_data(as_text=True)[:300]}")

# Test 6: Check if server is running
print("\n6. Testing server health...")
response = client.get('/api/health')
print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    data = response.get_json()
    print(f"   [OK] Health check: {data.get('status', 'unknown')}")
else:
    print(f"   [ERROR] Health check failed")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
print("\nIf all tests pass, the API is working correctly.")
print("If you see 404 errors, make sure:")
print("  1. Server is running: python start_server.py")
print("  2. Route /api/tree is registered")
print("  3. Database is connected")

