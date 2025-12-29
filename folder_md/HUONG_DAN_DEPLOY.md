# Hướng Dẫn Deploy Dự Án Lên Hosting Miễn Phí

## Tổng Quan

Dự án này là một ứng dụng Flask (Python) với MySQL database. Có thể deploy lên các nền tảng miễn phí sau:

### Các Lựa Chọn Hosting Miễn Phí:

1. **Render.com** ⭐ (Khuyến nghị)
   - Free tier: 750 giờ/tháng
   - Hỗ trợ MySQL database
   - Dễ cấu hình
   - Tự động deploy từ GitHub

2. **Railway.app**
   - Free tier: $5 credit/tháng
   - Hỗ trợ MySQL
   - Dễ dùng

3. **PythonAnywhere**
   - Free tier: 1 web app
   - Hỗ trợ MySQL
   - Giới hạn truy cập từ IP ngoài

4. **Fly.io**
   - Free tier: 3 VMs
   - Cần cấu hình phức tạp hơn

---

## Hướng Dẫn Deploy Lên Render.com (Khuyến Nghị)

### Bước 1: Chuẩn Bị Code

1. **Đảm bảo có file cần thiết:**
   - ✅ `requirements.txt` (đã có)
   - ✅ `Procfile` (đã tạo)
   - ✅ `runtime.txt` (đã tạo)
   - ✅ `render.yaml` (đã tạo - tùy chọn)

2. **Cập nhật cấu hình database trong `folder_py/app.py`:**
   
   File đã được cấu hình để đọc từ biến môi trường. Đảm bảo code như sau:

   ```python
   DB_CONFIG = {
       'host': os.environ.get('DB_HOST', 'localhost'),
       'database': os.environ.get('DB_NAME', 'your_database_name'),
       'user': os.environ.get('DB_USER', 'your_database_user'),
       'password': os.environ.get('DB_PASSWORD', 'your_database_password'),
       'charset': 'utf8mb4',
       'collation': 'utf8mb4_unicode_ci'
   }
   ```

### Bước 2: Đẩy Code Lên GitHub

1. **Tạo repository trên GitHub:**
   - Vào https://github.com
   - Tạo repository mới (ví dụ: `tbqc-giapha`)

2. **Đẩy code lên GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/tbqc-giapha.git
   git push -u origin main
   ```

### Bước 3: Tạo Tài Khoản Render.com

1. Vào https://render.com
2. Đăng ký bằng GitHub account (dễ nhất)
3. Xác thực email

### Bước 4: Tạo Database trên Render

1. **Tạo PostgreSQL Database (Render không có MySQL free, dùng PostgreSQL):**
   - Vào Dashboard → New → PostgreSQL
   - Name: `tbqc-db`
   - Database: `your_database_name` (thay bằng tên database thực tế)
   - User: `tbqc_admin`
   - Plan: **Free**
   - Region: Chọn gần nhất (Singapore hoặc Oregon)
   - Click "Create Database"

2. **Lưu thông tin kết nối:**
   - Internal Database URL (sẽ dùng cho web service)
   - External Database URL (để import data từ local)

### Bước 5: Tạo Web Service

1. **Tạo Web Service:**
   - Vào Dashboard → New → Web Service
   - Connect repository: Chọn repo GitHub của bạn
   - Name: `tbqc-giapha`
   - Environment: **Python 3**
   - Region: Cùng region với database
   - Branch: `main`
   - Root Directory: (để trống)
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd folder_py && python app.py`

2. **Cấu hình Environment Variables:**
   - Vào tab "Environment"
   - Thêm các biến sau:
     ```
     SECRET_KEY=<tạo random string>
     DB_HOST=<từ database service>
     DB_NAME=your_database_name
     DB_USER=your_database_user
     DB_PASSWORD=<từ database service>
    DB_PORT=5432
    
    # ⚠️ QUAN TRỌNG: Thêm các biến sau cho Members page password protection
    # Thay <your_password_here> bằng mật khẩu thực tế của bạn (ví dụ: tbqc@2026)
    MEMBERS_PASSWORD=<your_password_here>
    ADMIN_PASSWORD=<your_password_here>
    BACKUP_PASSWORD=<your_password_here>
    ```
   - **Lưu ý:** Render dùng PostgreSQL, cần cập nhật code để dùng `psycopg2` thay vì `mysql-connector-python`

### Bước 6: Cập Nhật Code Cho PostgreSQL

**Quan trọng:** Render.com free tier chỉ có PostgreSQL, không có MySQL. Cần cập nhật:

1. **Cập nhật `requirements.txt`:**
   ```
   flask==3.0.0
   flask-cors==4.0.0
   psycopg2-binary==2.9.9
   bcrypt==4.1.2
   flask-login==0.6.3
   ```

2. **Cập nhật `folder_py/app.py`:**
   - Thay `mysql.connector` bằng `psycopg2`
   - Cập nhật cú pháp SQL cho PostgreSQL

### Bước 7: Import Database

1. **Export database từ local MySQL:**
   ```bash
   mysqldump -u your_db_user -p your_database_name > database_backup.sql
   ```

2. **Convert sang PostgreSQL format** (dùng tool online hoặc script)

3. **Import vào Render PostgreSQL:**
   - Dùng pgAdmin hoặc psql command line
   - Hoặc dùng Render Dashboard → Database → Connect → External Connection

---

## Lựa Chọn 2: Railway.app (Có MySQL)

Railway.app hỗ trợ MySQL tốt hơn và có free tier $5/tháng.

### Bước 1: Tạo Tài Khoản Railway

1. Vào https://railway.app
2. Đăng ký bằng GitHub

### Bước 2: Tạo Project

1. New Project → Deploy from GitHub repo
2. Chọn repository của bạn

### Bước 3: Thêm MySQL Database

1. New → Database → MySQL
2. Railway tự động tạo và cung cấp connection string

### Bước 4: Cấu Hình Web Service

1. Railway tự detect Flask app
2. Cập nhật Environment Variables:
   ```
   DB_HOST=<từ MySQL service>
   DB_NAME=your_database_name
   DB_USER=your_database_user
   DB_PASSWORD=<từ MySQL service>
   DB_PORT=3306
   
   # ⚠️ QUAN TRỌNG: Thêm các biến sau cho Members page password protection
   # Thay <your_password_here> bằng mật khẩu thực tế của bạn (ví dụ: tbqc@2026)
   MEMBERS_PASSWORD=<your_password_here>
   ADMIN_PASSWORD=<your_password_here>
   BACKUP_PASSWORD=<your_password_here>
   ```

3. Deploy tự động!

---

## Lựa Chọn 3: PythonAnywhere (Đơn Giản Nhất)

### Bước 1: Tạo Tài Khoản

1. Vào https://www.pythonanywhere.com
2. Đăng ký free account

### Bước 2: Upload Code

1. Vào Files tab
2. Upload toàn bộ project
3. Hoặc clone từ GitHub

### Bước 3: Cấu Hình Web App

1. Vào Web tab
2. Add a new web app → Flask
3. Chọn Python version
4. Chọn path: `folder_py/app.py`

### Bước 4: Cấu Hình Database

1. Vào Databases tab
2. Tạo MySQL database
3. Cập nhật DB_CONFIG trong code

### Bước 5: Reload Web App

1. Vào Web tab
2. Click "Reload"

---

## Checklist Trước Khi Deploy

- [ ] Code đã được commit và push lên GitHub
- [ ] `requirements.txt` đã cập nhật đầy đủ
- [ ] `Procfile` hoặc start command đã đúng
- [ ] Environment variables đã được cấu hình
- [ ] Database connection đã được test
- [ ] Static files (HTML, CSS, JS) đã được include
- [ ] SMTP config (nếu cần) đã được setup

---

## Troubleshooting

### Lỗi: "Module not found"
- Kiểm tra `requirements.txt` đã có đủ packages
- Chạy `pip install -r requirements.txt` local để test

### Lỗi: "Database connection failed"
- Kiểm tra environment variables
- Kiểm tra database service đã running
- Kiểm tra firewall/network settings

### Lỗi: "Static files not found"
- Kiểm tra `BASE_DIR` trong `app.py`
- Đảm bảo HTML files ở root directory

### Lỗi: "Port already in use"
- Render/Railway tự động assign port
- Đảm bảo code đọc `PORT` từ environment: `port = int(os.environ.get('PORT', 5000))`

---

## Khuyến Nghị

**Cho dự án này, tôi khuyến nghị Railway.app vì:**
- ✅ Hỗ trợ MySQL (không cần convert sang PostgreSQL)
- ✅ Free tier $5/tháng (đủ cho dự án nhỏ)
- ✅ Dễ cấu hình
- ✅ Auto-deploy từ GitHub
- ✅ Có thể scale lên sau này

**Nếu muốn đơn giản nhất:**
- PythonAnywhere (free tier, nhưng giới hạn)

**Nếu muốn free hoàn toàn:**
- Render.com (nhưng cần convert sang PostgreSQL)

---

## Liên Hệ Hỗ Trợ

Nếu gặp vấn đề khi deploy, vui lòng:
1. Kiểm tra logs trên hosting platform
2. Test code local trước
3. Kiểm tra database connection
4. Xem documentation của platform
