#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API endpoints để kiểm tra kết nối database
"""

import requests
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:5000"

print("="*80)
print("KIEM TRA API ENDPOINTS")
print("="*80)

# Test 1: Health endpoint
print(f"\n1. Test /api/health")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Server: {data.get('server')}")
        print(f"   Database: {data.get('database')}")
        print(f"   DB Config: {data.get('db_config')}")
        print(f"   Stats: {data.get('stats')}")
    else:
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: /api/persons
print(f"\n2. Test /api/persons")
try:
    response = requests.get(f"{BASE_URL}/api/persons", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Số lượng persons: {len(data) if isinstance(data, list) else 'N/A'}")
        if isinstance(data, list) and len(data) > 0:
            print(f"   Person đầu tiên: {data[0].get('person_id')} - {data[0].get('full_name')}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: /api/search
print(f"\n3. Test /api/search?q=Minh")
try:
    response = requests.get(f"{BASE_URL}/api/search?q=Minh", timeout=10)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Số kết quả: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "="*80)
print("Luu y: Neu database status la 'connection_failed' hoac 'error',")
print("      co the la van de ket noi database hoac database trong.")

