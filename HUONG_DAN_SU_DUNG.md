# 📖 Hướng Dẫn Sử Dụng Hệ Thống Gia Phả Nguyễn Phước Tộc

**Website:** https://www.phongtuybienquancong.info

**Cập nhật:** Tháng 1/2026

---

## 📋 Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Các Trang Đăng Nhập](#các-trang-đăng-nhập)
3. [Chi Tiết Từng Trang](#chi-tiết-từng-trang)
4. [Thông Tin Tài Khoản](#thông-tin-tài-khoản)
5. [Hướng Dẫn Sử Dụng](#hướng-dẫn-sử-dụng)
6. [Lưu Ý Bảo Mật](#lưu-ý-bảo-mật)

---

## 🎯 Tổng Quan

Hệ thống Gia Phả Nguyễn Phước Tộc có **4 khu vực yêu cầu đăng nhập**:

1. **Trang Admin** - Quản trị hệ thống
2. **Trang Thành Viên (Members)** - Xem và quản lý danh sách thành viên
3. **Trang Hoạt Động (Activities)** - Đăng bài hoạt động
4. **Trang Gia Phả (Genealogy)** - Xem cây gia phả tương tác

---

## 🔐 Các Trang Đăng Nhập

### 1. Trang Admin (`/admin/login` hoặc `/login`)

**Mục đích:** Quản trị hệ thống, quản lý users, activities, data management, logs

**URL:** 
- https://www.phongtuybienquancong.info/admin/login
- https://www.phongtuybienquancong.info/login

**Template:** `templates/login.html`

**Chức năng:**
- Quản lý users (thêm, sửa, xóa)
- Quản lý activities (đăng, chỉnh sửa, xóa bài)
- Quản lý dữ liệu và xem logs
- Backup database
- Upload ảnh

---

### 2. Trang Thành Viên (`/members`)

**Mục đích:** Xem danh sách thành viên và thực hiện các thao tác (thêm, sửa, xóa)

**URL:** https://www.phongtuybienquancong.info/members

**Template:** `templates/members_gate.html` (trang đăng nhập) → `templates/members.html` (trang chính)

**Chức năng:**
- Xem danh sách tất cả thành viên
- Tìm kiếm và lọc thành viên
- Thêm thành viên mới (yêu cầu password)
- Chỉnh sửa thông tin thành viên (yêu cầu password)
- Xóa thành viên (yêu cầu password)
- Backup dữ liệu (yêu cầu password)

---

### 3. Trang Hoạt Động (`/admin/activities`)

**Mục đích:** Đăng bài hoạt động dòng họ

**URL:** https://www.phongtuybienquancong.info/admin/activities

**Template:** `templates/admin_activities_gate.html` (trang đăng nhập) → `templates/admin_activities.html` (trang quản lý)

**Chức năng:**
- Xem danh sách hoạt động
- Đăng bài hoạt động mới
- Chỉnh sửa bài đăng
- Xóa bài đăng
- Upload ảnh cho bài đăng

---

### 4. Trang Gia Phả (`/genealogy`)

**Mục đích:** Xem cây gia phả tương tác và tra cứu thông tin

**URL:** https://www.phongtuybienquancong.info/genealogy

**Template:** `templates/genealogy.html` (có gate bên trong)

**Chức năng:**
- Xem cây gia phả tương tác (zoom, pan)
- Lọc theo thế hệ
- Tra cứu chuỗi phả hệ (ancestors/descendants)
- Tìm kiếm lăng mộ với bản đồ
- Thống kê thành viên theo thế hệ
- Export PDF

---

## 👤 Thông Tin Tài Khoản

### ⚠️ LƯU Ý QUAN TRỌNG

**Tất cả passwords dưới đây là thông tin nhạy cảm. Chỉ chia sẻ với người được ủy quyền.**

---

### 1. Admin Login (`/admin/login`)

**Cách đăng nhập:**
- Truy cập: https://www.phongtuybienquancong.info/admin/login
- Nhập **username** hoặc **email**
- Nhập **password**
- Tick "Lưu đăng nhập" nếu muốn giữ session lâu hơn
- Click "🔐 Đăng nhập"

**Tài khoản:**
- Tài khoản được quản lý trong database (`users` table)
- Role: `admin` hoặc `editor`
- **Không có default account** - phải tạo bằng script `create_admin_user.py`

**Tạo tài khoản Admin mới:**
```bash
python create_admin_user.py --username admin_tbqc --password your_secure_password
python create_admin_user.py --username tbqc_admin --password your_secure_password
python create_admin_user.py --username phongb --password your_secure_password
```

**⚠️ QUAN TRỌNG:**
- Script này **KHÔNG có default password**
- Bạn **PHẢI cung cấp password** khi tạo user
- Password sẽ được hash bằng bcrypt trước khi lưu vào database

---

### 2. Members Gate (`/members`)

**Cách đăng nhập:**
- Truy cập: https://www.phongtuybienquancong.info/members
- Nhập **username**
- Nhập **password**
- Tick "Lưu mật khẩu" để tự động đăng nhập lần sau
- Click "Đăng nhập"

**Tài khoản (4 tài khoản cố định):**

| Username | Password | Ghi chú |
|----------|----------|---------|
| `tbqcnhanh1` | `nhanh1@123` | Tài khoản 1 |
| `tbqcnhanh2` | `nhanh2@123` | Tài khoản 2 |
| `tbqcnhanh3` | `nhanh3@123` | Tài khoản 3 |
| `tbqcnhanh4` | `nhanh4@123` | Tài khoản 4 |

**Lưu ý:**
- Hệ thống ưu tiên kiểm tra từ **database** (tất cả user có `role='user'` và `is_active=TRUE`)
- Chỉ fallback về hardcoded list khi **không thể kết nối database**
- Để đồng bộ: đảm bảo 4 accounts này có trong database với password tương ứng

**Password cho các thao tác (Add/Edit/Delete/Backup):**
- Password được lấy từ environment variables với priority:
  1. `MEMBERS_PASSWORD` (ưu tiên cao nhất)
  2. `ADMIN_PASSWORD`
  3. `BACKUP_PASSWORD`
  4. Default: `tbqc@2026` (nếu không có env vars)

**⚠️ LƯU Ý:**
- Default password `tbqc@2026` chỉ dùng khi không có environment variables
- Trên production, **PHẢI set** `MEMBERS_PASSWORD` trong environment variables
- Không sử dụng default password trong production

---

### 3. Activities Gate (`/admin/activities`)

**Cách đăng nhập:**
- Truy cập: https://www.phongtuybienquancong.info/admin/activities
- Nhập **username**
- Nhập **password**
- Click "Đăng nhập"

**Tài khoản:**
- **Cùng tài khoản với Members Gate** (4 accounts: `tbqcnhanh1-4`)
- Hoặc bất kỳ user nào trong database có `role='user'` và `is_active=TRUE`

**Xác thực:**
- Sử dụng cùng function `validate_tbqc_gate()` như Members Gate
- Kiểm tra từ database trước, fallback về hardcoded list nếu không kết nối được

---

### 4. Genealogy Gate (`/genealogy`)

**Cách đăng nhập:**
- Truy cập: https://www.phongtuybienquancong.info/genealogy
- Nhập **passphrase** (chuỗi mật khẩu)
- Tick "Lưu mật khẩu" để tự động mở khóa lần sau
- Click "Mở khóa"

**Passphrase hợp lệ (5 passphrases):**

| Passphrase | Ghi chú |
|------------|---------|
| `phutuybien2026` | Passphrase chính |
| `nhanh1@123` | Tương tự Members Gate |
| `nhanh2@123` | Tương tự Members Gate |
| `nhanh3@123` | Tương tự Members Gate |
| `nhanh4@123` | Tương tự Members Gate |

**Lưu ý:**
- Passphrase được lưu trong `localStorage` nếu tick "Lưu mật khẩu"
- Session được lưu trong `sessionStorage` (mất khi đóng browser)
- Tự động unlock nếu đã lưu passphrase và tick "Lưu mật khẩu"

---

## 📝 Hướng Dẫn Sử Dụng Chi Tiết

### 1. Đăng Nhập Admin

**Bước 1:** Truy cập https://www.phongtuybienquancong.info/admin/login

**Bước 2:** Nhập thông tin:
- **Tài khoản:** Username hoặc email của admin account
- **Mật khẩu:** Password của admin account

**Bước 3:** Tick "Lưu đăng nhập" (tùy chọn)

**Bước 4:** Click "🔐 Đăng nhập"

**Sau khi đăng nhập thành công:**
- Redirect đến `/admin/users` (nếu role = admin)
- Redirect đến `/admin/activities` (nếu role = editor/user)

**Quản lý Admin Users:**
- Truy cập `/admin/users` để xem danh sách users
- Có thể thêm, sửa, xóa users
- Set role: `admin`, `editor`, `user`
- Set `is_active` để enable/disable account

---

### 2. Đăng Nhập Thành Viên (Members)

**Bước 1:** Truy cập https://www.phongtuybienquancong.info/members

**Bước 2:** Nhập thông tin:
- **Tên đăng nhập:** `tbqcnhanh1` (hoặc `tbqcnhanh2`, `tbqcnhanh3`, `tbqcnhanh4`)
- **Mật khẩu:** `nhanh1@123` (tương ứng với username)

**Bước 3:** Tick "Lưu mật khẩu" (tùy chọn - sẽ tự động đăng nhập lần sau)

**Bước 4:** Click "Đăng nhập"

**Sau khi đăng nhập thành công:**
- Redirect đến `/members` (trang danh sách thành viên)
- Có thể xem, tìm kiếm, lọc thành viên

**Thực hiện thao tác (Add/Edit/Delete/Backup):**
- Khi click các nút "Thêm", "Sửa", "Xóa", "Backup"
- Hệ thống sẽ yêu cầu nhập password
- Password: `MEMBERS_PASSWORD` từ env vars hoặc `tbqc@2026` (default)

---

### 3. Đăng Nhập Hoạt Động (Activities)

**Bước 1:** Truy cập https://www.phongtuybienquancong.info/admin/activities

**Bước 2:** Nhập thông tin:
- **Tên đăng nhập:** `tbqcnhanh1` (hoặc `tbqcnhanh2`, `tbqcnhanh3`, `tbqcnhanh4`)
- **Mật khẩu:** `nhanh1@123` (tương ứng với username)

**Bước 3:** Click "Đăng nhập"

**Sau khi đăng nhập thành công:**
- Trang sẽ reload và hiển thị form đăng bài
- Có thể đăng bài mới, chỉnh sửa, xóa bài đăng
- Upload ảnh cho bài đăng

**Lưu ý:**
- Session được lưu trong `session['activities_post_ok']`
- Session mất khi đóng browser hoặc logout

---

### 4. Mở Khóa Gia Phả (Genealogy)

**Bước 1:** Truy cập https://www.phongtuybienquancong.info/genealogy

**Bước 2:** Nhập passphrase:
- Một trong 5 passphrases hợp lệ (ví dụ: `phutuybien2026`)

**Bước 3:** Tick "Lưu mật khẩu" (tùy chọn - sẽ tự động mở khóa lần sau)

**Bước 4:** Click "Mở khóa"

**Sau khi mở khóa thành công:**
- Gate sẽ ẩn đi
- Hiển thị nội dung cây gia phả tương tác
- Có thể zoom, pan, filter theo thế hệ
- Tra cứu chuỗi phả hệ
- Tìm kiếm lăng mộ

**Lưu ý:**
- Passphrase được lưu trong `localStorage` nếu tick "Lưu mật khẩu"
- Session được lưu trong `sessionStorage` (mất khi đóng browser)
- Tự động unlock nếu đã lưu passphrase hợp lệ

---

## 🔒 Lưu Ý Bảo Mật

### ⚠️ QUAN TRỌNG

1. **Không chia sẻ passwords với người không được ủy quyền**
2. **Đổi passwords định kỳ** (khuyến nghị 3-6 tháng)
3. **Không sử dụng default passwords trong production**
4. **Set environment variables** cho tất cả passwords trên production:
   - `MEMBERS_PASSWORD`
   - `ADMIN_PASSWORD`
   - `BACKUP_PASSWORD`
   - `SECRET_KEY` (Flask secret key)

### Best Practices

1. **Sử dụng mật khẩu mạnh:**
   - Tối thiểu 12 ký tự
   - Kết hợp chữ hoa, chữ thường, số, ký tự đặc biệt
   - Không dùng thông tin cá nhân

2. **Quản lý tài khoản:**
   - Tạo tài khoản riêng cho từng người
   - Set `is_active=FALSE` khi không còn sử dụng
   - Review danh sách users định kỳ

3. **Session Management:**
   - Logout khi không sử dụng
   - Không tick "Lưu đăng nhập" trên máy công cộng
   - Xóa cookies nếu nghi ngờ bị lộ

4. **Environment Variables:**
   - **KHÔNG** commit passwords vào Git
   - Sử dụng environment variables trên production
   - File `.env` đã được thêm vào `.gitignore`

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề về đăng nhập hoặc quyền truy cập:

1. **Kiểm tra lại username/password** đã đúng chưa
2. **Kiểm tra account có `is_active=TRUE`** trong database không
3. **Liên hệ nhóm Zalo BTS** để được hỗ trợ (theo ghi chú trong Genealogy Gate)
4. **Kiểm tra logs** trong `/admin/logs` (nếu có quyền admin)

---

## 📝 Tóm Tắt Nhanh

| Trang | URL | Username/Passphrase | Password cho thao tác |
|-------|-----|---------------------|----------------------|
| **Admin** | `/admin/login` | Tài khoản trong DB | - |
| **Members** | `/members` | `tbqcnhanh1-4` / `nhanh1@123-4` | `MEMBERS_PASSWORD` hoặc `tbqc@2026` |
| **Activities** | `/admin/activities` | `tbqcnhanh1-4` / `nhanh1@123-4` | - |
| **Genealogy** | `/genealogy` | `phutuybien2026` hoặc `nhanh1@123-4` | - |

---

**⚠️ LƯU Ý CUỐI CÙNG:**

File này chứa thông tin nhạy cảm. **KHÔNG commit** file này lên Git nếu chứa passwords thực tế. Chỉ sử dụng cho mục đích hướng dẫn nội bộ.

**Cập nhật:** Tháng 1/2026
