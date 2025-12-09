# 📁 Folder Images

Folder này chứa các file ảnh cho website.

## 🖼️ Ảnh cần có

### Ảnh Vua Minh Mạng
- **Tên file:** `vua-minh-mang.jpg` (hoặc `.png`)
- **Vị trí hiển thị:** Section "Giới Thiệu" (#about)
- **Kích thước khuyến nghị:** 
  - Chiều rộng: 400-600px
  - Tỷ lệ: 3:4 hoặc 4:5 (portrait)
  - Định dạng: JPG hoặc PNG
  - Dung lượng: < 500KB (để tải nhanh)

## 📝 Hướng dẫn thêm ảnh

1. **Đặt ảnh vào folder này:**
   - Tên file: `vua-minh-mang.jpg` (hoặc `.png`)
   - Đảm bảo tên file khớp với đường dẫn trong `index.html`

2. **Nếu dùng tên file khác:**
   - Mở file `index.html`
   - Tìm dòng: `<img src="/images/vua-minh-mang.jpg"`
   - Thay đổi tên file cho phù hợp

3. **Tối ưu ảnh:**
   - Nén ảnh để giảm dung lượng
   - Sử dụng JPG cho ảnh chân dung
   - Sử dụng PNG nếu cần độ trong suốt

## 🔗 Đường dẫn trong code

Ảnh được serve qua Flask route `/images/<filename>` trong `app.py`.

