#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test API /api/ancestors để kiểm tra ancestors_chain
"""

import sys
import io
import json

# Fix encoding cho Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Try to import requests, fallback to urllib
try:
    import requests
    USE_REQUESTS = True
except ImportError:
    USE_REQUESTS = False
    try:
        from urllib.request import urlopen, Request
        from urllib.error import URLError, HTTPError
    except ImportError:
        print("ERROR: Cannot import requests or urllib")
        sys.exit(1)

BASE_URL = 'http://localhost:5000'
PERSON_ID = 'P-4-23'  # Ưng Lương Thái Thường Tự Khanh

def fetch_json(url):
    """Fetch JSON từ URL"""
    try:
        if USE_REQUESTS:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Status {response.status_code}'}
        else:
            req = Request(url)
            with urlopen(req, timeout=10) as response:
                if response.getcode() == 200:
                    body = response.read().decode('utf-8')
                    return json.loads(body)
                else:
                    return {'error': f'Status {response.getcode()}'}
    except Exception as e:
        return {'error': str(e)}

def main():
    print("=" * 60)
    print(f"TEST API /api/ancestors/{PERSON_ID}")
    print("=" * 60)
    print("\nLưu ý: Đảm bảo server đang chạy (python app.py)\n")
    
    url = f"{BASE_URL}/api/ancestors/{PERSON_ID}"
    result = fetch_json(url)
    
    if 'error' in result:
        print(f"[ERROR] {result['error']}")
        sys.exit(1)
    
    ancestors_chain = result.get('ancestors_chain', [])
    person = result.get('person', {})
    
    print(f"Person: {person.get('full_name')} (Đời {person.get('generation_level')})")
    print(f"\nAncestors chain length: {len(ancestors_chain)}")
    print("\nAncestors chain:")
    print("-" * 60)
    
    for i, ancestor in enumerate(ancestors_chain, 1):
        person_id = ancestor.get('person_id', 'N/A')
        full_name = ancestor.get('full_name', 'N/A')
        generation = ancestor.get('generation_level') or ancestor.get('generation_number', 'N/A')
        gender = ancestor.get('gender', 'N/A')
        print(f"{i}. {person_id}: {full_name} (Đời {generation}, {gender})")
    
    print("\n" + "=" * 60)
    print("KẾT QUẢ MONG ĐỢI:")
    print("  - P-1-1: Vua Minh Mạng (Đời 1)")
    print("  - P-2-3: TBQC Miên Sủng (Đời 2)")
    print("  - P-3-12: Kỳ Ngoại Hầu Hường Phiêu (Đời 3)")
    print("  - P-4-23: Ưng Lương Thái Thường Tự Khanh (Đời 4)")
    print("=" * 60)

if __name__ == '__main__':
    main()

