# -*- coding: utf-8 -*-
# Template strings for admin routes (code cũ - render_template_string)
# Template strings for admin (dashboard, users, requests, data-management). ADMIN_REQUESTS_TEMPLATE minimal.

ADMIN_DASHBOARD_TEMPLATE = '''

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Quản Trị TBQC</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar h1 {
            font-size: 20px;
        }
        .navbar-menu {
            display: flex;
            gap: 20px;
            list-style: none;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .dashboard-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .card p {
            color: #666;
            font-size: 14px;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 15px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ Quản Trị Hệ Thống TBQC</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <h2>Chào mừng, {{ current_user.full_name or current_user.username }}!</h2>
        <p style="color: #666; margin-top: 10px;">Bạn đang đăng nhập với quyền: <strong>{{ current_user.role }}</strong></p>
        
        {% if error %}
        <div class="error" style="background: #fee; color: #c33; padding: 15px; border-radius: 6px; margin: 20px 0;">
            Lỗi: {{ error }}
        </div>
        {% endif %}
        
        <!-- Summary Cards -->
        <div class="dashboard-cards">
            <div class="card">
                <h3>👥 Tổng Thành Viên</h3>
                <p style="font-size: 32px; font-weight: bold; color: #3498db; margin: 10px 0;">
                    {{ stats.total_people or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>❤️ Còn Sống</h3>
                <p style="font-size: 32px; font-weight: bold; color: #27ae60; margin: 10px 0;">
                    {{ stats.alive_count or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>🕯️ Đã Mất</h3>
                <p style="font-size: 32px; font-weight: bold; color: #e74c3c; margin: 10px 0;">
                    {{ stats.deceased_count or 0 }}
                </p>
            </div>
            <div class="card">
                <h3>📊 Số Đời</h3>
                <p style="font-size: 32px; font-weight: bold; color: #9b59b6; margin: 10px 0;">
                    {{ stats.max_generation or 0 }}
                </p>
            </div>
        </div>
        
        <!-- Charts Section -->
        <div style="margin-top: 40px;">
            <h2 style="color: #2c3e50; margin-bottom: 20px;">📊 Thống Kê Chi Tiết</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                <!-- Biểu đồ theo Đời -->
                <div class="card">
                    <h3>📈 Số Người Theo Đời</h3>
                    <canvas id="generationChart" width="400" height="300"></canvas>
                </div>
                
                <!-- Biểu đồ Giới Tính -->
                <div class="card">
                    <h3>👥 Phân Bố Giới Tính</h3>
                    <canvas id="genderChart" width="400" height="300"></canvas>
                </div>
            </div>
            
            <div style="margin-top: 20px;">
                <div class="card">
                    <h3>📊 Tình Trạng Sống/Mất</h3>
                    <canvas id="statusChart" width="400" height="300"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Quick Actions -->
        <div class="dashboard-cards" style="margin-top: 40px;">
            <div class="card">
                <h3>👥 Quản Lý Tài Khoản</h3>
                <p>Thêm, sửa, xóa tài khoản người dùng</p>
                <a href="/admin/users" class="btn">Quản Lý</a>
            </div>
            <div class="card">
                <h3>🌳 Gia Phả</h3>
                <p>Xem và quản lý gia phả</p>
                <a href="/#genealogy" class="btn">Xem Gia Phả</a>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script>
        // Dữ liệu từ server
        const generationData = {{ stats.generation_stats|tojson|safe }};
        const genderData = {{ stats.gender_stats|tojson|safe }};
        const statusData = {{ stats.status_stats|tojson|safe }};
        
        // Biểu đồ theo Đời
        const genCtx = document.getElementById('generationChart').getContext('2d');
        new Chart(genCtx, {
            type: 'bar',
            data: {
                labels: generationData.map(item => 'Đời ' + item.generation_number),
                datasets: [{
                    label: 'Số người',
                    data: generationData.map(item => item.count),
                    backgroundColor: 'rgba(52, 152, 219, 0.6)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Biểu đồ Giới Tính
        const genderCtx = document.getElementById('genderChart').getContext('2d');
        new Chart(genderCtx, {
            type: 'doughnut',
            data: {
                labels: genderData.map(item => item.gender || 'Không rõ'),
                datasets: [{
                    data: genderData.map(item => item.count),
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.6)',
                        'rgba(231, 76, 60, 0.6)',
                        'rgba(149, 165, 166, 0.6)'
                    ]
                }]
            }
        });
        
        // Biểu đồ Tình Trạng
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        new Chart(statusCtx, {
            type: 'bar',
            data: {
                labels: statusData.map(item => item.status || 'Không rõ'),
                datasets: [{
                    label: 'Số người',
                    data: statusData.map(item => item.count),
                    backgroundColor: [
                        'rgba(39, 174, 96, 0.6)',
                        'rgba(231, 76, 60, 0.6)',
                        'rgba(149, 165, 166, 0.6)'
                    ]
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    </script>
</body>
</html>

'''

ADMIN_USERS_TEMPLATE = '''

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Tài Khoản - Admin</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar h1 {
            font-size: 20px;
        }
        .navbar-menu {
            display: flex;
            gap: 20px;
            list-style: none;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .header-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        .btn-warning:hover {
            background: #e67e22;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #229954;
        }
        table {
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .badge {
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-admin {
            background: #e74c3c;
            color: white;
        }
        .badge-user {
            background: #3498db;
            color: white;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            overflow: auto;
        }
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 500px;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .close {
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
        }
        .close:hover {
            color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }
        .form-group input,
        .form-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: #3498db;
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>👥 Quản Lý Tài Khoản</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <div class="header-actions">
            <h2>Danh Sách Tài Khoản</h2>
            <button class="btn btn-primary" onclick="openAddUserModal()">+ Thêm Tài Khoản</button>
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <div id="message"></div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Họ Tên</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Ngày Tạo</th>
                    <th>Hành Động</th>
                </tr>
            </thead>
            <tbody id="usersTable">
                {% for user in users %}
                <tr data-user-id="{{ user.user_id }}">
                    <td>{{ user.user_id }}</td>
                    <td>{{ user.username }}</td>
                    <td>{{ user.full_name or '-' }}</td>
                    <td>{{ user.email or '-' }}</td>
                    <td>
                        <span class="badge {% if user.role == 'admin' %}badge-admin{% else %}badge-user{% endif %}">
                            {{ user.role }}
                        </span>
                    </td>
                    <td>{{ user.created_at.strftime('%d/%m/%Y') if user.created_at else '-' }}</td>
                    <td>
                        <button class="btn btn-warning" onclick="openEditModal({{ user.user_id }}, '{{ user.username }}', '{{ user.full_name or '' }}', '{{ user.email or '' }}', '{{ user.role }}')">Sửa</button>
                        <button class="btn btn-danger" onclick="openResetPasswordModal({{ user.user_id }}, '{{ user.username }}')">Đặt Lại MK</button>
                        {% if user.user_id != current_user.id %}
                        <button class="btn btn-danger" onclick="deleteUser({{ user.user_id }}, '{{ user.username }}')">Xóa</button>
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    
    <!-- Modal Thêm User -->
    <div id="addUserModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Thêm Tài Khoản Mới</h3>
                <span class="close" onclick="closeModal('addUserModal')">&times;</span>
            </div>
            <form id="addUserForm" onsubmit="createUser(event)">
                <div class="form-group">
                    <label>Username *</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Họ Tên</label>
                    <input type="text" name="full_name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email">
                </div>
                <div class="form-group">
                    <label>Role *</label>
                    <select name="role" required>
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Mật Khẩu *</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Nhập Lại Mật Khẩu *</label>
                    <input type="password" name="password_confirm" required minlength="6">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Tạo Tài Khoản</button>
                    <button type="button" class="btn" onclick="closeModal('addUserModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Sửa User -->
    <div id="editUserModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Sửa Tài Khoản</h3>
                <span class="close" onclick="closeModal('editUserModal')">&times;</span>
            </div>
            <form id="editUserForm" onsubmit="updateUser(event)">
                <input type="hidden" name="user_id" id="edit_user_id">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="edit_username" readonly style="background: #f5f5f5;">
                </div>
                <div class="form-group">
                    <label>Họ Tên</label>
                    <input type="text" name="full_name" id="edit_full_name">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" name="email" id="edit_email">
                </div>
                <div class="form-group">
                    <label>Role *</label>
                    <select name="role" id="edit_role" required onchange="updatePermissionsByRole()">
                        <option value="user">User</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                
                <!-- Quyền chi tiết -->
                <div class="form-group" style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #eee;">
                    <label style="font-size: 16px; margin-bottom: 15px;">🔐 Quyền Chi Tiết:</label>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canViewGenealogy" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xem Gia Phả
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canComment" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Bình Luận
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canCreatePost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Tạo Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canEditPost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Sửa Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canDeletePost" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xóa Bài Viết
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canUploadMedia" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Upload Media
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canEditGenealogy" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Chỉnh Sửa Gia Phả
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canManageUsers" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Quản Lý Users
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canConfigurePermissions" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Cấu Hình Quyền
                        </label>
                        <label style="display: flex; align-items: center; font-weight: normal; cursor: pointer;">
                            <input type="checkbox" name="permission" value="canViewDashboard" class="permission-checkbox" style="margin-right: 8px; width: auto;">
                            Xem Dashboard
                        </label>
                    </div>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Lưu Thay Đổi</button>
                    <button type="button" class="btn" onclick="closeModal('editUserModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Modal Đặt Lại Mật Khẩu -->
    <div id="resetPasswordModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3>Đặt Lại Mật Khẩu</h3>
                <span class="close" onclick="closeModal('resetPasswordModal')">&times;</span>
            </div>
            <form id="resetPasswordForm" onsubmit="resetPassword(event)">
                <input type="hidden" name="user_id" id="reset_user_id">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="reset_username" readonly style="background: #f5f5f5;">
                </div>
                <div class="form-group">
                    <label>Mật Khẩu Mới *</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Nhập Lại Mật Khẩu *</label>
                    <input type="password" name="password_confirm" required minlength="6">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn btn-success" style="flex: 1;">Đặt Lại Mật Khẩu</button>
                    <button type="button" class="btn" onclick="closeModal('resetPasswordModal')" style="flex: 1; background: #95a5a6; color: white;">Hủy</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function showMessage(message, type) {
            const msgDiv = document.getElementById('message');
            msgDiv.className = type;
            msgDiv.textContent = message;
            msgDiv.style.display = 'block';
            setTimeout(() => {
                msgDiv.style.display = 'none';
            }, 5000);
        }
        
        function openAddUserModal() {
            document.getElementById('addUserModal').style.display = 'block';
            document.getElementById('addUserForm').reset();
        }
        
        async function openEditModal(userId, username, fullName, email, role) {
            document.getElementById('edit_user_id').value = userId;
            document.getElementById('edit_username').value = username;
            document.getElementById('edit_full_name').value = fullName || '';
            document.getElementById('edit_email').value = email || '';
            document.getElementById('edit_role').value = role;
            
            // Load permissions từ server
            try {
                const response = await fetch(`/admin/api/users/${userId}`);
                const userData = await response.json();
                if (userData.permissions) {
                    // Uncheck all first
                    document.querySelectorAll('.permission-checkbox').forEach(cb => cb.checked = false);
                    // Check permissions
                    Object.keys(userData.permissions).forEach(perm => {
                        if (userData.permissions[perm]) {
                            const checkbox = document.querySelector(`input.permission-checkbox[value="${perm}"]`);
                            if (checkbox) checkbox.checked = true;
                        }
                    });
                } else {
                    // Nếu không có permissions, set theo role
                    updatePermissionsByRole();
                }
            } catch (error) {
                console.error('Lỗi khi load permissions:', error);
                updatePermissionsByRole();
            }
            
            document.getElementById('editUserModal').style.display = 'block';
        }
        
        function updatePermissionsByRole() {
            const role = document.getElementById('edit_role').value;
            const checkboxes = document.querySelectorAll('.permission-checkbox');
            
            // Uncheck all
            checkboxes.forEach(cb => cb.checked = false);
            
            // Set default permissions theo role
            if (role === 'user') {
                document.querySelector('input[value="canViewGenealogy"]').checked = true;
                document.querySelector('input[value="canComment"]').checked = true;
            } else if (role === 'editor') {
                document.querySelector('input[value="canViewGenealogy"]').checked = true;
                document.querySelector('input[value="canComment"]').checked = true;
                document.querySelector('input[value="canCreatePost"]').checked = true;
                document.querySelector('input[value="canEditPost"]').checked = true;
                document.querySelector('input[value="canUploadMedia"]').checked = true;
                document.querySelector('input[value="canEditGenealogy"]').checked = true;
            } else if (role === 'admin') {
                // Admin có tất cả quyền
                checkboxes.forEach(cb => cb.checked = true);
            }
        }
        
        function openResetPasswordModal(userId, username) {
            document.getElementById('reset_user_id').value = userId;
            document.getElementById('reset_username').value = username;
            document.getElementById('resetPasswordForm').reset();
            document.getElementById('resetPasswordModal').style.display = 'block';
        }
        
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }
        
        async function createUser(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            try {
                const response = await fetch('/admin/api/users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã tạo tài khoản thành công!', 'success');
                    closeModal('addUserModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi tạo tài khoản', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function updateUser(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            const userId = data.user_id;
            
            try {
                const response = await fetch(`/admin/api/users/${userId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã cập nhật thành công!', 'success');
                    closeModal('editUserModal');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi cập nhật', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function resetPassword(event) {
            event.preventDefault();
            const form = event.target;
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            const userId = data.user_id;
            
            try {
                const response = await fetch(`/admin/api/users/${userId}/reset-password`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã đặt lại mật khẩu thành công!', 'success');
                    closeModal('resetPasswordModal');
                } else {
                    showMessage(result.error || 'Lỗi khi đặt lại mật khẩu', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        async function deleteUser(userId, username) {
            if (!confirm(`Bạn có chắc chắn muốn xóa tài khoản "${username}"?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/users/${userId}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showMessage(result.message || 'Đã xóa tài khoản thành công!', 'success');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    showMessage(result.error || 'Lỗi khi xóa tài khoản', 'error');
                }
            } catch (error) {
                showMessage('Lỗi kết nối: ' + error.message, 'error');
            }
        }
        
        // Đóng modal khi click ra ngoài
        window.onclick = function(event) {
            const modals = ['addUserModal', 'editUserModal', 'resetPasswordModal'];
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (event.target == modal) {
                    closeModal(modalId);
                }
            });
        }
    </script>
</body>
</html>

'''

ADMIN_REQUESTS_TEMPLATE = '''
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

DATA_MANAGEMENT_TEMPLATE = '''

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quản Lý Dữ Liệu CSV - Admin TBQC</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        .navbar {
            background: #2c3e50;
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .navbar-menu {
            display: flex;
            list-style: none;
            gap: 20px;
        }
        .navbar-menu a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .navbar-menu a:hover {
            background: rgba(255,255,255,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 30px auto;
            padding: 0 20px;
        }
        .page-header {
            background: white;
            padding: 20px 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .page-header h1 {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .tab {
            padding: 12px 24px;
            background: #ecf0f1;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            color: #7f8c8d;
            transition: all 0.3s;
        }
        .tab.active {
            background: #3498db;
            color: white;
        }
        .tab:hover {
            background: #bdc3c7;
        }
        .tab.active:hover {
            background: #2980b9;
        }
        .tab-content {
            display: none;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .tab-content.active {
            display: block;
        }
        .toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 6px;
        }
        .search-box {
            flex: 1;
            max-width: 400px;
        }
        .search-box input {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #bdc3c7;
            border-radius: 6px;
            font-size: 14px;
        }
        .search-box input:focus {
            outline: none;
            border-color: #3498db;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .btn-primary {
            background: #3498db;
            color: white;
        }
        .btn-primary:hover {
            background: #2980b9;
        }
        .btn-success {
            background: #27ae60;
            color: white;
        }
        .btn-success:hover {
            background: #229954;
        }
        .btn-danger {
            background: #e74c3c;
            color: white;
        }
        .btn-danger:hover {
            background: #c0392b;
        }
        .btn-warning {
            background: #f39c12;
            color: white;
        }
        .btn-warning:hover {
            background: #e67e22;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }
        th {
            background: #34495e;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .btn-sm {
            padding: 6px 12px;
            font-size: 12px;
            margin: 0 2px;
        }
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 20px;
        }
        .pagination button {
            padding: 8px 12px;
            border: 1px solid #bdc3c7;
            background: white;
            border-radius: 4px;
            cursor: pointer;
        }
        .pagination button:hover {
            background: #ecf0f1;
        }
        .pagination button.active {
            background: #3498db;
            color: white;
            border-color: #3498db;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            overflow: auto;
        }
        .modal-content {
            background: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 8px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
        }
        .close {
            font-size: 28px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
        }
        .close:hover {
            color: #000;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #2c3e50;
        }
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 2px solid #bdc3c7;
            border-radius: 6px;
            font-size: 14px;
        }
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #3498db;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }
        .alert {
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>🏛️ Quản Trị Hệ Thống TBQC</h1>
        <ul class="navbar-menu">
            <li><a href="/admin/dashboard">Dashboard</a></li>
            <li><a href="/admin/users">Tài Khoản</a></li>
            <li><a href="/admin/data-management">Quản Lý Dữ Liệu</a></li>
            <li><a href="/">Trang Chủ</a></li>
            <li><a href="/admin/logout">Đăng Xuất</a></li>
        </ul>
    </nav>
    <div class="container">
        <div class="page-header">
            <h1>📊 Quản Lý Dữ Liệu CSV</h1>
            <p style="color: #7f8c8d; margin-top: 5px;">Quản lý và điều chỉnh dữ liệu từ 3 file CSV: Sheet1, Sheet2, Sheet3</p>
        </div>
        
        <div id="alertContainer"></div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('sheet1')">📋 Sheet 1 - Thông tin chi tiết</button>
            <button class="tab" onclick="switchTab('sheet2')">🔗 Sheet 2 - Quan hệ</button>
            <button class="tab" onclick="switchTab('sheet3')">👨‍👩‍👧‍👦 Sheet 3 - Chi tiết quan hệ</button>
        </div>
        
        <!-- Sheet 1 Content -->
        <div id="sheet1" class="tab-content active">
            <div class="toolbar">
                <div class="search-box">
                    <input type="text" id="searchSheet1" placeholder="Tìm kiếm..." oninput="filterData('sheet1')">
                </div>
                <button class="btn btn-success" onclick="openAddModal('sheet1')">➕ Thêm mới</button>
                <button class="btn btn-primary" onclick="loadSheetData('sheet1')">🔄 Làm mới</button>
            </div>
            <div id="sheet1TableContainer">
                <div class="loading">Đang tải dữ liệu...</div>
            </div>
        </div>
        
        <!-- Sheet 2 Content -->
        <div id="sheet2" class="tab-content">
            <div class="toolbar">
                <div class="search-box">
                    <input type="text" id="searchSheet2" placeholder="Tìm kiếm..." oninput="filterData('sheet2')">
                </div>
                <button class="btn btn-success" onclick="openAddModal('sheet2')">➕ Thêm mới</button>
                <button class="btn btn-primary" onclick="loadSheetData('sheet2')">🔄 Làm mới</button>
            </div>
            <div id="sheet2TableContainer">
                <div class="loading">Đang tải dữ liệu...</div>
            </div>
        </div>
        
        <!-- Sheet 3 Content -->
        <div id="sheet3" class="tab-content">
            <div class="toolbar">
                <div class="search-box">
                    <input type="text" id="searchSheet3" placeholder="Tìm kiếm..." oninput="filterData('sheet3')">
                </div>
                <button class="btn btn-success" onclick="openAddModal('sheet3')">➕ Thêm mới</button>
                <button class="btn btn-primary" onclick="loadSheetData('sheet3')">🔄 Làm mới</button>
            </div>
            <div id="sheet3TableContainer">
                <div class="loading">Đang tải dữ liệu...</div>
            </div>
        </div>
    </div>
    
    <!-- Modal for Add/Edit -->
    <div id="dataModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Thêm mới</h2>
                <span class="close" onclick="closeModal()">&times;</span>
            </div>
            <form id="dataForm" onsubmit="saveData(event)">
                <div id="modalFormContent">
                    <!-- Form fields will be generated dynamically -->
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
                    <button type="button" class="btn btn-warning" onclick="closeModal()">Hủy</button>
                    <button type="submit" class="btn btn-success">💾 Lưu</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        let currentSheet = 'sheet1';
        let currentData = {};
        let currentPage = {sheet1: 1, sheet2: 1, sheet3: 1};
        const itemsPerPage = 50;
        
        function switchTab(sheetName) {
            currentSheet = sheetName;
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(sheetName).classList.add('active');
            
            loadSheetData(sheetName);
        }
        
        async function loadSheetData(sheetName) {
            const container = document.getElementById(sheetName + 'TableContainer');
            container.innerHTML = '<div class="loading">Đang tải dữ liệu...</div>';
            
            try {
                const response = await fetch(`/admin/api/csv-data/${sheetName}`);
                const result = await response.json();
                
                if (result.success) {
                    currentData[sheetName] = result.data;
                    renderTable(sheetName, result.data);
                } else {
                    container.innerHTML = `<div class="alert alert-error">Lỗi: ${result.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="alert alert-error">Lỗi kết nối: ${error.message}</div>`;
            }
        }
        
        function renderTable(sheetName, data) {
            if (!data || data.length === 0) {
                document.getElementById(sheetName + 'TableContainer').innerHTML = 
                    '<div class="alert">Không có dữ liệu</div>';
                return;
            }
            
            const headers = Object.keys(data[0]);
            const startIndex = (currentPage[sheetName] - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const pageData = data.slice(startIndex, endIndex);
            const totalPages = Math.ceil(data.length / itemsPerPage);
            
            let html = '<table><thead><tr>';
            headers.forEach(header => {
                html += `<th>${header}</th>`;
            });
            html += '<th>Thao tác</th></tr></thead><tbody>';
            
            pageData.forEach((row, index) => {
                const rowIndex = startIndex + index;
                html += '<tr>';
                headers.forEach(header => {
                    const value = row[header] || '';
                    html += `<td>${value.length > 50 ? value.substring(0, 50) + '...' : value}</td>`;
                });
                html += `<td>
                    <button class="btn btn-warning btn-sm" onclick="openEditModal('${sheetName}', ${rowIndex})">✏️ Sửa</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteRow('${sheetName}', ${rowIndex})">🗑️ Xóa</button>
                </td>`;
                html += '</tr>';
            });
            
            html += '</tbody></table>';
            
            if (totalPages > 1) {
                html += '<div class="pagination">';
                for (let i = 1; i <= totalPages; i++) {
                    html += `<button class="${i === currentPage[sheetName] ? 'active' : ''}" 
                             onclick="changePage('${sheetName}', ${i})">${i}</button>`;
                }
                html += '</div>';
            }
            
            document.getElementById(sheetName + 'TableContainer').innerHTML = html;
        }
        
        function changePage(sheetName, page) {
            currentPage[sheetName] = page;
            renderTable(sheetName, currentData[sheetName] || []);
        }
        
        function filterData(sheetName) {
            const searchTerm = document.getElementById('search' + sheetName.charAt(0).toUpperCase() + sheetName.slice(1)).value.toLowerCase();
            const data = currentData[sheetName] || [];
            
            if (!searchTerm) {
                renderTable(sheetName, data);
                return;
            }
            
            const filtered = data.filter(row => {
                return Object.values(row).some(value => 
                    String(value).toLowerCase().includes(searchTerm)
                );
            });
            
            currentPage[sheetName] = 1;
            renderTable(sheetName, filtered);
        }
        
        function openAddModal(sheetName) {
            currentSheet = sheetName;
            document.getElementById('modalTitle').textContent = 'Thêm mới - ' + sheetName.toUpperCase();
            
            const data = currentData[sheetName] || [];
            if (data.length === 0) {
                alert('Vui lòng tải dữ liệu trước');
                return;
            }
            
            const headers = Object.keys(data[0]);
            let formHTML = '<div class="form-row">';
            
            headers.forEach(header => {
                formHTML += `
                    <div class="form-group">
                        <label>${header}:</label>
                        <input type="text" name="${header}" value="">
                    </div>
                `;
            });
            
            formHTML += '</div>';
            document.getElementById('modalFormContent').innerHTML = formHTML;
            document.getElementById('dataForm').setAttribute('data-row-index', '-1');
            document.getElementById('dataModal').style.display = 'block';
        }
        
        function openEditModal(sheetName, rowIndex) {
            currentSheet = sheetName;
            document.getElementById('modalTitle').textContent = 'Chỉnh sửa - ' + sheetName.toUpperCase();
            
            const data = currentData[sheetName] || [];
            const row = data[rowIndex];
            
            if (!row) {
                alert('Không tìm thấy dữ liệu');
                return;
            }
            
            const headers = Object.keys(row);
            let formHTML = '<div class="form-row">';
            
            headers.forEach(header => {
                const value = row[header] || '';
                formHTML += `
                    <div class="form-group">
                        <label>${header}:</label>
                        <input type="text" name="${header}" value="${String(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;')}">
                    </div>
                `;
            });
            
            formHTML += '</div>';
            document.getElementById('modalFormContent').innerHTML = formHTML;
            document.getElementById('dataForm').setAttribute('data-row-index', rowIndex);
            document.getElementById('dataModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('dataModal').style.display = 'none';
        }
        
        async function saveData(event) {
            event.preventDefault();
            
            const form = event.target;
            const formData = new FormData(form);
            const rowIndex = parseInt(form.getAttribute('data-row-index'));
            const data = {};
            
            for (const [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            try {
                const url = rowIndex === -1 
                    ? `/admin/api/csv-data/${currentSheet}`
                    : `/admin/api/csv-data/${currentSheet}/${rowIndex}`;
                
                const method = rowIndex === -1 ? 'POST' : 'PUT';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', result.message || 'Đã lưu thành công!');
                    closeModal();
                    loadSheetData(currentSheet);
                } else {
                    showAlert('error', 'Lỗi: ' + (result.error || 'Không thể lưu dữ liệu'));
                }
            } catch (error) {
                showAlert('error', 'Lỗi kết nối: ' + error.message);
            }
        }
        
        async function deleteRow(sheetName, rowIndex) {
            if (!confirm('Bạn có chắc chắn muốn xóa dòng này?')) {
                return;
            }
            
            try {
                const response = await fetch(`/admin/api/csv-data/${sheetName}/${rowIndex}`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showAlert('success', result.message || 'Đã xóa thành công!');
                    loadSheetData(sheetName);
                } else {
                    showAlert('error', 'Lỗi: ' + (result.error || 'Không thể xóa dữ liệu'));
                }
            } catch (error) {
                showAlert('error', 'Lỗi kết nối: ' + error.message);
            }
        }
        
        function showAlert(type, message) {
            const alertContainer = document.getElementById('alertContainer');
            const alertClass = type === 'success' ? 'alert-success' : 'alert-error';
            alertContainer.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
            
            setTimeout(() => {
                alertContainer.innerHTML = '';
            }, 5000);
        }
        
        // Load data on page load
        window.addEventListener('DOMContentLoaded', () => {
            loadSheetData('sheet1');
        });
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('dataModal');
            if (event.target == modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>

'''
