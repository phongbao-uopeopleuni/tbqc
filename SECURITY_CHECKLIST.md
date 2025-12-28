# Security Checklist - Thông Tin Nhạy Cảm

## ⚠️ QUAN TRỌNG: Không được commit các thông tin sau lên GitHub

### 🔒 Thông tin BẮT BUỘC phải được ignore:

1. **Database Credentials:**
   - ✅ `tbqc_db.env` - File chứa DB_HOST, DB_PORT, DB_USER, DB_PASSWORD
   - ✅ Các file `.env` khác
   - ✅ Thông tin kết nối database trong code (nếu hardcode)

2. **API Keys & Tokens:**
   - ✅ Facebook Access Token
   - ✅ SMTP credentials
   - ✅ Secret keys
   - ✅ API keys

3. **Domain & Server Configuration:**
   - ✅ Railway deployment URLs (có thể thay đổi)
   - ✅ IP addresses của servers
   - ✅ Domain configuration files

4. **Personal Information:**
   - ✅ CCCD/Passport numbers
   - ✅ Email addresses cá nhân
   - ✅ Phone numbers
   - ✅ Địa chỉ nhà riêng

5. **Backup Files:**
   - ✅ SQL dump files trong `backups/`
   - ✅ Database backup files

### ✅ Đã được bảo vệ trong .gitignore:

- `*.env` - Tất cả file .env
- `tbqc_db.env` - File config database
- `backups/` - Thư mục backup
- `*.sql` - SQL files (trừ folder_sql/*.sql)
- `.smtp_config` - SMTP config

### 📝 Files cần kiểm tra trước khi commit:

1. **Markdown files** - Đảm bảo không có:
   - Database passwords
   - API keys
   - Personal information
   - Real IP addresses

2. **Code files** - Đảm bảo không có:
   - Hardcoded passwords
   - API keys trong code
   - Database credentials

3. **Config files** - Đảm bảo:
   - Sử dụng environment variables
   - Không commit file config thực tế

### 🔍 Cách kiểm tra trước khi commit:

```bash
# Kiểm tra xem file nhạy cảm có được track không
git ls-files | grep -E "\.env|password|secret|config"

# Kiểm tra nội dung có chứa thông tin nhạy cảm
git diff --cached | grep -i "password\|secret\|token\|key"

# Kiểm tra file có được ignore đúng không
git check-ignore -v tbqc_db.env
```

### 🚨 Nếu đã commit nhầm thông tin nhạy cảm:

1. **Xóa khỏi git tracking:**
   ```bash
   git rm --cached tbqc_db.env
   ```

2. **Thêm vào .gitignore:**
   - Đảm bảo file đã có trong .gitignore

3. **Commit lại:**
   ```bash
   git add .gitignore
   git commit -m "Remove sensitive file from tracking"
   ```

4. **Nếu đã push lên GitHub:**
   - Cần thay đổi password/credentials ngay lập tức
   - Xem xét sử dụng GitHub's secret scanning
   - Rotate tất cả keys/tokens đã bị lộ

### ✅ Best Practices:

1. **Luôn dùng environment variables:**
   - Không hardcode credentials trong code
   - Sử dụng `.env` files (đã ignore)

2. **Sử dụng .env.example:**
   - Tạo file `.env.example` với format mẫu (không có giá trị thực)
   - Commit `.env.example` để người khác biết cần config gì

3. **Review code trước khi commit:**
   - Kiểm tra `git diff` trước khi commit
   - Không commit file config thực tế

4. **Sử dụng secrets management:**
   - Railway: Environment Variables
   - GitHub: Secrets (cho CI/CD)
   - Local: .env files (đã ignore)

---

**Lưu ý:** File này có thể được commit vì chỉ chứa hướng dẫn, không có thông tin nhạy cảm thực tế.

