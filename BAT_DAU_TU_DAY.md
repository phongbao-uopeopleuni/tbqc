# 🚀 Bắt Đầu Từ Đây - Hướng Dẫn Từng Bước

## ✅ Bạn Đã Hoàn Thành:
- ✅ Code đã push lên GitHub
- ✅ Railway project đã tạo
- ✅ MySQL database đã deploy (Online)
- ✅ Web service đã có Start Command và status "Completed"
- ✅ URL: `tbqc-production.up.railway.app`

---

## 📋 Các Bước Tiếp Theo (Làm Ngay!)

### Bước 1: Kiểm Tra Website Có Chạy Không 🌐

1. **Truy cập website:**
   ```
   https://tbqc-production.up.railway.app
   ```

2. **Kiểm tra:**
   - [ ] Website có load được không?
   - [ ] Có hiển thị giao diện không?
   - [ ] Có lỗi 500/404 không?

**Nếu website load được → Chuyển Bước 2**
**Nếu website không load → Xem logs trong Railway**

---

### Bước 2: Kiểm Tra Database Connection 🔌

1. **Truy cập health check:**
   ```
   https://tbqc-production.up.railway.app/api/health
   ```

2. **Kiểm tra response:**
   - Nếu thấy `"database": "connected"` → ✅ Database OK, chuyển Bước 3
   - Nếu thấy `"database": "connection_failed"` → Cần fix environment variables (Bước 2.1)

#### Bước 2.1: Fix Database Connection (Nếu cần)

1. **Vào Railway Dashboard:**
   - Click vào **MySQL** service
   - Vào tab **Variables**
   - Copy các giá trị:
     - `MYSQLHOST`
     - `MYSQLDATABASE`
     - `MYSQLUSER`
     - `MYSQLPASSWORD`
     - `MYSQLPORT`

2. **Vào `tbqc` service:**
   - Vào tab **Variables**
   - Thêm các biến sau (nếu chưa có):
     ```
     DB_HOST=<paste MYSQLHOST>
     DB_NAME=<paste MYSQLDATABASE>
     DB_USER=<paste MYSQLUSER>
     DB_PASSWORD=<paste MYSQLPASSWORD>
     DB_PORT=<paste MYSQLPORT>
     SECRET_KEY=<random string, ví dụ: my-secret-key-123>
     ```

3. **Save và redeploy:**
   - Railway sẽ tự động redeploy
   - Đợi deploy xong (status "Completed")
   - Test lại `/api/health`

---

### Bước 3: Import Database (Nếu chưa có data) 📥

**Nếu `/api/health` trả về `"database": "connected"` nhưng không có data:**

1. **Export từ local:**
   ```bash
   mysqldump -u tbqc_admin -p tbqc2025 > backup.sql
   ```

2. **Lấy connection info từ Railway:**
   - Vào MySQL service → **Connect** tab
   - Copy "Public Network" connection string
   - Hoặc dùng thông tin từ Variables tab

3. **Import vào Railway MySQL:**

   **Cách A: Dùng MySQL Workbench (Dễ nhất)**
   - Mở MySQL Workbench
   - Tạo connection mới:
     - Host: `<MYSQLHOST>` (từ Variables)
     - Port: `<MYSQLPORT>`
     - Username: `<MYSQLUSER>`
     - Password: `<MYSQLPASSWORD>`
   - Connect
   - File → Run SQL Script → chọn `backup.sql`
   - Execute

   **Cách B: Dùng Command Line**
   ```bash
   mysql -h <MYSQLHOST> -P <MYSQLPORT> -u <MYSQLUSER> -p <MYSQLDATABASE> < backup.sql
   ```

   **Cách C: Dùng Railway CLI**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   
   # Login
   railway login
   
   # Link project
   railway link
   
   # Connect to MySQL
   railway connect mysql
   
   # Import
   mysql -u <user> -p < backup.sql
   ```

---

### Bước 4: Test Website Hoạt Động Đầy Đủ ✅

Sau khi database đã có data:

1. **Test trang chủ:**
   ```
   https://tbqc-production.up.railway.app
   ```
   - [ ] Cây gia phả có hiển thị không?
   - [ ] Activities preview có load không?
   - [ ] Stats section có số liệu không?

2. **Test trang thành viên:**
   ```
   https://tbqc-production.up.railway.app/members
   ```
   - [ ] Bảng thành viên có load được không?
   - [ ] Có hiển thị data không?

3. **Test API endpoints:**
   - `/api/persons` → Phải trả về array có data
   - `/api/members` → Phải trả về `{"success": true, "data": [...]}`
   - `/api/stats/members` → Phải trả về số liệu thống kê

---

## 🎯 Tóm Tắt - Làm Ngay Bây Giờ

### 1. Test Website (Làm ngay!)
- Truy cập: `https://tbqc-production.up.railway.app`
- Xem có load được không

### 2. Test Database Connection
- Truy cập: `https://tbqc-production.up.railway.app/api/health`
- Xem `"database"` có phải `"connected"` không

### 3. Nếu Database Chưa Connected
- Setup environment variables (Bước 2.1 ở trên)

### 4. Nếu Database Connected Nhưng Không Có Data
- Import database (Bước 3 ở trên)

---

## 🔍 Nếu Vẫn Gặp Lỗi

### Xem Logs:
1. Vào `tbqc` service → **Deployments**
2. Click deployment mới nhất
3. Xem **Logs** tab
4. Tìm dòng có `ERROR` hoặc `Failed`
5. Copy error message

### Các Lỗi Thường Gặp:

**"Cannot connect to database"**
- Kiểm tra environment variables
- Đảm bảo MySQL service đang running

**"Empty result" (không có data)**
- Database đã kết nối nhưng chưa có data
- Cần import database

**"ModuleNotFoundError"**
- Kiểm tra `requirements.txt` có đủ packages
- Railway sẽ tự install từ requirements.txt

---

## ✅ Checklist Nhanh

- [ ] Website load được: `https://tbqc-production.up.railway.app`
- [ ] `/api/health` trả về `"database": "connected"`
- [ ] Environment variables đã được set (nếu cần)
- [ ] Database đã được import (nếu cần)
- [ ] `/api/persons` trả về data
- [ ] `/api/members` trả về data
- [ ] Website hiển thị đầy đủ

---

## 🆘 Cần Hỗ Trợ?

Nếu vẫn không fix được:
1. Copy logs từ Railway
2. Copy response từ `/api/health`
3. Mô tả lỗi cụ thể
