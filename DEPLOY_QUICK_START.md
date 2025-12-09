# 🚀 Quick Start: Deploy Lên Railway.app (5 Phút)

## Bước 1: Push Code Lên GitHub (2 phút)

```bash
# Nếu chưa có git repo
git init
git add .
git commit -m "Ready for deployment"
git branch -M main

# Tạo repo trên GitHub, sau đó:
git remote add origin https://github.com/YOUR_USERNAME/tbqc-giapha.git
git push -u origin main
```

## Bước 2: Tạo Tài Khoản Railway (1 phút)

1. Vào https://railway.app
2. Click "Login with GitHub"
3. Authorize Railway

## Bước 3: Deploy (2 phút)

1. **Tạo Project:**
   - Click "New Project"
   - Chọn "Deploy from GitHub repo"
   - Chọn repository của bạn

2. **Thêm MySQL Database:**
   - Trong project, click "New" → "Database" → "MySQL"
   - Railway tự động tạo và cung cấp connection info

3. **Cấu Hình Web Service:**
   - Railway tự động detect Flask app
   - Vào Web service → Settings → Generate Domain
   - Copy domain (ví dụ: `tbqc-giapha.railway.app`)

4. **Setup Environment Variables:**
   - Vào MySQL service → Variables tab
   - Copy: `MYSQLHOST`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLPORT`, `MYSQLDATABASE`
   
   - Vào Web service → Variables tab, thêm:
     ```
     DB_HOST=<paste MYSQLHOST>
     DB_NAME=<paste MYSQLDATABASE>
     DB_USER=<paste MYSQLUSER>
     DB_PASSWORD=<paste MYSQLPASSWORD>
     DB_PORT=<paste MYSQLPORT>
     SECRET_KEY=<random string, ví dụ: abc123xyz789>
     ```

5. **Import Database:**
   - Export từ local: `mysqldump -u tbqc_admin -p tbqc2025 > backup.sql`
   - Import vào Railway MySQL (dùng MySQL Workbench hoặc command line)

6. **Deploy:**
   - Railway tự động deploy khi push code
   - Hoặc click "Deploy" button

## ✅ Xong!

Truy cập: `https://your-app.railway.app`

---

## 🔧 Nếu Gặp Lỗi

**"Cannot connect to database"**
- Kiểm tra environment variables đã đúng chưa
- Đảm bảo MySQL service đang running (green status)

**"Module not found"**
- Railway tự động install từ `requirements.txt`
- Kiểm tra file `requirements.txt` đã có đủ packages

**"Port error"**
- Code đã được fix để đọc PORT từ environment
- Railway tự động set PORT

---

## 💡 Tips

- Railway free tier: $5 credit/tháng (đủ cho dự án nhỏ)
- Có thể setup custom domain miễn phí
- Auto-deploy khi push code lên GitHub
- Có thể scale lên paid plan sau này

---

## 📞 Cần Hỗ Trợ?

Xem file `HUONG_DAN_DEPLOY.md` để biết chi tiết hơn.
