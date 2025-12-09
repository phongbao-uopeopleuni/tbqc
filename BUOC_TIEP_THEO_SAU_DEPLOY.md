# 🎯 Các Bước Tiếp Theo Sau Khi Deploy

## ✅ Bạn Đã Hoàn Thành:
- ✅ Code đã push lên GitHub
- ✅ Railway project đã tạo
- ✅ MySQL database đã deploy
- ✅ Web service đã có URL: `tbqc-production.up.railway.app`

---

## 📋 Checklist Các Bước Tiếp Theo

### Bước 1: Kiểm Tra Website Có Chạy Không ⚡

1. **Truy cập website:**
   ```
   https://tbqc-production.up.railway.app
   ```

2. **Kiểm tra:**
   - [ ] Website có load được không?
   - [ ] Có hiển thị giao diện không?
   - [ ] Có lỗi 500/404 không?

**Nếu website không load:**
- Vào Railway → `tbqc` service → Logs tab
- Xem lỗi và fix theo hướng dẫn bên dưới

---

### Bước 2: Kiểm Tra Database Connection 🔌

1. **Truy cập health check endpoint:**
   ```
   https://tbqc-production.up.railway.app/api/health
   ```

2. **Kiểm tra response:**
   ```json
   {
     "server": "ok",
     "database": "connected",  // ← Phải là "connected"
     "db_config": {...},
     "env_vars": {...}
   }
   ```

**Nếu `"database": "connection_failed"`:**
- Xem phần "Fix Database Connection" bên dưới

---

### Bước 3: Kiểm Tra Environment Variables 🔧

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Variables**

2. **Đảm bảo có các biến sau:**
   ```
   DB_HOST=<từ MySQL service>
   DB_NAME=<từ MySQL service>
   DB_USER=<từ MySQL service>
   DB_PASSWORD=<từ MySQL service>
   DB_PORT=<từ MySQL service>
   SECRET_KEY=<random string>
   ```

3. **Cách lấy giá trị từ MySQL service:**
   - Click vào **MySQL** service
   - Vào tab **Variables**
   - Copy các giá trị:
     - `MYSQLHOST` → paste vào `DB_HOST` trong web service
     - `MYSQLDATABASE` → paste vào `DB_NAME`
     - `MYSQLUSER` → paste vào `DB_USER`
     - `MYSQLPASSWORD` → paste vào `DB_PASSWORD`
     - `MYSQLPORT` → paste vào `DB_PORT`

4. **Lưu ý:** Railway có thể tự động link, nhưng nên kiểm tra lại

---

### Bước 4: Import Database 📥

**Nếu `/api/health` trả về `"database": "connected"` nhưng không có data:**

1. **Export database từ local:**
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

### Bước 5: Test API Endpoints 🧪

Sau khi import database, test các endpoint:

1. **Test health:**
   ```
   https://tbqc-production.up.railway.app/api/health
   ```
   → Phải trả về `"database": "connected"`

2. **Test lấy persons:**
   ```
   https://tbqc-production.up.railway.app/api/persons
   ```
   → Phải trả về array có data (không phải `[]`)

3. **Test lấy members:**
   ```
   https://tbqc-production.up.railway.app/api/members
   ```
   → Phải trả về `{"success": true, "data": [...]}`

4. **Test stats:**
   ```
   https://tbqc-production.up.railway.app/api/stats/members
   ```
   → Phải trả về số liệu thống kê

---

### Bước 6: Kiểm Tra Website Hoạt Động Đầy Đủ 🌐

1. **Trang chủ:**
   ```
   https://tbqc-production.up.railway.app
   ```
   - [ ] Cây gia phả có hiển thị không?
   - [ ] Activities preview có load không?
   - [ ] Stats section có hiển thị số liệu không?

2. **Trang thành viên:**
   ```
   https://tbqc-production.up.railway.app/members
   ```
   - [ ] Bảng thành viên có load được không?
   - [ ] Có hiển thị data không?

3. **Trang hoạt động:**
   ```
   https://tbqc-production.up.railway.app/activities
   ```
   - [ ] Có hiển thị danh sách activities không?

---

### Bước 7: Kiểm Tra Logs Nếu Có Lỗi 📊

1. **Vào Railway Dashboard:**
   - Click vào `tbqc` service
   - Vào tab **Deployments**
   - Click vào deployment mới nhất
   - Xem tab **Logs**

2. **Tìm các dòng:**
   - `🔌 Đang kết nối database với config:` → Xem config
   - `✅ Kết nối database thành công!` → Database OK
   - `❌ Lỗi kết nối database:` → Có lỗi, cần fix
   - `📥 API /api/persons được gọi` → API đang được gọi

---

## 🔧 Fix Các Lỗi Thường Gặp

### Lỗi 1: "Build failed"

**Nguyên nhân:**
- Thiếu dependencies trong `requirements.txt`
- Lỗi syntax trong code
- `Procfile` hoặc start command sai

**Fix:**
1. Xem logs trong Railway → Deployments → Logs
2. Tìm dòng lỗi cụ thể
3. Fix và push lại code

### Lỗi 2: "Cannot connect to database"

**Nguyên nhân:**
- Environment variables chưa set
- Database service chưa running
- Connection string sai

**Fix:**
1. Kiểm tra environment variables (Bước 3)
2. Đảm bảo MySQL service đang running (green status)
3. Kiểm tra `/api/health` để xem config

### Lỗi 3: "Table doesn't exist"

**Nguyên nhân:**
- Database chưa được import
- Schema chưa được tạo

**Fix:**
- Import database (Bước 4)

### Lỗi 4: "Empty result" (không có data)

**Nguyên nhân:**
- Database đã kết nối nhưng chưa có data
- Data chưa được import

**Fix:**
- Import database (Bước 4)

---

## ✅ Checklist Cuối Cùng

- [ ] Website load được: `https://tbqc-production.up.railway.app`
- [ ] `/api/health` trả về `"database": "connected"`
- [ ] Environment variables đã được set đúng
- [ ] Database đã được import (có data)
- [ ] `/api/persons` trả về data
- [ ] `/api/members` trả về data
- [ ] Trang chủ hiển thị đầy đủ
- [ ] Trang thành viên load được data
- [ ] Logs không có lỗi

---

## 🎉 Hoàn Thành!

Khi tất cả checklist đều ✅, website của bạn đã sẵn sàng!

**URL của bạn:**
- Website: `https://tbqc-production.up.railway.app`
- API Health: `https://tbqc-production.up.railway.app/api/health`

---

## 📞 Cần Hỗ Trợ?

Nếu gặp vấn đề:
1. Xem logs trong Railway
2. Test `/api/health` endpoint
3. Kiểm tra file `FIX_DATABASE_CONNECTION.md` để biết chi tiết
