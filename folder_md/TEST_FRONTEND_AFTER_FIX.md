# Hướng dẫn Test Frontend Sau Khi Sửa Null Check

## ✅ Đã hoàn thành

Tất cả các `addEventListener` và DOM operations đã được thêm null check để tránh lỗi "Cannot read properties of null".

## 🚀 Cách test

### Bước 1: Khởi động Server

```powershell
python app.py
```

**Hoặc:**
```powershell
python start_server.py
```

Đảm bảo server chạy trên `http://localhost:5000`

### Bước 2: Mở trình duyệt

Truy cập: `http://localhost:5000`

### Bước 3: Mở Developer Tools

Nhấn `F12` để mở Developer Tools, chuyển sang tab **Console**

### Bước 4: Test các tính năng

#### Test 1: Lineage Search
1. Scroll xuống phần "Tra cứu chuỗi phả hệ theo dòng cha"
2. Nhập tên vào ô "Tên (tìm kiếm thông minh)" (ví dụ: "Bảo Phong")
3. **Kiểm tra:**
   - [ ] Không có lỗi trong console
   - [ ] Suggestions hiển thị (nếu có)
   - [ ] Click vào suggestion hoạt động
   - [ ] Click vào button "🔍 Tìm chuỗi phả hệ" hoạt động

#### Test 2: Tree Search
1. Scroll lên phần "Cây Gia Phả Tương Tác"
2. Nhập tên vào ô "Vui lòng nhập tên cần tìm kiếm"
3. Click button "Tìm kiếm"
4. **Kiểm tra:**
   - [ ] Không có lỗi trong console
   - [ ] Kết quả tìm kiếm hiển thị
   - [ ] Click vào kết quả tìm kiếm hoạt động
   - [ ] Tree được load với person được chọn

#### Test 3: Tree View
1. Trong phần "Cây Gia Phả Tương Tác"
2. Click vào một person trong tree
3. **Kiểm tra:**
   - [ ] Panel "Thông tin chi tiết" hiển thị đúng
   - [ ] Không có lỗi trong console
   - [ ] Tất cả thông tin hiển thị đầy đủ

#### Test 4: Generation Filter
1. Trong phần "Cây Gia Phả Tương Tác"
2. Thay đổi dropdown "Hiển thị đến đời:"
3. **Kiểm tra:**
   - [ ] Tree được reload với generation mới
   - [ ] Không có lỗi trong console

#### Test 5: Mini Carousel (nếu có)
1. Scroll xuống phần có mini carousel (activities)
2. Click vào nút prev/next
3. Click vào dots
4. **Kiểm tra:**
   - [ ] Carousel hoạt động đúng
   - [ ] Không có lỗi trong console

#### Test 6: Navbar
1. Click vào các menu items trong navbar
2. Scroll trang để test active state
3. **Kiểm tra:**
   - [ ] Menu hoạt động đúng
   - [ ] Active state được cập nhật khi scroll
   - [ ] Không có lỗi trong console

### Bước 5: Kiểm tra Console

**Kết quả mong đợi:**
- ✅ Không có lỗi "Cannot read properties of null"
- ✅ Không có lỗi "Cannot read properties of undefined"
- ✅ Có thể có warnings nhưng không phải lỗi nghiêm trọng
- ✅ Các log messages từ code (ví dụ: `[Lineage] Initializing...`)

**Nếu có lỗi:**
- Ghi lại message lỗi
- Ghi lại dòng code gây lỗi (nếu có)
- Kiểm tra xem element có tồn tại trong DOM không

## 📋 Checklist Test

- [ ] Server khởi động thành công
- [ ] Trang web load không có lỗi
- [ ] Console không có lỗi null/undefined
- [ ] Lineage search hoạt động
- [ ] Tree search hoạt động
- [ ] Tree view hiển thị đúng
- [ ] Panel chi tiết hiển thị đúng
- [ ] Generation filter hoạt động
- [ ] Mini carousel hoạt động (nếu có)
- [ ] Navbar hoạt động đúng

## 🔍 Debug nếu có lỗi

### Lỗi "Cannot read properties of null"

1. **Kiểm tra element có tồn tại:**
   ```javascript
   // Trong console
   document.getElementById('elementId')
   ```

2. **Kiểm tra script có chạy sau DOM ready:**
   - Xem code có trong `DOMContentLoaded` không
   - Xem script có ở cuối body không

3. **Kiểm tra null check:**
   - Xem code có null check trước khi sử dụng không

### Lỗi khác

1. Xem message lỗi chi tiết trong console
2. Click vào dòng code trong console để xem stack trace
3. Kiểm tra Network tab nếu là lỗi API

## ✅ Kết quả mong đợi

Sau khi test, bạn sẽ thấy:
- ✅ Không còn lỗi "Cannot read properties of null"
- ✅ Tất cả tính năng hoạt động bình thường
- ✅ Console chỉ có log messages, không có errors

---

**Chúc bạn test thành công! 🎉**

