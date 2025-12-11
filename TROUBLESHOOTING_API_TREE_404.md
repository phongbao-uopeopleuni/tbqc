# 🔧 Troubleshooting: API /api/tree Trả Mã 404

## ✅ Kết Quả Test

Tất cả các test đều **PASS**:
- ✅ Route `/api/tree` đã được register đúng
- ✅ API trả về status 200 với tất cả các parameters
- ✅ Database connection hoạt động tốt

## 🔍 Nguyên Nhân Có Thể

Nếu bạn vẫn thấy lỗi 404, có thể do:

1. **Server chưa được restart** sau khi sửa code
2. **Frontend đang cache** route cũ
3. **URL trong frontend không đúng**
4. **Server đang chạy trên port khác**

## 🚀 Giải Pháp

### Bước 1: Restart Server (QUAN TRỌNG NHẤT)

**Dừng server hiện tại:**
- Nhấn `Ctrl+C` trong terminal đang chạy server
- Hoặc đóng terminal và mở lại

**Khởi động lại server:**
```bash
python start_server.py
```

Hoặc:
```bash
python app.py
```

**Đảm bảo server đã khởi động:**
- Bạn sẽ thấy message: `Running on http://127.0.0.1:5000`
- Hoặc: `Running on http://0.0.0.0:5000`

### Bước 2: Kiểm Tra Server Đang Chạy

Mở browser và truy cập:
```
http://localhost:5000/api/health
```

**Expected:** JSON response với `status: "ok"`

Nếu không thấy, server chưa chạy → Quay lại Bước 1

### Bước 3: Test API Tree Trực Tiếp

**Cách 1: Dùng Browser**
```
http://localhost:5000/api/tree?max_generation=5
```

**Cách 2: Dùng PowerShell**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/tree?max_generation=5" | Select-Object -ExpandProperty Content
```

**Cách 3: Dùng Script Test**
```bash
python test_tree_api_comprehensive.py
```

**Expected:** Status 200 với JSON data

### Bước 4: Clear Browser Cache

Nếu frontend vẫn báo 404:

1. **Hard Refresh:**
   - Windows: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Clear Cache:**
   - Mở DevTools (F12)
   - Right-click vào nút Refresh
   - Chọn "Empty Cache and Hard Reload"

3. **Disable Cache trong DevTools:**
   - Mở DevTools (F12)
   - Vào tab Network
   - Check "Disable cache"

### Bước 5: Kiểm Tra URL Trong Frontend

Đảm bảo frontend đang gọi đúng URL:

**Đúng:**
```javascript
fetch('/api/tree?max_generation=5')
// Hoặc
fetch('http://localhost:5000/api/tree?max_generation=5')
```

**Sai:**
```javascript
fetch('/tree?max_generation=5')  // Thiếu /api/
fetch('/api/tree?max_gen=5')      // OK nhưng frontend có thể dùng max_generation
```

### Bước 6: Kiểm Tra CORS (Nếu Frontend Chạy Trên Port Khác)

Nếu frontend chạy trên port khác (ví dụ: 3000), cần kiểm tra CORS:

1. Kiểm tra `app.py` có `CORS(app)` không
2. Kiểm tra `flask-cors` đã được cài đặt:
   ```bash
   pip install flask-cors
   ```

## 📋 Checklist

- [ ] Server đã được restart (dừng và khởi động lại)
- [ ] `/api/health` trả về status 200
- [ ] `/api/tree?max_generation=5` trả về status 200 trong browser
- [ ] Browser cache đã được clear
- [ ] Frontend đang gọi đúng URL `/api/tree`
- [ ] CORS đã được cấu hình (nếu cần)

## 🧪 Test Script

Chạy script test để verify:

```bash
python test_tree_api_comprehensive.py
```

**Expected Output:**
```
[OK] Found 4 route(s) with 'tree'
[OK] Response received
Status Code: 200
```

## 🆘 Nếu Vẫn Còn Lỗi

### Lỗi: Connection refused
→ Server chưa chạy, cần chạy `python start_server.py`

### Lỗi: 404 Not Found
→ Kiểm tra:
1. Server đã restart chưa?
2. Route có được register không? (chạy test script)
3. URL có đúng `/api/tree` không?

### Lỗi: 500 Internal Server Error
→ Kiểm tra:
1. Database connection
2. Xem server logs để biết lỗi cụ thể
3. Kiểm tra `genealogy_tree.py` có import được không

### Lỗi: Person not found
→ Kiểm tra:
1. `root_id` có tồn tại trong database không?
2. Chạy: `SELECT person_id FROM persons WHERE person_id = 'P-1-1'`

## 📝 Notes

- Route `/api/tree` hỗ trợ cả `max_gen` và `max_generation` parameters
- Default `root_id` là `P-1-1` (Vua Minh Mạng)
- Default `max_gen` là `5` nếu không chỉ định
- Server phải được restart sau mỗi lần sửa code

## ✅ Verification

Sau khi làm theo các bước trên, bạn sẽ thấy:

**Browser:**
```
http://localhost:5000/api/tree?max_generation=5
```

**Response:**
```json
{
  "person_id": "P-1-1",
  "full_name": "Vua Minh Mạng",
  "children": [...]
}
```

**Status:** `200 OK`

---

**Nếu vẫn gặp vấn đề, hãy:**
1. Chạy `python test_tree_api_comprehensive.py` và gửi kết quả
2. Kiểm tra server logs
3. Kiểm tra browser console (F12) để xem lỗi cụ thể

