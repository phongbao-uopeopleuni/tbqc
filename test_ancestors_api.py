#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API /api/ancestors
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
print("TEST API /api/ancestors/P-7-654")
print("="*80)

# Test
response = client.get('/api/ancestors/P-7-654')
print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.get_json()
    if data:
        person = data.get('person', {})
        ancestors = data.get('ancestors_chain', [])
        print(f"\n[OK] Person ID: {person.get('person_id')}")
        print(f"[OK] Person Name: {person.get('full_name')}")
        print(f"[OK] Ancestors Count: {len(ancestors)}")
        if ancestors:
            print(f"\nFirst 3 ancestors:")
            for i, anc in enumerate(ancestors[:3], 1):
                print(f"  {i}. {anc.get('person_id')} - {anc.get('full_name')} (Level {anc.get('level')})")
    else:
        print("[ERROR] No data returned")
else:
    print(f"\n[ERROR] Response: {response.get_data(as_text=True)[:500]}")

print("\n" + "="*80)

