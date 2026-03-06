## Hướng dẫn cho Debugger (không commit mật khẩu)

Dự án này **không lưu** username/password/server thật trong Git. Tất cả thông tin nhạy cảm được nạp từ **biến môi trường** hoặc file local (ví dụ `.env`, `tbqc_db.env`) vốn đã được `.gitignore`.

Mục tiêu của tài liệu này là giúp debugger đọc code và hiểu “secret đi vào hệ thống như thế nào” mà không cần thấy giá trị thật.

### 1) Các nhóm cấu hình chính

- **Kết nối Database**
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - Code lấy từ env (hoặc biến tương đương `MYSQL*` tùy nền tảng).

- **Flask session/cookie**
  - `SECRET_KEY` (bắt buộc trên production)
  - `COOKIE_DOMAIN` (production, dùng chung cho domain và www)

- **Auth/Password nội bộ**
  - `MEMBERS_PASSWORD`, `ADMIN_PASSWORD`, `BACKUP_PASSWORD`
  - `ALBUM_PASSWORD` (tuỳ chọn)
  - `GRAVE_IMAGE_DELETE_PASSWORD` (tuỳ chọn)
  - `MEMBERS_FIXED_ACCOUNTS` (tuỳ chọn): danh sách user/pass cố định cho cổng Members
    - Format: `user1:pass1,user2:pass2`

- **Passphrase mở trang Gia phả**
  - `GENEALOGY_PASSPHRASES` (phân cách bằng dấu phẩy)
    - Ví dụ: `phrase1,phrase2,phrase3`

### 2) Điểm vào (entrypoint)

- Chạy ứng dụng từ `app.py` (thư mục gốc repo). Blueprints được đăng ký từ đây.

### 3) Luồng bảo vệ trang Gia phả (passphrase)

- Frontend (`templates/genealogy.html`) gọi API:
  - `POST /api/genealogy/verify-passphrase` với JSON `{ "passphrase": "..." }`
- Backend (`blueprints/main.py`) kiểm tra passphrase dựa trên env `GENEALOGY_PASSPHRASES`.

### 4) Gợi ý cách set env khi debug

- Tạo file `.env` local dựa trên `.env.example` và điền giá trị thật.
- Hoặc cấu hình “Environment variables” ngay trong IDE/debugger profile (khuyến nghị nếu không muốn tạo file).

