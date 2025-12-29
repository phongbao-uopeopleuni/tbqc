#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify generation dropdown sorting logic
"""
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def sort_generation_options(options):
    """
    Sort generation options numerically
    Extracts number from "Đời X" format and sorts ascending
    """
    def extract_number(text):
        import re
        match = re.search(r'\d+', text)
        return int(match.group(0)) if match else float('inf')
    
    return sorted(options, key=lambda opt: extract_number(opt['text']))

# Test case: Unsorted options
test_options = [
    {'value': '1', 'text': 'Đến đời 1'},
    {'value': '10', 'text': 'Đến đời 10'},
    {'value': '2', 'text': 'Đến đời 2'},
    {'value': '5', 'text': 'Đến đời 5'},
    {'value': '3', 'text': 'Đến đời 3'},
]

print("Before sorting:")
for opt in test_options:
    print(f"  {opt['text']}")

sorted_options = sort_generation_options(test_options)

print("\nAfter sorting:")
for opt in sorted_options:
    print(f"  {opt['text']}")

# Verify
expected_order = ['Đến đời 1', 'Đến đời 2', 'Đến đời 3', 'Đến đời 5', 'Đến đời 10']
actual_order = [opt['text'] for opt in sorted_options]

if actual_order == expected_order:
    print("\n✅ PASS: Options are sorted correctly!")
else:
    print(f"\n❌ FAIL: Expected {expected_order}, got {actual_order}")

# Test with duplicates
test_with_duplicates = [
    {'value': '5', 'text': 'Đến đời 5'},
    {'value': '1', 'text': 'Đến đời 1'},
    {'value': '5', 'text': 'Đến đời 5'},  # Duplicate
    {'value': '10', 'text': 'Đến đời 10'},
]

print("\n\nTest with duplicates:")
print("Before (with duplicates):")
for opt in test_with_duplicates:
    print(f"  {opt['text']}")

# Remove duplicates using Set
unique_values = set()
deduplicated = []
for opt in test_with_duplicates:
    if opt['value'] not in unique_values:
        unique_values.add(opt['value'])
        deduplicated.append(opt)

sorted_deduplicated = sort_generation_options(deduplicated)
print("\nAfter deduplication and sorting:")
for opt in sorted_deduplicated:
    print(f"  {opt['text']}")

