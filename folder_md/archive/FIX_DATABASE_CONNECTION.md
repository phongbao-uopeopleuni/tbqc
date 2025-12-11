# 🔧 Hướng Dẫn Fix Lỗi "Chưa Load Được Data"

## Vấn Đề

Sau khi deploy lên hosting, website chạy được nhưng không load được data từ database.

## Nguyên Nhân Có Thể

1. **Database chưa được import** (phổ biến nhất)
2. **Environment variables chưa được cấu hình đúng**
3. **Database connection string sai**
4. **Database service chưa running**

---

## Bước 1: Kiểm Tra Health Check

Truy cập endpoint mới: `https://your-app.railway.app/api/health`

Endpoint này sẽ trả về:
- Trạng thái server
- Trạng thái database connection
- Database config đang được dùng
- Environment variables

**Nếu thấy:**
- `"database": "connection_failed"` → Database chưa kết nối được
- `"database": "connected"` → Database OK, có thể là data chưa import

---

## Bước 2: Kiểm Tra Environment Variables

### Trên Railway.app:

1. Vào **Web Service** → **Variables** tab
2. Đảm bảo có các biến sau:
   ```
   DB_HOST=<từ MySQL service>
   DB_NAME=<từ MySQL service>
   DB_USER=<từ MySQL service>
   DB_PASSWORD=<từ MySQL service>
   DB_PORT=<từ MySQL service>
   SECRET_KEY=<random string>
   ```

3. **Cách lấy giá trị:**
   - Vào **MySQL Service** → **Variables** tab
   - Copy các giá trị:
     - `MYSQLHOST` → paste vào `DB_HOST`
     - `MYSQLDATABASE` → paste vào `DB_NAME`
     - `MYSQLUSER` → paste vào `DB_USER`
     - `MYSQLPASSWORD` → paste vào `DB_PASSWORD`
     - `MYSQLPORT` → paste vào `DB_PORT`

4. **Lưu ý:** Railway có thể dùng tên biến khác, kiểm tra trong Variables tab của MySQL service

---

## Bước 3: Import Database

### Cách 1: Dùng MySQL Workbench (Dễ nhất)

1. **Export từ local:**
   ```bash
   mysqldump -u tbqc_admin -p tbqc2025 > backup.sql
   ```

2. **Lấy connection info từ Railway:**
   - Vào MySQL service → **Connect** tab
   - Copy "Public Network" connection string
   - Hoặc dùng thông tin từ Variables tab

3. **Import vào Railway MySQL:**
   - Mở MySQL Workbench
   - Tạo connection mới với thông tin từ Railway
   - Connect
   - File → Run SQL Script → chọn `backup.sql`
   - Execute

### Cách 2: Dùng Command Line

1. **Export từ local:**
   ```bash
   mysqldump -u tbqc_admin -p tbqc2025 > backup.sql
   ```

2. **Import vào Railway:**
   ```bash
   # Lấy connection string từ Railway MySQL service
   mysql -h <MYSQLHOST> -P <MYSQLPORT> -u <MYSQLUSER> -p <MYSQLDATABASE> < backup.sql
   ```

### Cách 3: Dùng Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

2. **Connect và import:**
   ```bash
   railway link
   railway connect mysql
   mysql -u <user> -p < backup.sql
   ```

---

## Bước 4: Kiểm Tra Logs

### Trên Railway.app:

1. Vào **Web Service** → **Deployments** tab
2. Click vào deployment mới nhất
3. Xem **Logs** tab

**Tìm các dòng:**
- `🔌 Đang kết nối database với config:` → Xem config có đúng không
- `✅ Kết nối database thành công!` → Database OK
- `❌ Lỗi kết nối database:` → Có lỗi, xem chi tiết

---

## Bước 5: Test API Endpoints

Sau khi import database, test các endpoint:

1. **Test health:**
   ```
   https://your-app.railway.app/api/health
   ```

2. **Test lấy persons:**
   ```
   https://your-app.railway.app/api/persons
   ```

3. **Test lấy members:**
   ```
   https://your-app.railway.app/api/members
   ```

4. **Test stats:**
   ```
   https://your-app.railway.app/api/stats/members
   ```

**Nếu trả về data → OK!**
**Nếu trả về lỗi → Xem error message**

---

## Lỗi Thường Gặp

### 1. "Cannot connect to database"

**Nguyên nhân:**
- Environment variables chưa set
- Database service chưa running
- Connection string sai

**Fix:**
- Kiểm tra environment variables
- Đảm bảo MySQL service đang running (green status)
- Kiểm tra `/api/health` để xem config

### 2. "Table doesn't exist"

**Nguyên nhân:**
- Database chưa được import
- Schema chưa được tạo

**Fix:**
- Import database từ local
- Hoặc chạy SQL scripts trong `folder_sql/`

### 3. "Access denied"

**Nguyên nhân:**
- Username/password sai
- User không có quyền

**Fix:**
- Kiểm tra environment variables
- Đảm bảo dùng đúng user từ MySQL service

### 4. "Empty result" (không có data)

**Nguyên nhân:**
- Database đã kết nối nhưng chưa có data
- Data chưa được import

**Fix:**
- Import data từ local MySQL
- Kiểm tra tables có data không: `SELECT COUNT(*) FROM persons;`

---

## Checklist

- [ ] Environment variables đã được set đúng
- [ ] MySQL service đang running (green status)
- [ ] Database đã được import (có tables và data)
- [ ] `/api/health` trả về `"database": "connected"`
- [ ] `/api/persons` trả về data (không phải empty array)
- [ ] Logs không có lỗi database connection

---

## Debug Nhanh

1. **Kiểm tra health:**
   ```bash
   curl https://your-app.railway.app/api/health
   ```

2. **Xem logs trên Railway:**
   - Web Service → Deployments → Logs

3. **Test connection local:**
   - Dùng MySQL Workbench connect vào Railway database
   - Kiểm tra có tables và data không

---

## Cần Hỗ Trợ Thêm?

Nếu vẫn gặp vấn đề:
1. Copy logs từ Railway
2. Copy response từ `/api/health`
3. Mô tả lỗi cụ thể
