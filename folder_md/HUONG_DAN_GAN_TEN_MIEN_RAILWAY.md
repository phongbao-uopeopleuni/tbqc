# Hướng Dẫn Gắn Tên Miền Lên Railway

## 📋 Thông tin tên miền
- **Tên miền:** `phongtuybienquancong.info`
- **Nhà đăng ký:** GMO-Z.com Runsystem
- **Name Servers (NS):** 
  - `ns-a1.tenten.vn` (137.59.104.65)
  - `ns-a2.tenten.vn` (137.59.104.66)
  - `ns-a3.tenten.vn` (150.95.111.47)

### ⚠️ Lưu ý về Name Servers (NS)
**Name Servers (NS) là gì?**
- Name Servers là các máy chủ quản lý DNS cho domain của bạn
- Chúng chỉ định **ai** sẽ quản lý các DNS records (A, CNAME, MX, etc.)
- Trong trường hợp này, **Tenten.vn đang quản lý DNS** cho domain của bạn

**Khi nào cần thay đổi NS?**
- **KHÔNG CẦN** thay đổi nếu bạn đang dùng Tenten.vn để quản lý DNS (như hiện tại)
- **CHỈ CẦN** thay đổi nếu bạn muốn dùng DNS của nhà cung cấp khác (ví dụ: Cloudflare, AWS Route 53)

**Với Railway:**
- Railway **KHÔNG** yêu cầu thay đổi NS
- Bạn chỉ cần thêm **A record** hoặc **CNAME record** trên Tenten.vn (như đã làm)
- Name Servers giữ nguyên như hiện tại

## 📋 Thông tin DNS từ Railway
- **Type:** CNAME (hoặc A record)
- **Name:** @
- **Value:** `[CNAME từ Railway Dashboard]` hoặc `[IP address từ Railway]`
- **Lưu ý:** Thông tin cụ thể sẽ được hiển thị trên Railway Dashboard khi bạn thêm custom domain

---

## 🚀 Các Bước Thực Hiện

### ⚠️ BƯỚC 0: Hoàn thành eKYC (Định danh điện tử) - BẮT BUỘC

**QUAN TRỌNG:** Trước khi cấu hình DNS, bạn **PHẢI** hoàn thành eKYC trên Tenten.vn.

1. **Truy cập:** https://hosotenmien.com
2. **Đăng nhập** bằng thông tin quản trị tên miền (thông tin đăng ký tên miền)
3. **Hoàn thành eKYC:**
   - Cập nhật hồ sơ cá nhân
   - Xác thực CCCD/Hộ chiếu
   - Upload các giấy tờ cần thiết
4. **Đợi phê duyệt:** Sau khi hoàn thành, đợi Tenten.vn phê duyệt (thường 1-2 ngày làm việc)
5. **Kiểm tra:** Sau khi được phê duyệt, bạn mới có thể cấu hình DNS/NS

**Lưu ý:** Không thể cấu hình DNS cho đến khi eKYC được phê duyệt!

---

### Bước 1: Cấu hình Custom Domain trên Railway

1. **Đăng nhập vào Railway Dashboard**
   - Truy cập: https://railway.app
   - Đăng nhập vào tài khoản của bạn

2. **Chọn Project và Service**
   - Chọn project chứa ứng dụng TBQC của bạn
   - Click vào service (thường là service chạy Flask app)

3. **Thêm Custom Domain**
   - Vào tab **Settings** của service
   - Scroll xuống phần **Domains**
   - Click **Generate Domain** (nếu chưa có) hoặc **Add Domain**
   - Nhập tên miền: `phongtuybienquancong.info`
   - Railway sẽ hiển thị thông tin DNS cần cấu hình

4. **Lấy thông tin DNS từ Railway**
   - Railway sẽ cung cấp:
     - **CNAME record** (ví dụ: `xxxxx.railway.app`)
     - Hoặc **A record** với IP address
   - **Lưu lại thông tin này** để cấu hình ở bước tiếp theo

---

### Bước 2: Cấu hình DNS trên Tenten.vn

1. **Đăng nhập vào Tenten.vn**
   - Truy cập: https://tenten.vn hoặc portal của GMO-Z.com Runsystem
   - Đăng nhập với tài khoản đã đăng ký tên miền

2. **Vào quản lý DNS**
   - Tìm phần **Quản lý DNS** hoặc **DNS Management**
   - Chọn tên miền `phongtuybienquancong.info`

3. **Thêm DNS Records**

   **Dùng CNAME (Railway đã cung cấp):**
   ```
   Type: CNAME
   Name: @ (hoặc để trống)
   Value: [CNAME từ Railway Dashboard, ví dụ: xxxxx.up.railway.app]
   TTL: 3600 (hoặc mặc định)
   ```
   
   **Lưu ý:** 
   - Name: `@` có nghĩa là root domain (phongtuybienquancong.info)
   - Nếu không nhập được `@`, có thể để trống hoặc nhập `phongtuybienquancong.info`

   **Option 2: Dùng A Record (nếu Railway cung cấp IP)**
   ```
   Type: A
   Name: @ (hoặc để trống)
   Value: [IP address từ Railway]
   TTL: 3600 (hoặc mặc định)
   ```

   **Thêm www subdomain (tùy chọn):**
   ```
   Type: CNAME
   Name: www
   Value: [CNAME từ Railway Dashboard, giống như trên]
   TTL: 3600
   ```

4. **Lưu cấu hình**
   - Click **Save** hoặc **Lưu**
   - Đợi vài phút để DNS propagate

---

### Bước 3: Xác minh trên Railway

1. **Quay lại Railway Dashboard**
   - Vào phần **Settings > Domains**
   - Railway sẽ tự động kiểm tra DNS
   - Đợi trạng thái chuyển sang **Active** hoặc **Verified**

2. **Kiểm tra SSL Certificate**
   - Railway tự động cấp SSL certificate (Let's Encrypt)
   - Đợi vài phút để certificate được cấp
   - Trạng thái sẽ hiển thị **Active** khi hoàn tất

---

### Bước 4: Kiểm tra kết nối

1. **Test DNS propagation**
   ```bash
   # Kiểm tra DNS record
   nslookup phongtuybienquancong.info
   
   # Hoặc dùng dig
   dig phongtuybienquancong.info
   ```

2. **Test website**
   - Mở trình duyệt
   - Truy cập: `https://phongtuybienquancong.info`
   - Kiểm tra xem website có load được không
   - Kiểm tra SSL certificate (ổ khóa xanh)

---

## ⚙️ Cấu hình bổ sung (nếu cần)

### Redirect www về non-www (hoặc ngược lại)

Nếu muốn redirect `www.phongtuybienquancong.info` → `phongtuybienquancong.info`:

1. **Trên Railway:**
   - Thêm cả 2 domains: `phongtuybienquancong.info` và `www.phongtuybienquancong.info`
   - Cấu hình redirect trong code (Flask)

2. **Trong app.py:**
   ```python
   @app.before_request
   def redirect_www():
       if request.host.startswith('www.'):
           return redirect(request.url.replace('www.', '', 1), code=301)
   ```

### Cấu hình Environment Variables

Đảm bảo các biến môi trường đã được cấu hình đúng trên Railway:
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `SECRET_KEY`
- Các biến khác cần thiết

---

## 🔍 Troubleshooting

### DNS chưa propagate
- **Vấn đề:** DNS chưa cập nhật sau 24-48 giờ
- **Giải pháp:**
  - Kiểm tra lại cấu hình DNS trên Tenten.vn
  - Đảm bảo TTL không quá cao (nên để 3600)
  - Xóa cache DNS: `ipconfig /flushdns` (Windows) hoặc `sudo dscacheutil -flushcache` (Mac)

### Railway không verify được domain
- **Vấn đề:** Railway không thể verify domain
- **Giải pháp:**
  - Kiểm tra DNS record đã được tạo đúng chưa
  - Đảm bảo CNAME/A record trỏ đúng về Railway
  - Đợi thêm thời gian để DNS propagate

### SSL Certificate không được cấp
- **Vấn đề:** HTTPS không hoạt động
- **Giải pháp:**
  - Đảm bảo domain đã được verify trên Railway
  - Đợi vài phút để Let's Encrypt cấp certificate
  - Kiểm tra logs trên Railway để xem lỗi

### Website không load
- **Vấn đề:** Truy cập domain nhưng không thấy website
- **Giải pháp:**
  - Kiểm tra service có đang chạy không trên Railway
  - Kiểm tra logs để xem lỗi
  - Đảm bảo port đúng (Railway tự động map port)

---

## 📝 Checklist

- [ ] **Đã hoàn thành eKYC trên hosotenmien.com** ⚠️ BẮT BUỘC
- [ ] **Đã được Tenten.vn phê duyệt eKYC** ⚠️ BẮT BUỘC
- [ ] Đã thêm custom domain trên Railway
- [ ] Đã lấy thông tin DNS từ Railway Dashboard
- [ ] Đã cấu hình DNS record trên Tenten.vn
- [ ] Đã đợi DNS propagate (có thể mất 5-30 phút)
- [ ] Railway đã verify domain thành công
- [ ] SSL certificate đã được cấp
- [ ] Website có thể truy cập qua `https://phongtuybienquancong.info`
- [ ] Đã test cả www và non-www (nếu cấu hình)

---

## 🔗 Tài liệu tham khảo

- Railway Custom Domains: https://docs.railway.app/deploy/custom-domains
- Tenten.vn DNS Management: https://tenten.vn
- GMO-Z.com Runsystem: https://www.gmo-z.com/runsystem/

---

## 💡 Lưu ý

1. **DNS Propagation:** Thường mất 5-30 phút, nhưng có thể lên đến 48 giờ
2. **SSL Certificate:** Railway tự động cấp, thường mất 5-10 phút sau khi domain được verify
3. **Backup:** Luôn giữ backup thông tin DNS cũ trước khi thay đổi
4. **Monitoring:** Theo dõi logs trên Railway để phát hiện lỗi sớm

---

**Chúc bạn thành công! 🎉**

