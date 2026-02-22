# -*- coding: utf-8 -*-
"""Extract ADMIN_* and DATA_MANAGEMENT templates from archive_py/admin_routes.py into admin_templates.py.
Nếu archive_py đã bị xóa, script bỏ qua bước extract và chỉ in thông báo."""
import os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_archive_path = 'archive_py/admin_routes.py'
if not os.path.exists(_archive_path):
    print('archive_py/admin_routes.py không còn tồn tại (đã xóa để tránh nhầm lẫn).')
    print('admin_templates.py đã có sẵn template; không cần chạy script này trừ khi tái tạo từ nguồn khác.')
    raise SystemExit(0)

with open(_archive_path, 'r', encoding='utf-8') as f:
    content = f.read()

def extract(start_marker):
    start = content.find(start_marker)
    if start == -1:
        return None
    q = content.find("'''", start)
    if q == -1:
        return None
    q += 3
    end = content.find("'''", q)
    if end == -1:
        return None
    return content[q:end]

dash = extract('ADMIN_DASHBOARD_TEMPLATE = ')
users = extract('ADMIN_USERS_TEMPLATE = ')
data = extract('DATA_MANAGEMENT_TEMPLATE = ')

ADMIN_REQUESTS_TEMPLATE_BODY = r'''
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yêu cầu chỉnh sửa - Admin TBQC</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: #2c3e50; color: white; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; }
        .navbar-menu { display: flex; gap: 20px; list-style: none; }
        .navbar-menu a { color: white; text-decoration: none; padding: 8px 15px; border-radius: 4px; }
        .navbar-menu a:hover { background: rgba(255,255,255,0.1); }
        .container { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        table { width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #34495e; color: white; }
        .error { background: #fee; color: #c33; padding: 12px; border-radius: 6px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>Yêu cầu chỉnh sửa</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <h2>Danh sách yêu cầu</h2>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Người yêu cầu</th>
                    <th>Người liên quan</th>
                    <th>Đời</th>
                    <th>Trạng thái</th>
                    <th>Ngày tạo</th>
                </tr>
            </thead>
            <tbody>
                {% for r in requests %}
                <tr>
                    <td>{{ r.request_id }}</td>
                    <td>{{ r.requester_username or '-' }} ({{ r.requester_name or '-' }})</td>
                    <td>{{ r.person_full_name or '-' }}</td>
                    <td>{{ r.person_generation or '-' }}</td>
                    <td>{{ r.status or 'pending' }}</td>
                    <td>{{ r.created_at.strftime('%d/%m/%Y %H:%M') if r.created_at else '-' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% if not requests %}
        <p style="margin-top:20px;color:#666;">Chưa có yêu cầu nào.</p>
        {% endif %}
    </div>
</body>
</html>
'''

out = '''# -*- coding: utf-8 -*-
# Template strings for admin routes (code cũ - render_template_string)
# Generated from archive_py/admin_routes.py + ADMIN_REQUESTS_TEMPLATE minimal
'''

if dash:
    out += "\nADMIN_DASHBOARD_TEMPLATE = '''\n" + dash + "\n'''\n"
if users:
    out += "\nADMIN_USERS_TEMPLATE = '''\n" + users + "\n'''\n"
out += "\nADMIN_REQUESTS_TEMPLATE = '''" + ADMIN_REQUESTS_TEMPLATE_BODY + "\n'''\n"
if data:
    out += "\nDATA_MANAGEMENT_TEMPLATE = '''\n" + data + "\n'''\n"

with open('admin_templates.py', 'w', encoding='utf-8') as f:
    f.write(out)
print('Written admin_templates.py')
print('Dashboard:', len(dash) if dash else 0, 'Users:', len(users) if users else 0, 'Data:', len(data) if data else 0)
