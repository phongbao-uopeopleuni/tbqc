#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API /api/tree - Khong can requests module
"""

import urllib.request
import urllib.parse
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:5000"

def test_api(url, params=None):
    """Test API endpoint"""
    try:
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            data = json.loads(response.read().decode('utf-8'))
            return status, data
    except Exception as e:
        return None, str(e)

print("="*80)
print("TEST API /api/tree")
print("="*80)

# Test 1: Basic tree
print("\n1. Test /api/tree?root_id=P-1-1&max_gen=3")
status, result = test_api(f"{BASE_URL}/api/tree", {'root_id': 'P-1-1', 'max_gen': 3})
if status == 200:
    print(f"   Status: {status}")
    print(f"   OK: Tree co {len(str(result))} characters")
    print(f"   Sample: {json.dumps(result, ensure_ascii=False)[:200]}...")
else:
    print(f"   ERROR: Status={status}, Error={result}")

# Test 2: With max_generation (frontend parameter)
print("\n2. Test /api/tree?root_id=P-1-1&max_generation=3")
status, result = test_api(f"{BASE_URL}/api/tree", {'root_id': 'P-1-1', 'max_generation': 3})
if status == 200:
    print(f"   Status: {status}")
    print(f"   OK: Tree co {len(str(result))} characters")
else:
    print(f"   ERROR: Status={status}, Error={result}")

# Test 3: Default (no parameters)
print("\n3. Test /api/tree (default)")
status, result = test_api(f"{BASE_URL}/api/tree")
if status == 200:
    print(f"   Status: {status}")
    print(f"   OK: Tree co {len(str(result))} characters")
else:
    print(f"   ERROR: Status={status}, Error={result}")

print("\n" + "="*80)
print("Luu y: Neu server chua chay, chay: python start_server.py")
print("="*80)

