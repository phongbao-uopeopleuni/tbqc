#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script helper để chạy server từ root directory
Tự động thêm folder_py vào Python path
"""

import sys
import os

# Thêm folder_py vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
folder_py = os.path.join(current_dir, 'folder_py')
if folder_py not in sys.path:
    sys.path.insert(0, folder_py)
    sys.path.insert(0, current_dir)

# Đảm bảo working directory là thư mục root
os.chdir(current_dir)

# Import và chạy app
if __name__ == '__main__':
    # Import app từ folder_py
    from folder_py.app import app
    
    print("="*80)
    print("🚀 ĐANG KHỞI ĐỘNG SERVER...")
    print("="*80)
    print("📂 Working directory:", os.getcwd())
    print("📂 Base directory:", current_dir)
    print("📦 Python path đã được cập nhật")
    
    # Kiểm tra file index.html có tồn tại không
    index_path = os.path.join(current_dir, 'index.html')
    if os.path.exists(index_path):
        print("✅ File index.html tìm thấy tại:", index_path)
    else:
        print("⚠️  CẢNH BÁO: File index.html KHÔNG tìm thấy tại:", index_path)
    
    print("="*80)
    print("\n🌐 Server sẽ chạy tại:")
    print("   - Trang chủ: http://localhost:5000")
    print("   - Admin: http://localhost:5000/admin/login")
    print("   - API: http://localhost:5000/api/persons")
    print("\n⚠️  Nhấn Ctrl+C để dừng server")
    print("="*80 + "\n")
    
    try:
        app.run(debug=True, port=5000, host='0.0.0.0')
    except Exception as e:
        print(f"\n❌ LỖI KHI KHỞI ĐỘNG SERVER: {e}")
        print("\n💡 Kiểm tra:")
        print("   1. Port 5000 có đang được sử dụng bởi ứng dụng khác không?")
        print("   2. MySQL đang chạy chưa?")
        print("   3. Database tbqc2025 đã được tạo chưa?")
        sys.exit(1)
