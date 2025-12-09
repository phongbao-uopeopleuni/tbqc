#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script kiểm tra server có chạy đúng không
"""

import requests
import sys

def check_server():
    """Kiểm tra server"""
    base_url = "http://localhost:5000"
    
    print("="*80)
    print("🔍 KIỂM TRA SERVER")
    print("="*80)
    
    # Test 1: Kiểm tra server có chạy không
    print("\n1️⃣  Kiểm tra server có chạy...")
    try:
        response = requests.get(base_url, timeout=5)
        print(f"   ✅ Server đang chạy (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("   ❌ Server KHÔNG chạy hoặc không thể kết nối")
        print("   💡 Hãy chạy: python start_server.py")
        return False
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False
    
    # Test 2: Kiểm tra route '/'
    print("\n2️⃣  Kiểm tra route '/' (trang chủ)...")
    try:
        response = requests.get(base_url + "/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Trang chủ hoạt động")
            if 'html' in response.headers.get('content-type', '').lower():
                print("   ✅ Trả về HTML")
            else:
                print(f"   ⚠️  Content-Type: {response.headers.get('content-type')}")
        else:
            print(f"   ❌ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
    
    # Test 3: Kiểm tra API
    print("\n3️⃣  Kiểm tra API '/api/persons'...")
    try:
        response = requests.get(base_url + "/api/persons", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"   ✅ API hoạt động (trả về {len(data)} persons)")
            else:
                print(f"   ⚠️  API trả về dữ liệu không đúng format")
        elif response.status_code == 500:
            print("   ❌ Lỗi server (500) - có thể do database chưa kết nối")
        else:
            print(f"   ❌ Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
    
    # Test 4: Kiểm tra admin route
    print("\n4️⃣  Kiểm tra route '/admin/login'...")
    try:
        response = requests.get(base_url + "/admin/login", timeout=5)
        if response.status_code == 200:
            print("   ✅ Trang admin login hoạt động")
        else:
            print(f"   ⚠️  Status code: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
    
    print("\n" + "="*80)
    print("✅ HOÀN THÀNH KIỂM TRA")
    print("="*80)
    return True

if __name__ == '__main__':
    try:
        check_server()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng kiểm tra")
        sys.exit(0)
