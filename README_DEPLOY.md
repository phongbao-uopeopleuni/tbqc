# 🚀 Hướng Dẫn Deploy Nhanh

## ⚡ Deploy Lên Railway.app (Khuyến Nghị - Có MySQL Free)

### 1. Chuẩn Bị
- Đảm bảo code đã push lên GitHub
- Có tài khoản GitHub

### 2. Tạo Tài Khoản Railway
1. Vào https://railway.app
2. Đăng nhập bằng GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Chọn repository của bạn

### 3. Thêm MySQL Database
1. Trong project, click "New" → "Database" → "MySQL"
2. Railway tự động tạo database và cung cấp connection string

### 4. Cấu Hình Environment Variables
1. Vào MySQL service → Variables tab
2. Copy các giá trị: `MYSQLHOST`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLPORT`, `MYSQLDATABASE`

3. Vào Web service → Variables tab, thêm:
   ```
   DB_HOST=<MYSQLHOST>
   DB_NAME=<MYSQLDATABASE>
   DB_USER=<MYSQLUSER>
   DB_PASSWORD=<MYSQLPASSWORD>
   DB_PORT=<MYSQLPORT>
   SECRET_KEY=<random string>
   ```

### 5. Import Database
1. Export từ local MySQL:
   ```bash
   mysqldump -u tbqc_admin -p tbqc2025 > backup.sql
   ```

2. Import vào Railway MySQL (dùng MySQL client hoặc Railway CLI)

### 6. Deploy
- Railway tự động deploy khi bạn push code lên GitHub
- Hoặc click "Deploy" trong Railway dashboard

### 7. Truy Cập
- Railway cung cấp URL: `https://your-app.railway.app`
- Có thể setup custom domain miễn phí

---

## 📝 Lưu Ý Quan Trọng

1. **Port Configuration:**
   - Code đã được cập nhật để đọc `PORT` từ environment
   - Railway tự động set PORT

2. **Database:**
   - Railway MySQL free tier có giới hạn
   - Nên backup định kỳ

3. **Static Files:**
   - HTML/CSS/JS files phải ở root directory
   - Code đã cấu hình đúng `BASE_DIR`

4. **SMTP (Email):**
   - Cần setup biến môi trường hoặc file `.smtp_config`
   - Hoặc dùng service như SendGrid (free tier)

---

## 🔧 Troubleshooting

**Lỗi: "Cannot connect to database"**
- Kiểm tra environment variables
- Đảm bảo MySQL service đang running
- Kiểm tra network settings

**Lỗi: "Module not found"**
- Kiểm tra `requirements.txt`
- Railway tự động install từ requirements.txt

**Lỗi: "Port already in use"**
- Code đã fix, đọc PORT từ environment
- Railway tự động set PORT

---

## 📚 Tài Liệu Tham Khảo

- Railway Docs: https://docs.railway.app
- Flask Deployment: https://flask.palletsprojects.com/en/latest/deploying/
