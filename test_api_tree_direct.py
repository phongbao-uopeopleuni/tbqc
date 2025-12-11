#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API /api/tree trực tiếp bằng cách import Flask app
"""

import sys
import os

# Thêm folder_py vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_py = os.path.join(current_dir, 'folder_py')
if folder_py not in sys.path:
    sys.path.insert(0, folder_py)
    sys.path.insert(0, current_dir)

os.chdir(current_dir)

# Import Flask app
from app import app

# Test route registration
print("="*80)
print("KIEM TRA ROUTE /api/tree")
print("="*80)

# List all routes
print("\nTat ca routes co 'tree' trong ten:")
with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'tree' in rule.rule.lower():
            print(f"  {rule.rule} [{', '.join(rule.methods)}]")

# Test route handler
print("\n" + "="*80)
print("TEST ROUTE HANDLER")
print("="*80)

# Create test client
client = app.test_client()

# Test 1: Basic request
print("\n1. Test GET /api/tree?root_id=P-1-1&max_gen=3")
response = client.get('/api/tree?root_id=P-1-1&max_gen=3')
print(f"   Status Code: {response.status_code}")
print(f"   Response: {response.get_data(as_text=True)[:500]}")

# Test 2: With max_generation
print("\n2. Test GET /api/tree?root_id=P-1-1&max_generation=3")
response = client.get('/api/tree?root_id=P-1-1&max_generation=3')
print(f"   Status Code: {response.status_code}")
print(f"   Response: {response.get_data(as_text=True)[:500]}")

# Test 3: Default
print("\n3. Test GET /api/tree")
response = client.get('/api/tree')
print(f"   Status Code: {response.status_code}")
print(f"   Response: {response.get_data(as_text=True)[:500]}")

print("\n" + "="*80)
print("KET THUC TEST")
print("="*80)

