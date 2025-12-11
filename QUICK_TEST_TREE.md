# Quick Test API /api/tree

## Vấn Đề

Script `test_tree_api.py` báo lỗi `ModuleNotFoundError: No module named 'requests'`

## Giải Pháp

Đã sửa script để dùng `urllib` (built-in module) thay vì `requests`.

## Cách Test

### Cách 1: Chạy Script Test (Không Cần requests)

```bash
python test_tree_api.py
```

**Lưu ý:** Server phải đãy trước:
```bash
python start_server.py
```

### Cách 2: Test Trong Browser

Mở browser và truy cập:
```
http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3
```

Hoặc với `max_generation`:
```
http://localhost:5000/api/tree?root_id=P-1-1&max_generation=3
```

### Cách 3: Dùng curl (Nếu có)

```bash
curl "http://localhost:5000/api/tree?root_id=P-1-1&max_gen=3"
```

## Kiểm Tra Server

Trước khi test, đảm bảo server đang chạy:

```bash
# Khởi động server
python start_server.py

# Hoặc
python app.py
```

Sau đó mở browser: `http://localhost:5000`

## Expected Results

- ✅ Status 200
- ✅ JSON response với tree structure
- ✅ Có field `person_id`, `full_name`, `children`, etc.

## Troubleshooting

### Lỗi: Connection refused
→ Server chưa chạy, cần chạy `python start_server.py` trước

### Lỗi: 404 Not Found
→ Kiểm tra route `/api/tree` có được register không
→ Kiểm tra server logs

### Lỗi: 500 Internal Server Error
→ Kiểm tra database connection
→ Kiểm tra `genealogy_tree.py` có import được không
→ Xem server logs để biết lỗi cụ thể

