#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để fix lỗi alias và import lại dữ liệu
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("FIX ALIAS COLUMN AND RE-IMPORT DATA")
print("="*80)

print("\n1. Chay reset_and_import.py de:")
print("   - Drop bang cu")
print("   - Tao schema moi (co alias)")
print("   - Import du lieu tu CSV")
print()

response = input("Ban co muon chay reset_and_import.py ngay bay gio? (y/n): ")
if response.lower() == 'y':
    print("\nDang chay reset_and_import.py...")
    os.system("python reset_and_import.py")
else:
    print("\nBan co the chay thu cong:")
    print("  python reset_and_import.py")

print("\n" + "="*80)
print("Sau khi chay xong, kiem tra:")
print("  python check_schema_alias.py")
print("="*80)

