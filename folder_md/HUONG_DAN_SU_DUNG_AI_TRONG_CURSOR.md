# Hướng dẫn sử dụng AI trong Cursor

## 🚀 Các cách sử dụng AI trong Cursor

### 1. **Chat với AI (Cmd/Ctrl + L)**
- **Phím tắt**: `Cmd + L` (Mac) hoặc `Ctrl + L` (Windows/Linux)
- **Chức năng**: Mở chat panel để hỏi AI về code, yêu cầu giải thích, hoặc nhờ AI viết code
- **Cách dùng**:
  1. Nhấn `Cmd/Ctrl + L`
  2. Gõ câu hỏi hoặc yêu cầu
  3. AI sẽ trả lời và có thể đề xuất code

**Ví dụ**:
```
"Giải thích hàm get_person này làm gì"
"Viết function để validate email"
"Sửa lỗi trong file app.py dòng 100"
```

### 2. **Inline Editing (Cmd/Ctrl + K)**
- **Phím tắt**: `Cmd + K` (Mac) hoặc `Ctrl + K` (Windows/Linux)
- **Chức năng**: Chỉnh sửa code trực tiếp tại vị trí con trỏ
- **Cách dùng**:
  1. Đặt con trỏ tại dòng code cần sửa
  2. Nhấn `Cmd/Ctrl + K`
  3. Gõ yêu cầu (ví dụ: "Thêm error handling", "Refactor function này")
  4. AI sẽ sửa code ngay tại chỗ

**Ví dụ**:
- Chọn một function → `Cmd/Ctrl + K` → "Thêm try-catch cho function này"
- Chọn một đoạn code → `Cmd/Ctrl + K` → "Tối ưu đoạn code này"

### 3. **Composer (Cmd/Ctrl + I)**
- **Phím tắt**: `Cmd + I` (Mac) hoặc `Ctrl + I` (Windows/Linux)
- **Chức năng**: Tạo code mới hoặc chỉnh sửa nhiều file cùng lúc
- **Cách dùng**:
  1. Nhấn `Cmd/Ctrl + I`
  2. Mô tả những gì bạn muốn làm
  3. AI sẽ tạo/sửa code trong nhiều file nếu cần

**Ví dụ**:
```
"Tạo API endpoint mới /api/users với CRUD operations"
"Refactor toàn bộ error handling trong app.py"
```

### 4. **Tab (Tự động đề xuất)**
- **Chức năng**: AI tự động đề xuất code khi bạn gõ
- **Cách dùng**: Chỉ cần gõ code, AI sẽ tự động đề xuất
- **Chấp nhận**: Nhấn `Tab` để chấp nhận đề xuất

### 5. **Explain Code (Cmd/Ctrl + Shift + L)**
- **Phím tắt**: `Cmd/Ctrl + Shift + L`
- **Chức năng**: Giải thích code được chọn
- **Cách dùng**:
  1. Chọn đoạn code
  2. Nhấn `Cmd/Ctrl + Shift + L`
  3. AI sẽ giải thích code đó

## 📋 Các tính năng nâng cao

### 1. **Multi-file Editing**
- Sử dụng Composer (`Cmd/Ctrl + I`)
- Có thể yêu cầu AI sửa nhiều file cùng lúc
- Ví dụ: "Thêm logging vào tất cả API endpoints"

### 2. **Code Review**
- Chọn code → `Cmd/Ctrl + L` → "Review code này"
- AI sẽ phân tích và đề xuất cải thiện

### 3. **Debug Help**
- Chọn code có lỗi → `Cmd/Ctrl + L` → "Fix lỗi này"
- AI sẽ phân tích và sửa lỗi

### 4. **Generate Tests**
- Chọn function → `Cmd/Ctrl + K` → "Tạo unit test cho function này"
- AI sẽ tạo test cases

## 🎯 Tips sử dụng hiệu quả

### 1. **Mô tả rõ ràng**
❌ Không tốt: "Sửa lỗi"
✅ Tốt: "Sửa lỗi 500 trong /api/person endpoint, thêm error handling cho database queries"

### 2. **Cung cấp context**
- Mở file liên quan trước khi hỏi
- AI sẽ hiểu context tốt hơn

### 3. **Sử dụng @ để reference**
- `@filename` - Reference một file cụ thể
- `@function_name` - Reference một function
- Ví dụ: "Sửa function @get_person để thêm error handling"

### 4. **Iterative refinement**
- Bắt đầu với yêu cầu đơn giản
- Sau đó yêu cầu chi tiết hơn dựa trên kết quả

## 🔧 Troubleshooting

### AI không phản hồi?
1. Kiểm tra kết nối internet
2. Kiểm tra API key trong Settings
3. Thử restart Cursor

### Code không đúng như mong muốn?
1. Cung cấp thêm context
2. Yêu cầu cụ thể hơn
3. Sử dụng "Undo" và thử lại

### Muốn AI hiểu codebase tốt hơn?
1. Mở các file liên quan
2. Sử dụng @ để reference files
3. Cung cấp thông tin về structure của project

## 📚 Ví dụ thực tế

### Ví dụ 1: Sửa lỗi
```
1. Mở file app.py
2. Tìm dòng có lỗi
3. Chọn đoạn code → Cmd/Ctrl + K
4. Gõ: "Sửa lỗi này, thêm try-catch và logging"
```

### Ví dụ 2: Tạo function mới
```
1. Đặt con trỏ tại vị trí muốn thêm function
2. Cmd/Ctrl + K
3. Gõ: "Tạo function validate_email(email) để kiểm tra format email"
```

### Ví dụ 3: Refactor code
```
1. Chọn function cần refactor
2. Cmd/Ctrl + L
3. Gõ: "Refactor function này để dễ đọc hơn, tách thành các helper functions nhỏ"
```

### Ví dụ 4: Debug
```
1. Chọn code có lỗi
2. Cmd/Ctrl + L
3. Gõ: "Debug lỗi này, tại sao API trả về 500 error?"
```

## 🎓 Best Practices

1. **Luôn review code AI tạo ra** - Đảm bảo code đúng và an toàn
2. **Test sau khi AI sửa code** - Chạy test để đảm bảo không có lỗi mới
3. **Sử dụng version control** - Commit thường xuyên để có thể rollback
4. **Học từ code AI tạo** - Hiểu cách AI giải quyết vấn đề để học hỏi

## 💡 Lưu ý

- AI trong Cursor là **Auto** (tên của model)
- AI có thể đọc và hiểu toàn bộ codebase
- AI có thể sử dụng tools để đọc file, tìm kiếm code, chạy commands
- AI luôn cố gắng hiểu context và đưa ra giải pháp phù hợp

## 🆘 Cần giúp đỡ?

Nếu gặp vấn đề:
1. Kiểm tra Settings → AI để đảm bảo đã cấu hình đúng
2. Xem logs trong Cursor (Help → Show Logs)
3. Thử restart Cursor
4. Kiểm tra documentation của Cursor

---

**Chúc bạn code vui vẻ với AI! 🚀**

