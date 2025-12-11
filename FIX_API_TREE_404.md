# Fix API /api/tree 404 Error

## ✅ Đã Sửa

1. **Route đã được register đúng**: Route `/api/tree` đã tồn tại và hoạt động
2. **Đã cải thiện error handling**: Sử dụng functions đã import ở đầu file thay vì import lại trong route handler
3. **Đã test thành công**: API trả về status 200 với dữ liệu hợp lệ

## 🔍 Nguyên Nhân Có Thể

Lỗi 404 có thể do:
1. **Server chưa được restart** sau khi sửa code
2. **Frontend đang cache** route cũ
3. **URL không đúng** (thiếu `/api/` prefix)

## 🚀 Cách Khắc Phục

### Bước 1: Restart Server

**Dừng server hiện tại** (nếu đang chạy):
- Nhấn `Ctrl+C` trong terminal đang chạy server

**Khởi động lại server**:
```bash
python start_server.py
```

Hoặc:
```bash
python app.py
```

### Bước 2: Kiểm Tra Server Đang Chạy

Mở browser và truy cập:
```
http://localhost:5000/api/health
```

Nếu thấy JSON với `status: "ok"` thì server đang hoạt động.

### Bước 3: Test API Tree

**Cách 1: Dùng Browser**
```
http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3
```

Hoặc với `max_generation`:
```
http://localhost:5000/api/tree?root_id=P-1-1&max_generation=3
```

**Cách 2: Dùng PowerShell**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3" | Select-Object -ExpandProperty Content
```

**Cách 3: Dùng Script Test**
```bash
python test_api_tree_direct.py
```

### Bước 4: Kiểm Tra Frontend

Nếu frontend vẫn báo 404:

1. **Kiểm tra URL trong frontend code**:
   - Đảm bảo URL là `/api/tree` (không phải `/tree`)
   - Đảm bảo có đầy đủ domain: `http://localhost:5000/api/tree`

2. **Clear browser cache**:
   - Nhấn `Ctrl+Shift+R` để hard refresh
   - Hoặc mở DevTools (F12) → Network tab → Disable cache

3. **Kiểm tra CORS** (nếu frontend chạy trên port khác):
   - Đảm bảo `flask-cors` đã được cài đặt
   - Kiểm tra `app.py` có `CORS(app)` không

## 📋 Expected Results

Khi API hoạt động đúng, bạn sẽ thấy:

**Status Code**: `200 OK`

**Response JSON**:
```json
{
  "person_id": "P-1-1",
  "full_name": "...",
  "alias": null,
  "children": [
    {
      "person_id": "P-2-1",
      "full_name": "...",
      "children": [...]
    }
  ],
  ...
}
```

## 🐛 Troubleshooting

### Lỗi: Connection refused
→ Server chưa chạy, cần chạy `python start_server.py` trước

### Lỗi: 404 Not Found
→ Kiểm tra:
- Server đã restart chưa?
- URL có đúng `/api/tree` không?
- Route có được register không? (chạy `python test_api_tree_direct.py` để kiểm tra)

### Lỗi: 500 Internal Server Error
→ Kiểm tra:
- Database connection
- Xem server logs để biết lỗi cụ thể
- Kiểm tra `genealogy_tree.py` có import được không

### Lỗi: Person not found
→ Kiểm tra:
- `root_id` có tồn tại trong database không?
- Chạy: `SELECT person_id FROM persons WHERE person_id = 'P-1-1'`

## ✅ Verification Checklist

- [ ] Server đã được restart
- [ ] `/api/health` trả về `status: "ok"`
- [ ] `/api/tree?root_id=P-1-1&max_gen=3` trả về status 200
- [ ] Response JSON có cấu trúc đúng (có `person_id`, `children`, etc.)
- [ ] Frontend có thể gọi API thành công

## 📝 Notes

- Route `/api/tree` hỗ trợ cả `max_gen` và `max_generation` parameters
- Default `root_id` là `P-1-1` (Vua Minh Mạng)
- Default `max_gen` là `5` nếu không chỉ định

